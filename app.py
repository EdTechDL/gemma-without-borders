"""
app.py  —  Gemma Without Borders (student-facing quiz + AI study guide).

Run it:   streamlit run app.py

Flow:  take a short quiz  ->  submit  ->  score + a personalized study guide the
AGENT builds from your wrong answers (explanation + fresh practice per mistake),
plus the agent's read on your #1 misconception and a teacher hand-off if needed.
"""
import json
from pathlib import Path
import streamlit as st

import agent

QUESTIONS = json.loads((Path(__file__).parent / "data" / "questions.json").read_text())
STRANDS = sorted({q["strand"] for q in QUESTIONS})

st.set_page_config(page_title="Gemma Without Borders", page_icon="📘", layout="centered")


def pick_quiz(strand: str, n: int) -> list:
    pool = QUESTIONS if strand == "Mixed" else [q for q in QUESTIONS if q["strand"] == strand]
    return pool[:n]


def reset():
    for k in ("stage", "quiz", "answers"):
        st.session_state.pop(k, None)


# ---------------- INTRO ----------------
def intro():
    st.title("📘 Gemma Without Borders")
    st.caption("An autonomous study agent for the Grade 9 EQAO math assessment.")
    st.write(
        "Take a short quiz. When you submit, the agent finds **why** you missed what you "
        "missed, teaches each gap, and gives you a fresh question to prove you've got it."
    )
    col1, col2 = st.columns(2)
    strand = col1.selectbox("Topic", ["Mixed"] + STRANDS)
    n = col2.slider("Questions", 3, 8, 5)
    if st.button("Start quiz", type="primary"):
        st.session_state.stage = "quiz"
        st.session_state.quiz = pick_quiz(strand, n)
        st.session_state.answers = {}
        st.rerun()


# ---------------- QUIZ ----------------
def quiz():
    st.title("📝 Quiz")
    st.caption("Answer everything, then submit. No interruptions.")
    for i, q in enumerate(st.session_state.quiz, 1):
        st.markdown(f"**{i}. {q['question']}**")
        labels = [o["label"] for o in q["options"]]
        choice = st.radio(
            f"q_{q['id']}",
            labels,
            format_func=lambda l, q=q: f"{l})  " + next(o['text'] for o in q['options'] if o['label'] == l),
            index=None,
            key=f"radio_{q['id']}",
            label_visibility="collapsed",
        )
        st.session_state.answers[q["id"]] = choice
        st.divider()

    answered = sum(1 for q in st.session_state.quiz if st.session_state.answers.get(q["id"]))
    st.progress(answered / len(st.session_state.quiz), text=f"{answered}/{len(st.session_state.quiz)} answered")
    if st.button("Submit", type="primary", disabled=answered < len(st.session_state.quiz)):
        st.session_state.stage = "results"
        st.rerun()


# ---------------- RESULTS ----------------
def results():
    result = agent.grade_quiz(st.session_state.quiz, st.session_state.answers)
    analysis = agent.analyze(result)

    st.title("✅ Your results")
    st.metric("Score", f"{result['correct']} / {result['total']}", f"{result['score_pct']}%")

    if not result["wrong"]:
        st.success("Perfect score — no misconceptions to clear. 🎉")
        st.button("Take another quiz", on_click=reset)
        return

    # --- the agent's decision: what matters most ---
    if analysis["priority"]:
        st.info(
            f"🧠 **The agent's read:** your main gap is **{analysis['priority']['name']}** "
            f"(missed {analysis['priority']['count']}×). We'll start there."
        )
    if analysis["escalate"]:
        st.warning(
            "⚠️ You missed quite a few — the agent would **loop in your teacher** here with a summary."
        )
        with st.expander("Preview the teacher hand-off report"):
            st.code(agent.teacher_report(result, analysis))

    # --- a study-guide card per missed question ---
    st.subheader("📚 Your personalized study guide")
    for guide in agent.build_study_guides(result):
        with st.container(border=True):
            st.markdown(f"**{guide['question']}**")
            st.markdown(f"You picked **{guide['chosen']}** · correct is **{guide['correct']}**")
            if guide["misconception"].get("name"):
                st.caption(f"Misconception: {guide['misconception']['name']}")
            st.markdown("**Why:** " + guide["explanation"])
            if guide["worked_solution"]:
                with st.expander("See the worked solution"):
                    st.markdown(guide["worked_solution"])
            st.markdown("**Now you try:** " + guide["practice"])

    st.button("Take another quiz", on_click=reset)


# ---------------- ROUTER ----------------
stage = st.session_state.get("stage", "intro")
{"intro": intro, "quiz": quiz, "results": results}[stage]()
