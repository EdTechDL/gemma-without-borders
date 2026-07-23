"""
agent.py  —  the AGENT CONTROLLER.

This is what makes the project an *agent* instead of a chatbot: after the quiz it
doesn't just react to each wrong answer, it looks across ALL of them, decides what
matters most, and drives toward a goal (student demonstrates understanding).

v1 implements the parts that don't need the model yet (analyze + prioritise +
escalation decision). The teach -> follow-up -> evaluate -> adapt loop is scaffolded
here and gets fleshed out once real Gemma is connected (see the Blueprint doc).
"""
from collections import Counter
from tutor import diagnose, study_guide

# escalate to a human once a student misses this fraction of the quiz badly
ESCALATE_WRONG_RATIO = 0.6


def grade_quiz(questions: list, answers: dict) -> dict:
    """answers = {item_id: chosen_label}. Returns score + the wrong ones diagnosed."""
    wrong = []
    correct_count = 0
    for q in questions:
        chosen = answers.get(q["id"])
        if chosen == q["correct"]:
            correct_count += 1
        elif chosen:  # answered, but wrong
            misc = diagnose(q, chosen)
            wrong.append({"item": q, "chosen": chosen, "misconception": misc})
    return {
        "total": len(questions),
        "correct": correct_count,
        "score_pct": round(100 * correct_count / max(1, len(questions))),
        "wrong": wrong,
    }


def analyze(result: dict) -> dict:
    """The 'decide what to do' step: find the misconception pattern across all
    wrong answers and pick the priority one to tackle first."""
    counts = Counter()
    for w in result["wrong"]:
        m = w["misconception"]
        if m and m.get("id"):
            counts[(m["id"], m["name"])] += 1

    patterns = [{"id": k[0], "name": k[1], "count": c}
                for k, c in counts.most_common()]
    priority = patterns[0] if patterns else None

    wrong_ratio = len(result["wrong"]) / max(1, result["total"])
    escalate = wrong_ratio >= ESCALATE_WRONG_RATIO

    return {"patterns": patterns, "priority": priority, "escalate": escalate}


def build_study_guides(result: dict, questions: list = None) -> list:
    """One study-guide card per missed question (the student-facing output).

    Passing the question bank lets each card's 'Now you try' come from verified
    items; already-used ids are shared so no card repeats another's question."""
    used = {w["item"]["id"] for w in result["wrong"]}
    return [study_guide(w["item"], w["chosen"], questions=questions, used_ids=used)
            for w in result["wrong"]]


def teacher_report(result: dict, analysis: dict) -> str:
    """Deterministic (no-model) handoff report — the escalation path."""
    lines = [
        "TEACHER SUMMARY — Gemma Without Borders",
        f"Score: {result['correct']}/{result['total']} ({result['score_pct']}%)",
        "",
        "Misconception patterns observed:",
    ]
    for p in analysis["patterns"]:
        lines.append(f"  - {p['id']}: {p['name']}  (missed {p['count']}x)")
    if analysis["priority"]:
        lines.append("")
        lines.append(f"Recommended focus: {analysis['priority']['name']}")
    lines.append("")
    lines.append("Suggested action: short 1:1 on the focus misconception before moving on.")
    return "\n".join(lines)
