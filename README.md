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

## See how it works, cell by cell

Open [docs/notebook-walkthrough.html](docs/notebook-walkthrough.html) in a browser — the
whole pipeline shown as annotated Jupyter-style cells, with a plain-words explanation of
every block. Good first stop for new teammates.

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

## Where Gemma does the thinking

Gemma is not a text box bolted onto a quiz — it sits at every decision point of the
agent loop, always through one auditable door (`gemma_client.py`), always constrained
so a model mistake cannot corrupt the loop:

| Call site | What Gemma does | Capability | Guardrail |
|---|---|---|---|
| `tutor.study_guide` | Personalized explanation of the student's specific error | Generation | Facts (correct answer, solution) come from the verified bank, not the model |
| `tutor.study_guide` | Fresh practice question per mistake | Generation | Clearly separated from graded content |
| `mastery.teach` | Strategy-specific lesson (4 distinct pedagogies) | Generation | Strategy recipe fixed by the ladder; model writes within it |
| `mastery._grade_reasoning` | Classifies the student's typed reasoning: RESOLVED / SHALLOW / SAME_ERROR | Reasoning, structured output | Closed label set; fail-open to RESOLVED; a right answer with shaky reasoning does not count toward mastery |
| `mastery._choose_strategy` | Picks the next teaching strategy from the remaining ladder, with a stated reason | Reasoning, decision-making, structured output | Choice restricted to the remaining menu; deterministic ladder fallback on any parse failure |
| `mastery._generated_probe` | Authors a new check question (JSON) when the bank is exhausted | Structured output | Must pass a blind self-solve audit before a student ever sees it |
| `tutor.hint` | Progressive hints on practice questions (nudge, then first step) | Generation | Grounded in the verified solution; may not invent numbers |
| `gemma_client.transcribe_image` | Reads a photo of the student's handwritten work, on-device | Multimodal (vision) | Transcribes only — correctness is always judged against the verified bank |

What Gemma is deliberately NOT allowed to do: grade multiple-choice answers
(ground-truth key), diagnose bank items (ground-truth tags), or decide loop
termination (hard caps in plain code). We caught the 1B model generating a
question with a wrong answer key during testing — that is why generated probes
are last-resort and self-audited. Model size is a dial, not a rewrite: set
`GEMMA_MODEL=gemma3:12b` and every call above upgrades in place.

## Reliability by design

The parts that must be correct never rely on the model guessing: diagnosis is a
**table lookup** from the tagged answer key, and the correct solution comes straight
from the verified bank. Gemma is used only where it's strong — writing the explanation
and generating fresh practice.

---
*Built for the GDG Windsor · Build with AI — Gemma Hackathon. Edge / On-Device track.*
