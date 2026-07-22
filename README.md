# Gemma Without Borders

An **autonomous study agent** for the Grade 9 EQAO math assessment (Ontario MTH1W).

A student takes a short quiz. On submit, the agent looks across **all** their wrong
answers, decides which misconception matters most, and builds a personalized study
guide — for each mistake: what went wrong, the correct method, and a **fresh practice
question** to prove they've got it. If a student is struggling badly, it hands off to
a teacher with a summary.

> A chatbot responds. **An agent pursues a goal and decides what to do next.**
> Here the goal is: bring the student to mastery of their misconception with minimal
> teacher intervention.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens in your browser. No model or internet needed yet — Gemma's responses are
**placeholders** so the whole app runs today (see "Wiring in Gemma" below).

## How it's built

| File | Job |
|------|-----|
| `app.py` | The quiz UI (Streamlit): quiz → submit → score + study guide |
| `agent.py` | **The agent controller** — grades, finds the misconception pattern, decides the priority, escalates to a teacher |
| `tutor.py` | Turns one wrong answer into a study-guide card |
| `gemma_client.py` | **The one door to Gemma** — every AI call goes through `ask_gemma()` |
| `data/questions.json` | 36 verified EQAO-style questions, each wrong answer tagged with its misconception |

## Wiring in Gemma (later — one change)

The app is built so Gemma plugs into a single spot. In `gemma_client.py`, set
`USE_REAL_GEMMA = True` and fill in `_real_gemma()` — either **local via Ollama**
(the on-device / Edge story) or the **Kaggle/transformers** path from
`gemma-tutor-CLEAN.ipynb`. Nothing else in the app changes.

## Reliability by design

The parts that must be correct never rely on the model guessing: diagnosis is a
**table lookup** from the tagged answer key, and the correct solution comes straight
from the verified bank. Gemma is used only where it's strong — writing the explanation
and generating fresh practice.

---
*Built for the GDG Windsor · Build with AI — Gemma Hackathon. Edge / On-Device track.*
