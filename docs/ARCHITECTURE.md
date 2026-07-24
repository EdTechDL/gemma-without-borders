# Architecture

## System overview

Gemma Without Borders is a Streamlit application wrapped around an agent controller and an autonomous mastery loop, with a single auditable door to the model. The student takes a diagnostic quiz; `agent.py` grades it, diagnoses the trick behind each wrong answer — the specific wrong idea that felt right — by table lookup against a verified 36-item tagged question bank (`data/questions.json` — the ground truth for all answer keys, trick tags, and worked solutions), prioritizes the most frequent trick, and builds personalized study guides. `mastery.py` then runs a state machine — TEACH, CHECK, EVALUATE, ADAPT — that teaches through a fixed ladder of four strategies, poses a fresh check question after each lesson, grades typed reasoning, and terminates deterministically at mastery (two consecutive correct with sound reasoning) or a hand-off to the student's parents. Every model call in the system goes through one function, `ask_gemma()` in `gemma_client.py`, backed by a local Gemma via Ollama — fully on-device, with a placeholder stub if no model is installed.

## Where Gemma does the thinking

Gemma is not a text box bolted onto a quiz — it sits at every decision point of the agent loop, always through one door (`gemma_client.py`), always constrained so a model mistake cannot corrupt the loop:

| Call site | What Gemma does | Capability | Guardrail |
|---|---|---|---|
| `tutor.study_guide` | Personalized explanation of the student's specific error | Generation | Facts (correct answer, worked solution) come from the verified bank; the model may not redo the calculation or state new numeric results |
| `tutor.pick_practice` | Fresh practice question per mistake | Generation | Bank-first: an unused verified item is always preferred; generation is last resort and produces the question only — never an answer key |
| `mastery.teach` | Strategy-specific lesson (4 distinct pedagogies) | Generation | Strategy recipe fixed by the ladder; lesson grounded in the verified solution — no invented calculations |
| `mastery._grade_reasoning` | Classifies the student's typed reasoning: RESOLVED / SHALLOW / SAME_ERROR | Reasoning, structured output | Closed label set; fail-open to RESOLVED; a right answer with shaky reasoning does not count toward mastery |
| `mastery._choose_strategy` | Picks the next teaching strategy from the remaining ladder, with a stated reason | Reasoning, decision-making, structured output | Choice restricted to the remaining menu; deterministic ladder fallback on any parse failure |
| `mastery._generated_check` | Authors a new check question (JSON) when the bank is exhausted | Structured output | Must pass a blind self-solve audit (`_self_check`) before a student ever sees it |
| `tutor.hint` | Progressive hints on practice questions (nudge, then first step) | Generation | Grounded in the verified solution; may not invent numbers |
| `gemma_client.transcribe_image` | Reads a photo of the student's handwritten work, on-device | Multimodal (vision) | Transcribes only — correctness is always judged against the verified bank |

The reports for mum and dad (`agent.teacher_report`, `mastery.escalation_report`) use the same door: the facts (score, diagnosed tricks, strategies tried, attempt counts) are computed deterministically and injected into the prompt; Gemma writes only the interpretation and the ten-minute kitchen-table activities under "Try at home:".

What Gemma is deliberately not allowed to do: grade multiple-choice answers (ground-truth key), diagnose bank items (ground-truth tags), or decide loop termination (hard caps in plain code). Model size is a dial, not a rewrite: set `GEMMA_MODEL=gemma3:12b` and every call above upgrades in place.

## Reliability by design

- **Diagnosis is a table lookup.** Every wrong option in the bank is tagged with the trick it reveals; `tutor.diagnose` reads the tag. No model call, no guessing — 100 percent deterministic.
- **Answer keys and worked solutions come from the verified bank.** Multiple-choice grading and the "correct method" shown to students never depend on the model.
- **Model output is sanitized and grounded.** Every human-facing string passes through `plainify()` (LaTeX stripped to plain math notation), and every generation prompt carries the verified solution with an explicit rule: do not invent numbers or recompute.
- **Generated questions must audit themselves.** When the bank is exhausted, a Gemma-authored check question is only used if Gemma can solve it blind — without seeing its own answer key — and agree with itself. A question that fails its own audit is silently discarded.
- **Hard caps guarantee termination.** Four check attempts, 12 model calls, and strategy-ladder exhaustion each independently force a hand-off to the parents. The loop cannot run forever, regardless of model behavior.
- **Reasoning grading fails open.** If the grader's reply does not parse, the label defaults to RESOLVED. A model hiccup can never punish the student.

## Findings from testing

- The 1B model invented wrong arithmetic when asked to re-explain a solution. Response: the grounding rule — the verified solution is supplied in the prompt and is the only math the model may state.
- The 1B model produced a generated question with a wrong answer key. Response: check questions are drawn from the bank first, and anything generated must pass the blind self-solve audit.
- The 1B model under-detects shallow reasoning that the 12B model catches reliably — same architecture, same prompts. Model size is a quality dial, switched with the `GEMMA_MODEL` environment variable.

## File map

- `app.py` — Streamlit UI and stage router: intro, quiz, results, mastery, map (game hub)
- `agent.py` — agent controller: grade_quiz, analyze (priority trick, escalation), build_study_guides, the Gemma-written report for mum and dad (`teacher_report`)
- `mastery.py` — autonomous mastery loop: MasterySession state machine, teach, next_check, submit_answer, rationale, escalation report
- `tutor.py` — study-guide cards: diagnosis lookup, grounded explanation, bank-first practice picker, hint ladder
- `gemma_client.py` — the one door to the model: ask_gemma (Ollama HTTP), plainify, transcribe_image (vision), report formatting, stub fallback
- `data/questions.json` — 55 verified EQAO-style questions, every one mapped to a published MTH1W expectation, every wrong option tagged with its trick (ground truth)
- `.streamlit/config.toml` — theme and hot-reload settings
- `docs/` — slides, notebook walkthrough, handoff, this document
