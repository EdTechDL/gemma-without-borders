"""
app.py  —  Gemma Without Borders (student-facing quiz + AI study guide).

Run it:   streamlit run app.py

Flow:  take a short quiz  ->  submit  ->  score + a personalized study guide the
AGENT builds from your wrong answers (explanation + fresh practice per mistake),
plus the agent's read on your #1 misconception and a teacher hand-off if needed.
"""
import json
import re
from pathlib import Path
import streamlit as st

import agent
import mastery as m
import tutor
from gemma_client import vision_available, transcribe_image, plainify

QUESTIONS = json.loads((Path(__file__).parent / "data" / "questions.json").read_text())
STRANDS = sorted({q["strand"] for q in QUESTIONS})

st.set_page_config(page_title="Gemma Without Borders", layout="centered")

# ---- global styling: warm neutrals, serif display, one clay accent ----
st.markdown("""
<style>
:root {
    --ink: #1F1E1B;
    --muted: #6E6B63;
    --line: #E4E1D7;
    --card: #FFFFFF;
    --accent: #C96442;
}
h1, h2, h3 {
    font-family: Georgia, 'Times New Roman', serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
    color: var(--ink) !important;
}
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
.stButton button {
    border-radius: 6px;
    border: 1px solid var(--line);
    box-shadow: none;
}
.stButton button[kind="primary"] {
    background: var(--accent);
    border: 1px solid var(--accent);
    color: #FFFFFF;
}
.stButton button[kind="primary"]:hover { background: #B25638; border-color: #B25638; }
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card);
    border: 1px solid var(--line) !important;
    border-radius: 8px;
}
[data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 6px;
    background: var(--card);
}
[data-testid="stMetricValue"] {
    font-family: Georgia, 'Times New Roman', serif;
    color: var(--ink);
}
hr { border-color: var(--line) !important; }
.gwb-note {
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    background: var(--card);
    padding: 0.85rem 1.1rem;
    margin: 0.4rem 0 0.9rem 0;
    color: var(--ink);
}
.gwb-note .label {
    display: block;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.25rem;
}
.gwb-kicker {
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.2rem;
}
</style>
""", unsafe_allow_html=True)


def _inline_md(s: str) -> str:
    """Render **bold** / *italic* as HTML inside our note boxes (raw HTML doesn't
    process markdown). The italic rule ignores '2 * 3' (asterisks hugging text
    only), so multiplication is never mistaken for emphasis."""
    s = re.sub(r"\*\*(\S(?:.*?\S)?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", s)
    return s


def note(label: str, body: str):
    st.markdown(
        f'<div class="gwb-note"><span class="label">{label}</span>{_inline_md(body)}</div>',
        unsafe_allow_html=True,
    )


_FRAC = re.compile(r"(?<![\w.$])(\d+)\s*/\s*(\d+)(?![\w.])")


def esc(text) -> str:
    """Prepare text for display: (1) escape currency '$' so $3.60 shows literally
    instead of the run between two '$' rendering as LaTeX; (2) turn plain integer
    fractions like 3/7 into proper stacked fractions via KaTeX. Decimals and
    money (3.60 / 1.5, $3.60) are left alone by the fraction rule."""
    t = str(text).replace("$", "\\$")                 # currency first
    t = _FRAC.sub(r"$\\frac{\1}{\2}$", t)             # 3/7 -> stacked fraction
    return t


def pick_quiz(strand: str, n: int) -> list:
    pool = QUESTIONS if strand == "Mixed" else [q for q in QUESTIONS if q["strand"] == strand]
    return pool[:n]


def reset():
    for k in ("stage", "quiz", "answers", "guides", "mastered", "teacher_report",
              "escal_report", "msession", "mprobe", "mlesson", "mfeedback", "mtranscript"):
        st.session_state.pop(k, None)


