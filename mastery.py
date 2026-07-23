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

from gemma_client import ask_gemma, plainify

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
    seed_solution: str = ""       # its VERIFIED worked solution (grounds every lesson)
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
    grounding = (f"The verified solution to that question is: {session.seed_solution}\n"
                 if session.seed_solution else "")
    lesson = ask_gemma(
        f"TASK: explain\n"
        f"MISCONCEPTION: {session.misconception_name}\n"
        f"You are tutoring a Grade 9 student who keeps making this mistake: "
        f"{session.misconception_name}. They originally missed this question: "
        f"{session.seed_question}\n"
        f"{grounding}"
        f"Teaching approach for THIS attempt — {name}: {recipe}\n"
        f"Keep it under 150 words, encouraging, plain language. Any numbers you "
        f"mention must come from the verified solution above — do NOT invent new "
        f"calculations or results. Do not give them a new question to answer; "
        f"just teach."
    )
    lesson = plainify(lesson)
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
            if data["correct"] in opts and len(opts) >= 3 and _self_check(session, data):
                probe = {
                    "source": "generated",
                    "id": f"GEN-{session.attempts + 1}",
                    "question": plainify(data["question"]),
                    "options": [{"label": k, "text": plainify(v), "is_correct": k == data["correct"]}
                                for k, v in sorted(opts.items())],
                    "correct": data["correct"],
                    "solution": "",
                }
                session.history.append({"kind": "probe", "source": "generated"})
                return probe
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return None


def _self_check(session: MasterySession, data: dict) -> bool:
    """Before a generated question is shown, Gemma must solve it BLIND (without
    seeing which option it marked correct) and agree with its own answer key.
    A question that fails its own audit is discarded — we caught the small
    model marking wrong keys, and this check turns that failure mode into a
    silent retry instead of a student-facing bug."""
    if session.gemma_calls >= MAX_GEMMA_CALLS:
        return False
    opts = "\n".join(f"{k}) {v}" for k, v in sorted(data["options"].items()))
    session.gemma_calls += 1
    verdict = ask_gemma(
        f"TASK: solve\n"
        f"Solve this and reply with ONLY the letter of the correct option.\n"
        f"{data['question']}\n{opts}"
    )
    m = re.search(r"\b([A-F])\b", verdict.upper())
    ok = bool(m) and m.group(1) == data["correct"]
    session.history.append({"kind": "self_check", "passed": ok})
    return ok


# ------------------------------------------------------------ EVALUATE + ADAPT
def _grade_reasoning(session: MasterySession, probe: dict, chosen_label: str,
                     explanation: str) -> str:
    """Gemma as a CONSTRAINED grader: classify the student's typed reasoning
    into a closed label set. It compares against the known answer — it never
    recomputes the math open-endedly. Fail-open: any parse problem returns
    RESOLVED so a model hiccup can never hurt the student."""
    correct_opt = next(o["text"] for o in probe["options"] if o["is_correct"])
    session.gemma_calls += 1
    raw = ask_gemma(
        f"TASK: grade\n"
        f"MISCONCEPTION: {session.misconception_name}\n"
        f"A Grade 9 student answered this question: {probe['question']}\n"
        f"The correct answer is: {correct_opt}. The student chose "
        f"'{chosen_label}' and explained their thinking: \"{explanation}\"\n"
        f"Classify ONLY the quality of their reasoning. Reply with exactly one "
        f"word from this list and nothing else:\n"
        f"RESOLVED  (their reasoning shows the concept is genuinely understood)\n"
        f"SHALLOW   (right answer but the reasoning is missing, circular, or lucky)\n"
        f"SAME_ERROR (their reasoning still shows the misconception: "
        f"{session.misconception_name})"
    )
    m = re.search(r"\b(RESOLVED|SHALLOW|SAME_ERROR)\b", raw.upper())
    label = m.group(1) if m else "RESOLVED"
    session.history.append({"kind": "reasoning_grade", "label": label,
                            "explanation": explanation})
    return label


