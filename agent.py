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
            wrong.append({"item": q, "chosen": chosen, "trick": misc})
    return {
        "total": len(questions),
        "correct": correct_count,
        "score_pct": round(100 * correct_count / max(1, len(questions))),
        "wrong": wrong,
    }


def analyze(result: dict) -> dict:
    """The 'decide what to do' step: find the trick pattern across all
    wrong answers and pick the priority one to tackle first."""
    counts = Counter()
    for w in result["wrong"]:
        m = w["trick"]
        if m and m.get("id"):
            counts[(m["id"], m["name"])] += 1

    patterns = [{"id": k[0], "name": k[1], "count": c}
                for k, c in counts.most_common()]
    priority = patterns[0] if patterns else None

    wrong_ratio = len(result["wrong"]) / max(1, result["total"])
    escalate = wrong_ratio >= ESCALATE_WRONG_RATIO

    return {"patterns": patterns, "priority": priority, "escalate": escalate}


def build_study_guides(result: dict, questions: list = None, seen_ids=None) -> list:
    """One study-guide card per missed question (the student-facing output).

    'Now you try' comes from verified bank items the student has NOT already seen:
    seed with seen_ids (every quiz question) so a practice item is never one they
    just answered, and share the set so no two cards repeat a question."""
    used = set(seen_ids or ()) | {w["item"]["id"] for w in result["wrong"]}
    return [study_guide(w["item"], w["chosen"], questions=questions, used_ids=used)
            for w in result["wrong"]]


def teacher_report(result: dict, analysis: dict) -> str:
    """A report the PARENTS can act on. The FACTS (score, tricks) are
    deterministic; Gemma writes the interpretation and concrete interventions,
    grounded in those facts."""
    from gemma_client import ask_gemma, plainify, format_teacher_report

    patterns = "; ".join(f"{p['name']} (missed {p['count']})"
                         for p in analysis["patterns"]) or "none identified"
    focus = analysis["priority"]["name"] if analysis["priority"] else "n/a"

    narrative = plainify(ask_gemma(
        "TASK: parent\n"
        "You are writing a brief, warm report for the PARENTS of a Grade 9 student, "
        "using ONLY the facts below. Do not invent numbers or facts.\n"
        f"Diagnostic-quiz score: {result['correct']} of {result['total']}.\n"
        f"Tricks the student showed: {patterns}.\n"
        f"The trick that caught them most: {focus}.\n\n"
        "Write, in plain text (no LaTeX, no dollar signs), addressed to the parents "
        "in plain everyday language, no teaching jargon:\n"
        "First, TWO sentences explaining, in everyday words, the wrong idea their child keeps applying "
        "and what it reveals about how the student is thinking.\n"
        "Then a line exactly 'Try at home:' followed by THREE specific, kitchen-table-ready "
        "activities (each on its own line starting with '- ') that target THIS "
        "trick. Be concrete and doable at the kitchen table in 10 minutes - no teaching jargon.",
        max_new_tokens=380))

    header = (f"**Parent report** — scored {result['correct']} of {result['total']} "
              f"({result['score_pct']}%). The trick that caught them most: **{focus}**.")
    return format_teacher_report(header, narrative)
