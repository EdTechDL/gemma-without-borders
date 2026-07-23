"""
tutor.py  —  turns ONE wrong answer into a study-guide card.

Splits cleanly into two kinds of content:
  * FACTS we already have (no AI needed): the misconception name, the correct
    answer, and the worked solution from our verified bank.
  * GENERATED content (Gemma's job): a friendly personalized explanation and a
    fresh follow-up practice question. These go through ask_gemma().

The `strategy` argument is how the AGENT adapts: if a plain explanation doesn't
land, it re-calls with a different strategy (see agent.py / the blueprint).
"""
from __future__ import annotations
from gemma_client import ask_gemma

STRATEGIES = ["explanation", "worked_example", "visual", "analogy"]


def diagnose(item: dict, chosen_label: str) -> dict | None:
    """Which misconception does this wrong choice reveal? Pure lookup from the
    ground-truth tags — 100% reliable, no model call."""
    for opt in item["options"]:
        if opt["label"] == chosen_label and not opt["is_correct"]:
            return {"id": opt.get("misconception_id"), "name": opt.get("misconception_name")}
    return None


def pick_practice(item: dict, misc: dict, questions: list, used_ids: set) -> dict:
    """The 'Now you try' question, as a full interactive item. Bank-first
    (verified answer key + worked solution), generation last: a small model can
    produce a garbled or wrong question, a bank item cannot."""
    for q in questions or []:
        if q["id"] in used_ids:
            continue
        if any(o.get("misconception_id") == misc.get("id") for o in q["options"]):
            used_ids.add(q["id"])
            return {"source": "bank", **q}
    for q in questions or []:
        if q["id"] not in used_ids and q["strand"] == item["strand"]:
            used_ids.add(q["id"])
            return {"source": "bank", **q}
    text = ask_gemma(
        f"TASK: practice\n"
        f"MISCONCEPTION: {misc['name']}\n"
        f"Write ONE fresh Grade 9 practice question, in English, that tests the "
        f"same skill as: {item['question']}\n"
        f"Use different numbers. Output ONLY the question itself - no answer, "
        f"no solution, no extra commentary."
    )
    return {"source": "generated", "id": f"GEN-{item['id']}", "question": text}


def hint(practice: dict, misc: dict, level: int) -> str:
    """A progressive hint for a practice item, grounded in its verified
    solution. Level 1 = a nudge; level 2 = the first concrete step."""
    depth = ("a gentle nudge at the right first thing to think about - do NOT "
             "reveal any step of the solution" if level <= 1 else
             "the first concrete step of the solution, but not the final answer")
    grounding = (f"The verified solution is: {practice.get('solution', '')}\n"
                 if practice.get("solution") else "")
    return ask_gemma(
        f"TASK: explain\n"
        f"MISCONCEPTION: {misc['name']}\n"
        f"A Grade 9 student is attempting: {practice['question']}\n"
        f"{grounding}"
        f"Give ONE hint - {depth}. One or two sentences, encouraging, and any "
        f"numbers must come from the verified solution above."
    )


def study_guide(item: dict, chosen_label: str, strategy: str = "explanation",
                questions: list = None, used_ids: set = None) -> dict:
    """Build the full study-guide card for one missed question."""
    misc = diagnose(item, chosen_label) or {"id": None, "name": "an unclear error"}
    correct = next(o for o in item["options"] if o["is_correct"])
    used_ids = used_ids if used_ids is not None else set()

    # Grounding rule: Gemma never recomputes the math. It receives the verified
    # answer and worked solution and explains WHY the student's method fails —
    # we caught the small model inventing wrong arithmetic when asked to redo it.
    explain_prompt = (
        f"TASK: {'visual' if strategy == 'visual' else 'explain'}\n"
        f"MISCONCEPTION: {misc['name']}\n"
        f"The student was asked: {item['question']}\n"
        f"They chose '{_text(item, chosen_label)}'. The correct answer is "
        f"'{correct['text']}', and the verified solution is: {item.get('solution', '')}\n"
        f"In under 120 words, for a 14-year-old, explain WHY the student's method "
        f"('{misc['name']}') gives the wrong result and what the right way of "
        f"thinking is. Do NOT redo the calculation and do NOT state any new "
        f"numeric results — the verified solution above is the only math. "
        f"Plain, encouraging language."
    )

    return {
        "item_id": item["id"],
        "strand": item["strand"],
        "question": item["question"],
        "chosen": _text(item, chosen_label),
        "correct": correct["text"],
        "misconception": misc,
        "strategy": strategy,
        "explanation": ask_gemma(explain_prompt),      # Gemma (stub for now)
        "worked_solution": item.get("solution", ""),    # real, from the bank
        "practice": pick_practice(item, misc, questions, used_ids),
    }


def _text(item: dict, label: str) -> str:
    for o in item["options"]:
        if o["label"] == label:
            return o["text"]
    return "(no answer)"