def _choose_strategy(session: MasterySession, explanation: str) -> str:
    """Gemma DECIDES the next teaching move: given the student's own words, it
    picks the most promising remaining strategy and says why. Deterministic
    fallback (next rung of the ladder) if the reply doesn't parse."""
    remaining = STRATEGY_LADDER[session.strategy_index + 1:]
    fallback_reason = "moving to the next approach on the ladder"
    if not remaining:
        return fallback_reason
    if len(remaining) > 1 and explanation:
        names = ", ".join(name for name, _ in remaining)
        session.gemma_calls += 1
        raw = ask_gemma(
            f"TASK: choose\n"
            f"MISCONCEPTION: {session.misconception_name}\n"
            f"A student still has this misconception after a lesson. Their own "
            f"words about their thinking: \"{explanation}\"\n"
            f"Which teaching approach should be tried next? Reply with ONLY JSON: "
            f'{{"strategy": "<one of: {names}>", "why": "<one short sentence>"}}'
        )
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                for offset, (name, _) in enumerate(remaining):
                    if name.lower() in str(data.get("strategy", "")).lower():
                        session.strategy_index += 1 + offset
                        return plainify(data.get("why", fallback_reason))
            except json.JSONDecodeError:
                pass
    session.strategy_index += 1
    return fallback_reason


def submit_answer(session: MasterySession, probe: dict, chosen_label: str,
                  explanation: str = "") -> dict:
    """Grade the probe answer, judge the reasoning, decide what happens next.

    Multiple-choice correctness is deterministic (bank ground truth). Gemma
    grades the typed reasoning and chooses the next strategy; hard caps and
    final state transitions stay in plain code so the loop always terminates.

    Returns {"correct", "label", "state", "strategy_changed", "strategy_why"}."""
    correct = chosen_label == probe["correct"]
    session.attempts += 1
    session.history.append({"kind": "answer", "probe_id": probe.get("id"),
                            "chosen": chosen_label, "correct": correct})

    label = ""
    strategy_changed = False
    strategy_why = ""
    if correct:
        label = (_grade_reasoning(session, probe, chosen_label, explanation)
                 if explanation.strip() else "RESOLVED")
        if label == "SHALLOW":
            # right answer, shaky reasoning: mastery is not demonstrated,
            # but the streak isn't punished either
            pass
        elif label == "SAME_ERROR":
            session.consecutive_correct = 0
        else:
            session.consecutive_correct += 1
        if session.consecutive_correct >= MASTERY_BAR:
            session.state = MASTERED
    else:
        session.consecutive_correct = 0
        if session.strategy_index + 1 < len(STRATEGY_LADDER):
            strategy_why = _choose_strategy(session, explanation)
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

    return {"correct": correct, "label": label, "state": session.state,
            "strategy_changed": strategy_changed, "strategy_why": strategy_why}


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
    """A teacher-actionable hand-off. Facts are deterministic; Gemma interprets
    the session (what worked, where the student is stuck) and proposes concrete
    interventions informed by which tutoring approaches already failed."""
    tried = list(dict.fromkeys(h["strategy"] for h in session.history if h["kind"] == "lesson"))
    answers = [h for h in session.history if h["kind"] == "answer"]
    right = sum(1 for a in answers if a["correct"])
    reasoning = [h["label"] for h in session.history if h["kind"] == "reasoning_grade"]

    narrative = plainify(ask_gemma(
        "TASK: teacher\n"
        "Write a brief report for a Grade 9 math teacher about ONE student whom an AI "
        "tutor worked with but could not bring to mastery. Use ONLY these facts; do not "
        "invent numbers.\n"
        f"Misconception: {session.misconception_name}.\n"
        f"The tutor tried these teaching approaches, in order, and none fully worked: "
        f"{', '.join(tried) or 'none'}.\n"
        f"Across {len(answers)} follow-up questions the student got {right} correct.\n"
        f"Reasoning quality when correct: {', '.join(reasoning) or 'not assessed'}.\n"
        f"The tutor stopped because: {session.escalation_reason}.\n\n"
        "Write, in plain text (no LaTeX, no dollar signs), addressed to the teacher:\n"
        "First, TWO sentences: the underlying misunderstanding, and what the session "
        "showed about where the student improved and where they are still stuck.\n"
        "Then a line exactly 'Try in class:' followed by THREE specific interventions "
        "(each on its own line starting with '- ') targeting this misconception - and "
        "different from the tutoring approaches that already failed above.",
        max_new_tokens=400))

    return (
        "TEACHER REPORT - Gemma Without Borders\n"
        f"Stuck on: {session.misconception_name}.\n"
        f"Tutor tried: {', '.join(tried) or 'none'}. "
        f"Follow-up questions: {right}/{len(answers)} correct.\n\n"
        + narrative
    )