def start_mastery(result, analysis):
    """Enter the autonomous practice loop, targeting the priority misconception."""
    pid = analysis["priority"]["id"]
    seed = next(w for w in result["wrong"]
                if w["misconception"] and w["misconception"].get("id") == pid)
    s = m.MasterySession(
        misconception_id=pid,
        misconception_name=analysis["priority"]["name"],
        strand=seed["item"]["strand"],
        seed_question=seed["item"]["question"],
        seed_solution=seed["item"].get("solution", ""),
        used_item_ids=[q["id"] for q in st.session_state.quiz],
    )
    st.session_state.msession = s
    with st.spinner("The agent is preparing your first lesson..."):
        st.session_state.mlesson = m.teach(s)
        st.session_state.mprobe = m.next_probe(s, QUESTIONS)
    st.session_state.mfeedback = None
    st.session_state.stage = "mastery"


# ---------------- INTRO ----------------
def intro():
    st.markdown('<div class="gwb-kicker">Grade 9 EQAO Mathematics</div>', unsafe_allow_html=True)
    st.title("Gemma Without Borders")
    st.caption("An autonomous study agent, running privately on device.")
    st.write(
        "Take a short quiz. When you submit, the agent identifies why you missed "
        "what you missed, teaches each gap, and gives you a fresh question to "
        "confirm you understand."
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
    st.title("Quiz")
    st.caption("Answer every question, then submit.")
    for i, q in enumerate(st.session_state.quiz, 1):
        st.markdown(f"**{i}. {esc(q['question'])}**")
        labels = [o["label"] for o in q["options"]]
        choice = st.radio(
            f"q_{q['id']}",
            labels,
            format_func=lambda l, q=q: f"{l})  " + esc(next(o['text'] for o in q['options'] if o['label'] == l)),
            index=None,
            key=f"radio_{q['id']}",
            label_visibility="collapsed",
        )
        st.session_state.answers[q["id"]] = choice
        st.divider()

    answered = sum(1 for q in st.session_state.quiz if st.session_state.answers.get(q["id"]))
    st.progress(answered / len(st.session_state.quiz), text=f"{answered} of {len(st.session_state.quiz)} answered")
    if st.button("Submit", type="primary", disabled=answered < len(st.session_state.quiz)):
        st.session_state.stage = "results"
        st.rerun()


# ---------------- RESULTS ----------------
def results():
    result = agent.grade_quiz(st.session_state.quiz, st.session_state.answers)
    analysis = agent.analyze(result)

    st.title("Results")
    st.metric("Score", f"{result['correct']} / {result['total']}", f"{result['score_pct']}%")

    if not result["wrong"]:
        st.write("A perfect score — no misconceptions to address.")
        st.button("Take another quiz", key="again_perfect", on_click=reset)
        return

    # --- the agent's decision: what matters most ---
    priority = analysis["priority"]
    mastered = st.session_state.get("mastered", set())
    if priority and priority["id"] in mastered:
        note(
            "Mastered",
            f"You've closed your main gap — <strong>{priority['name']}</strong>. "
            "Well done.",
        )
        st.write("Not feeling fully confident yet? Take another quiz to prove it sticks.")
        st.button("Take another quiz", type="primary", key="again_top", on_click=reset)
    elif priority:
        n = priority["count"]
        note(
            "Agent analysis",
            f"Your main gap is <strong>{priority['name']}</strong> "
            f"(missed {n} time{'s' if n != 1 else ''}). The study guide starts there.",
        )
        st.button(
            "Practice until I've mastered it",
            type="primary",
            on_click=start_mastery, args=(result, analysis),
            help="The agent keeps teaching and checking, switching approaches "
                 "when one doesn't land, until you get two in a row right.",
        )
    # only nudge the teacher when the main gap is still open
    if analysis["escalate"] and not (priority and priority["id"] in mastered):
        note(
            "Teacher hand-off",
            "Several questions were missed. The agent writes the teacher a report they "
            "can act on — not just a score.",
        )
        with st.expander("See the teacher report", expanded=True):
            if "teacher_report" not in st.session_state:
                with st.spinner("Writing a report the teacher can act on..."):
                    st.session_state.teacher_report = agent.teacher_report(result, analysis)
            st.code(st.session_state.teacher_report)

    # --- a study-guide card per missed question ---
    st.subheader("Your study guide")
    if "guides" not in st.session_state:
        with st.spinner("The agent is studying your mistakes and writing your guide..."):
            st.session_state.guides = agent.build_study_guides(result, QUESTIONS)
    for i, guide in enumerate(st.session_state.guides):
        with st.container(border=True):
            st.markdown(f"**{esc(guide['question'])}**")
            st.markdown(f"You picked **{esc(guide['chosen'])}** — the correct answer is **{esc(guide['correct'])}**")
            if guide["misconception"].get("name"):
                st.caption(f"Misconception: {guide['misconception']['name']}")
            st.markdown("**Why:** " + guide["explanation"])
            if guide["worked_solution"]:
                with st.expander("See the worked solution"):
                    st.markdown(plainify(guide["worked_solution"]))

            # --- interactive "Now you try" ---
            p = guide["practice"]
            st.markdown("**Now you try:** " + esc(p["question"]))
            if p.get("options"):
                choice = st.radio(
                    f"practice_{i}",
                    [o["label"] for o in p["options"]],
                    format_func=lambda l, p=p: f"{l})  " + esc(next(
                        o["text"] for o in p["options"] if o["label"] == l)),
                    index=None, key=f"practice_{i}", label_visibility="collapsed",
                )
                if choice:
                    if choice == p["correct"]:
                        note("Correct", "That's exactly it.")
                    else:
                        o = next(o for o in p["options"] if o["label"] == choice)
                        trap = o.get("misconception_name")
                        note("Not quite",
                             f"That's the <strong>{trap}</strong> trap again — "
                             "open a hint, or peek at the solution." if trap else
                             "Open a hint, or peek at the solution.")
                # hint + solution are expanders: they open in place, no page jump
                if guide.get("hint"):
                    with st.expander("Stuck? Show a hint"):
                        st.markdown(guide["hint"])
                if p.get("solution"):
                    with st.expander("See this one worked out"):
                        st.markdown(plainify(p["solution"]))

    st.button("Take another quiz", key="again_bottom", on_click=reset)


# ---------------- MASTERY LOOP ----------------
def check_answer():
    s = st.session_state.msession
    probe = st.session_state.mprobe
    chosen = st.session_state.get("mastery_choice")
    if not chosen:
        return
    explanation = st.session_state.get("mastery_reason", "")
    photo = st.session_state.get(f"mastery_photo_{s.attempts}")
    st.session_state.mtranscript = None
    if photo is not None and vision_available():
        with st.spinner("Gemma is reading your written work (on-device)..."):
            transcript = transcribe_image(photo.getvalue())
        st.session_state.mtranscript = transcript
        explanation = (explanation + "\n" if explanation else "") + \
            f"My written work: {transcript}"
    with st.spinner("The agent is reading your answer..."):
        outcome = m.submit_answer(s, probe, chosen, explanation)
    st.session_state.mfeedback = outcome
    if outcome["state"] == m.IN_PROGRESS:
        with st.spinner("The agent is deciding what to try next..."):
            if outcome["strategy_changed"]:
                st.session_state.mlesson = m.teach(s)
            st.session_state.mprobe = m.next_probe(s, QUESTIONS)
    st.session_state.pop("mastery_choice", None)
    st.session_state.pop("mastery_reason", None)


def mastery_stage():
    s = st.session_state.msession
    st.markdown('<div class="gwb-kicker">Autonomous practice</div>', unsafe_allow_html=True)
    st.title("Mastering: " + s.misconception_name)

    # one quiet status line + an escape hatch while practising
    if s.state == m.IN_PROGRESS:
        st.caption(f"Attempt {s.attempts + 1} of {m.MAX_ATTEMPTS} · "
                   f"{s.strategy_name} · streak {s.consecutive_correct} of {m.MASTERY_BAR}")
        st.button("← Back to results", key="leave_practice",
                  on_click=lambda: st.session_state.update(stage="results"),
                  help="Leave practice — you can start it again from your results anytime.")

    # terminal screens
    if s.state == m.MASTERED:
        # remember it: the results page now shows this gap as closed
        st.session_state.setdefault("mastered", set()).add(s.misconception_id)
        note("Mastery demonstrated",
             "Two fresh questions in a row, answered correctly. The gap is closed.")
        st.code(m.mastery_recap(s))
        st.button("Back to my results", key="back_mastered",
                  on_click=lambda: st.session_state.update(stage="results"))
        st.button("Take another quiz", key="again_mastered", on_click=reset)
        return
    if s.state == m.ESCALATED:
        note("Teacher hand-off",
             "The agent tried every approach it has. Time for a human — here is a report "
             "the teacher can act on, informed by what already didn't work.")
        if "escal_report" not in st.session_state:
            with st.spinner("Writing a report the teacher can act on..."):
                st.session_state.escal_report = m.escalation_report(s)
        st.code(st.session_state.escal_report)
        st.button("Back to my results", key="back_escalated",
                  on_click=lambda: st.session_state.update(stage="results"))
        st.button("Take another quiz", key="again_escalated", on_click=reset)
        return

    # feedback from the previous answer
    fb = st.session_state.get("mfeedback")
    if st.session_state.get("mtranscript"):
        note("What Gemma read from your photo",
             st.session_state.mtranscript.replace("\n", "<br>"))
    if fb:
        if fb["correct"] and fb.get("label") == "SHALLOW":
            note("Right answer — but shaky reasoning",
                 "The agent read your explanation and isn't convinced yet, so this "
                 "one doesn't count toward mastery. Say how you'd solve the next "
                 "one and prove it.")
        elif fb["correct"] and fb.get("label") == "SAME_ERROR":
            note("Right answer — wrong path",
                 "Your explanation still shows the original misconception, so the "
                 "streak resets. Read the lesson once more before the next question.")
        elif fb["correct"]:
            note("Correct", "One more in a row and you've shown mastery.")
        elif fb["strategy_changed"]:
            why = f" {fb['strategy_why'].rstrip('.')}." if fb.get("strategy_why") else ""
            note("Not yet — switching approach",
                 f"The agent is trying a different way: "
                 f"<strong>{s.strategy_name}</strong>.{why}")

    # the lesson for the current strategy
    with st.container(border=True):
        st.caption(f"Lesson — {s.strategy_name}")
        st.markdown(st.session_state.mlesson)

    # the probe
    probe = st.session_state.mprobe
    if probe is None:
        s.state = m.ESCALATED
        s.escalation_reason = "no fresh check question available"
        st.rerun()
    st.markdown(f"**Check yourself: {esc(probe['question'])}**")
    st.radio(
        "mastery probe",
        [o["label"] for o in probe["options"]],
        format_func=lambda l: f"{l})  " + esc(next(o["text"] for o in probe["options"] if o["label"] == l)),
        index=None,
        key="mastery_choice",
        label_visibility="collapsed",
    )
    st.text_input(
        "In one line: how did you get your answer? (optional — the agent reads it)",
        key="mastery_reason",
        placeholder="e.g. I found a common denominator of 12, then added the tops",
    )
    if vision_available():
        st.file_uploader(
            "...or photograph your written work — Gemma reads it on this device",
            type=["png", "jpg", "jpeg"], key=f"mastery_photo_{s.attempts}",
        )
    st.button("Check my answer", type="primary", on_click=check_answer,
              disabled=st.session_state.get("mastery_choice") is None)


# ---------------- ROUTER ----------------
stage = st.session_state.get("stage", "intro")
{"intro": intro, "quiz": quiz, "results": results, "mastery": mastery_stage}[stage]()
