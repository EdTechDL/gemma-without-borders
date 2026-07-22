"""
mastery.py  —  the autonomous mastery loop.

After the quiz diagnoses a misconception, this module keeps the agent working the
problem until the student demonstrates understanding or a safety cap trips:

    TEACH (Gemma, strategy-specific lesson)
      -> PROBE (a fresh question on the same misconception)
      -> EVALUATE (deterministic when the probe comes from the bank)
      -> ADAPT (plain code: mastery, next strategy, or teacher hand-off)

Design rules (from the project blueprint):
  * Adaptation = advancing through a FIXED strategy ladder — each retry is a
    genuinely different teaching approach, never an open-ended invention.
  * Evaluation prefers bank probes, where the answer key is ground truth.
  * Hard caps guarantee termination: the demo cannot loop forever.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field

from gemma_client import ask_gemma

# ---- the strategy ladder: each entry is a different way to teach ----
STRATEGY_LADDER = [
    ("Direct correction",
     "State the misconception plainly ('you might think..., but actually...'), "
     "explain the correct rule in 2-3 sentences, then show one fully worked example."),
    ("Visual walkthrough",
     "Teach it with a picture built from words: a number line, an area model, "
     "groups of objects, or a table — walk through the visual step by step. "
     "Avoid abstract rules; make the student SEE why it works."),
    ("Side-by-side contrast",
     "Show the WRONG method and the RIGHT method side by side on the same "
     "problem, line by line, and point at the exact step where they part ways."),
    ("Real-world analogy",
     "Anchor the idea in an everyday situation (money, pizza slices, game "
     "scores). Build the analogy first, then map it back to the math."),
]

MASTERY_BAR = 2      # consecutive correct answers to declare mastery
MAX_ATTEMPTS = 4     # probe cycles before we hand off to a human
MAX_GEMMA_CALLS = 12 # absolute budget, belt and suspenders

MASTERED, ESCALATED, IN_PROGRESS = "MASTERED", "ESCALATED", "IN_PROGRESS"


@dataclass
class MasterySession:
    misconception_id: str
    misconception_name: str
    strand: str
    seed_question: str            # the quiz question the student originally missed
    used_item_ids: list = field(default_factory=list)
    strategy_index: int = 0
    attempts: int = 0
    consecutive_correct: int = 0
    gemma_calls: int = 0
    state: str = IN_PROGRESS
    escalation_reason: str = ""
    history: list = field(default_factory=list)   # dicts: lesson / probe / answer rows

    @property
    def strategy_name(self) -> str:
        return STRATEGY_LADDER[min(self.strategy_index, len(STRATEGY_LADDER) - 1)][0]


# ------------------------------------------------------------------ TEACH
def teach(session: MasterySession) -> str:
    """One strategy-specific lesson from Gemma."""
    name, recipe = STRATEGY_LADDER[session.strategy_index]
    session.gemma_calls += 1
    lesson = ask_gemma(
        f"TASK: explain\n"
        f"MISCONCEPTION: {session.misconception_name}\n"
        f"You are tutoring a Grade 9 student who keeps making this mistake: "
        f"{session.misconception_name}. They originally missed this question: "
        f"{session.seed_question}\n"
        f"Teaching approach for THIS attempt — {name}: {recipe}\n"
        f"Keep it under 150 words, encouraging, plain language. Do not give them a "
        f"new question to answer; just teach."
    )
    session.history.append({"kind": "lesson", "strategy": name, "text": lesson})
    return lesson


# ------------------------------------------------------------------ PROBE
def next_probe(session: MasterySession, questions: list) -> dict | None:
    """A FRESH check question on the same misconception.

    Order of preference (most trustworthy first):
      1. an unused bank item tagged with the SAME misconception (ground-truth key)
      2. an unused bank item from the same STRAND (still ground-truth key)
      3. a Gemma-generated item (last resort: a small model can get its own
         answer key wrong, so the bank always wins while items remain)"""
    def take(q, why):
        session.used_item_ids.append(q["id"])
        session.history.append({"kind": "probe", "source": why, "id": q["id"]})
        return {"source": why, **q}

    for q in questions:
        if q["id"] in session.used_item_ids:
            continue
        if any(o.get("misconception_id") == session.misconception_id for o in q["options"]):
            return take(q, "bank")
    for q in questions:
        if q["id"] not in session.used_item_ids and q["strand"] == session.strand:
            return take(q, "bank-strand")
    return _generated_probe(session)


def _generated_probe(session: MasterySession) -> dict | None:
    """Gemma-generated multiple-choice probe, validated before use."""
    for _ in range(2):  # one retry on a bad parse
        if session.gemma_calls >= MAX_GEMMA_CALLS:
            return None
        session.gemma_calls += 1
        raw = ask_gemma(
            f"TASK: practice\n"
            f"MISCONCEPTION: {session.misconception_name}\n"
            f"Write ONE new Grade 9 multiple-choice question, in English, testing "
            f"the same skill as: {session.seed_question}\n"
            f"Use different numbers than the original. Exactly one option is correct.\n"
            f"Return ONLY JSON, no other text, exactly this shape:\n"
            f'{{"question": "...", "options": {{"A": "...", "B": "...", '
            f'"C": "...", "D": "..."}}, "correct": "A"}}'
        )
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            continue
        try:
            data = json.loads(m.group())
            opts = data["options"]
            if data["correct"] in opts and len(opts) >= 3:
                probe = {
                    "source": "generated",
                    "id": f"GEN-{session.attempts + 1}",
                    "question": data["question"],
                    "options": [{"label": k, "text": v, "is_correct": k == data["correct"]}
                                for k, v in sorted(opts.items())],
                    "correct": data["correct"],
                    "solution": "",
                }
                session.history.append({"kind": "probe", "source": "generated"})
                return probe
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return None


# ------------------------------------------------------------ EVALUATE + ADAPT
def submit_answer(session: MasterySession, probe: dict, chosen_label: str) -> dict:
    """Grade the probe answer, then decide what happens next (plain code only).

    Returns {"correct": bool, "state": ..., "strategy_changed": bool}."""
    correct = chosen_label == probe["correct"]
    session.attempts += 1
    session.history.append({"kind": "answer", "probe_id": probe.get("id"),
                            "chosen": chosen_label, "correct": correct})

    strategy_changed = False
    if correct:
        session.consecutive_correct += 1
        if session.consecutive_correct >= MASTERY_BAR:
            session.state = MASTERED
    else:
        session.consecutive_correct = 0
        if session.strategy_index + 1 < len(STRATEGY_LADDER):
            session.strategy_index += 1
            strategy_changed = True
        else:
            session.state = ESCALATED
            session.escalation_reason = "every teaching strategy has been tried"

    if session.state == IN_PROGRESS and session.attempts >= MAX_ATTEMPTS:
        session.state = ESCALATED
        session.escalation_reason = f"attempt cap reached ({MAX_ATTEMPTS} probes)"
    if session.state == IN_PROGRESS and session.gemma_calls >= MAX_GEMMA_CALLS:
        session.state = ESCALATED
        session.escalation_reason = "model call budget reached"

    return {"correct": correct, "state": session.state,
            "strategy_changed": strategy_changed}


# ------------------------------------------------------------------ REPORTS
def mastery_recap(session: MasterySession) -> str:
    tried = [h["strategy"] for h in session.history if h["kind"] == "lesson"]
    return (
        f"Mastery demonstrated: {session.misconception_name}.\n"
        f"Probes answered: {session.attempts} - final streak of "
        f"{session.consecutive_correct} correct.\n"
        f"Teaching approaches used: {', '.join(dict.fromkeys(tried))}."
    )


def escalation_report(session: MasterySession) -> str:
    tried = [h["strategy"] for h in session.history if h["kind"] == "lesson"]
    answers = [h for h in session.history if h["kind"] == "answer"]
    right = sum(1 for a in answers if a["correct"])
    return (
        "TEACHER HAND-OFF - Gemma Without Borders\n"
        f"Student is stuck on: {session.misconception_id}: {session.misconception_name}\n"
        f"Stopped because: {session.escalation_reason}\n"
        f"Probes: {right}/{len(answers)} correct across {session.attempts} attempts\n"
        f"Strategies tried: {', '.join(dict.fromkeys(tried)) or 'none'}\n"
        "Suggested action: a short 1:1 on this concept before further practice."
    )
