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


def study_guide(item: dict, chosen_label: str, strategy: str = "explanation") -> dict:
    """Build the full study-guide card for one missed question."""
    misc = diagnose(item, chosen_label) or {"id": None, "name": "an unclear error"}
    correct = next(o for o in item["options"] if o["is_correct"])

    explain_prompt = (
        f"TASK: {'visual' if strategy == 'visual' else 'explain'}\n"
        f"MISCONCEPTION: {misc['name']}\n"
        f"The student was asked: {item['question']}\n"
        f"They chose '{_text(item, chosen_label)}' but the answer is '{correct['text']}'.\n"
        f"Using a {strategy} approach, explain the mistake and the correct method for a "
        f"14-year-old. Use plain, encouraging language."
    )
    practice_prompt = (
        f"TASK: practice\n"
        f"MISCONCEPTION: {misc['name']}\n"
        f"Write ONE fresh Grade 9 practice question (with its answer) that targets the same "
        f"misconception as: {item['question']}"
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
        "practice": ask_gemma(practice_prompt),         # Gemma (stub for now)
    }


def _text(item: dict, label: str) -> str:
    for o in item["options"]:
        if o["label"] == label:
            return o["text"]
    return "(no answer)"
