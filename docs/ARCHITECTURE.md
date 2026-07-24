# Architecture

## System overview

GEMMA MONSTERS is a Streamlit application wrapped around an agent controller and an autonomous mastery loop, with a single auditable door to the model. A first-time challenger meets a skippable 3D introduction, then enters the citadel. The student takes a battle (the strand's diagnostic quiz); `agent.py` grades it, diagnoses the trick behind each wrong answer — the specific wrong idea that felt right — by table lookup against a verified 55-item tagged question bank (`data/questions.json` — the ground truth for all answer keys, trick tags, and worked solutions), prioritizes the most frequent trick, and builds personalized study guides. `mastery.py` then runs a state machine — TEACH, CHECK, EVALUATE, ADAPT — that teaches through a set ladder of four strategies, poses a fresh check question after each lesson, grades and answers the student's typed reasoning, and terminates deterministically at mastery (two consecutive correct with sound reasoning) or a hand-off to the student's parents. `agent.direct_next` lets Gemma decide where the session goes next. Everything written for the parents is kept on a letters-home page and can be turned into a printable practice sheet by `practice_sheet.py`. Every model call in the system goes through one function, `ask_gemma()` in `gemma_client.py`, backed by a local Gemma via Ollama — fully on-device, with a placeholder stub if no model is installed.

## Where Gemma does the thinking

Gemma is not a text box bolted onto a quiz — it sits at every decision point of the agent loop, always through one door (`gemma_client.py`), always constrained so a model mistake cannot corrupt the loop:

| Call site | What Gemma does | Capability | Guardrail |
|---|---|---|---|
| `agent.direct_next` | The director: chooses the next fight — which monster to hunt, which of the Collector's lieutenants to drill — and names the evidence for it | Reasoning, decision-making, structured output | Plain code builds the candidate list (real, still-open fights only) and rejects any reply that does not name one; the evidence lines are the complete record, and the model is told to invent no history |
| `tutor.study_guide` | Personalized explanation of the student's specific error | Generation | Facts (correct answer, worked solution) come from the verified bank; the model may not redo the calculation or state new numeric results |
| `tutor.pick_practice` | Fresh practice question per mistake | Generation | Bank-first: an unused verified item is always preferred; generation is last resort and produces the question only — never an answer key |
| `mastery.teach` | Strategy-specific lesson (4 distinct pedagogies) | Generation | Strategy recipe set by the ladder; lesson grounded in the verified solution — no invented calculations |
| `mastery._grade_reasoning` | Classifies the student's typed reasoning: RESOLVED / SHALLOW / SAME_ERROR | Reasoning, structured output | Closed label set; fail-open to RESOLVED; a right answer with shaky reasoning does not count toward mastery |
| `mastery._reaction` | Answers the student's typed reasoning directly, in the citadel's voice — naming the idea in their own words that held up or did not | Generation | Reacts only to what the student wrote; the grader above, not this line, decides what counts; off-topic or joking text gets a playful callout |
| `mastery._choose_strategy` | Picks the next teaching strategy from the remaining ladder, with a stated reason | Reasoning, decision-making, structured output | Choice restricted to the remaining menu; deterministic ladder fallback on any parse failure |
| `mastery._generated_check` | Authors a new check question (JSON) when the bank is exhausted | Structured output | Must pass a blind self-solve audit (`_self_check`) before a student ever sees it |
| `practice_sheet._one_generated` | Writes extra printable questions when the bank runs short on one trick | Structured output | Bank items fill the sheet first; every generated question must survive `_blind_solve_agrees` and a hard call budget, or it never reaches the paper |
| `tutor.hint` | Progressive hints on practice questions (nudge, then first step) | Generation | Grounded in the verified solution; may not invent numbers |
| `rewards.forge_relic` / `battle_memory_line` | Names the trophy a beaten trick drops; writes the line a monster greets a returning student with | Generation | Flavour only, built from logged session facts; no mathematical claims |
| Skirmish coaching (`app.coach_stage`) | Reads the misses from a 90-second speed drill, names the pattern, teaches the fix, sets a three-question drill | Reasoning, generation | Telemetry is computed client-side; a stock line stands in if the call fails |

The reports for mum and dad (`agent.teacher_report`, `mastery.escalation_report`) use the same door: the facts (score, diagnosed tricks, strategies tried, attempt counts) are computed deterministically and injected into the prompt; Gemma writes only the interpretation and the ten-minute kitchen-table activities under "Try at home:".

What Gemma is deliberately not allowed to do: grade multiple-choice answers (ground-truth key), diagnose bank items (ground-truth tags), invent a destination for the director, or decide loop termination (hard caps in plain code). Model size is a dial, not a rewrite: set `GEMMA_MODEL=gemma3:12b` and every call above upgrades in place.

## Reliability by design

- **Diagnosis is a table lookup.** Every wrong option in the bank is tagged with the trick it reveals; `tutor.diagnose` reads the tag. No model call, no guessing — 100 percent deterministic.
- **Answer keys and worked solutions come from the verified bank.** Multiple-choice grading and the "correct method" shown to students never depend on the model.
- **The bank itself is audited.** All 55 items sit inside what the EQAO Grade 9 assessment covers and map to a published MTH1W expectation. The answer key is balanced across A–D (14/14/14/13), so a student who always picks one letter learns nothing about the key. Wrong-answer notes live in a `traps` list keyed to the answer's **text**, never its letter, so they stay true no matter how the options are ordered.
- **Model output is sanitized and grounded.** Every human-facing string passes through `plainify()` (LaTeX stripped to plain math notation, house vocabulary normalized, currency signs preserved while math delimiters are not), and every generation prompt carries the verified solution with an explicit rule: do not invent numbers or recompute.
- **Generated questions must audit themselves.** When the bank is exhausted, a Gemma-authored check question is only used if Gemma can solve it blind — without seeing its own answer key — and agree with itself. The same audit gates every generated question on a printable practice sheet.
- **Hard caps guarantee termination.** Four check attempts, 12 model calls, and strategy-ladder exhaustion each independently force a hand-off to the parents. A practice sheet has its own 24-call ceiling and comes back short rather than unverified. Nothing can run forever, regardless of model behavior.
- **Reasoning grading fails open.** If the grader's reply does not parse, the label defaults to RESOLVED. A model hiccup can never punish the student.
- **The director cannot wander.** `agent.direct_next` is handed a candidate list built from real, still-open fights; a reply naming anything else falls back to code's own pick, with a reason that says plainly why.

## The letters home

Every note the agent writes for the parents — after any battle where something was missed, when the loop hands off, and when a trick is finally beaten — is saved by `app.save_letter` into session state and to `data/letters/<challenger>.json` on the same machine. Closing the tab does not lose them. A pinned button on every screen opens the letters-home page, where the notes stack newest-first, download as one file, and each diagnosed trick offers **Make a practice sheet**: `practice_sheet.build_sheet` lays out up to ten questions on that single trick with working space and an answer key on its own page, as a standalone printable HTML document with inline CSS and no external requests.

## Findings from testing

- The 1B model invented wrong arithmetic when asked to re-explain a solution. Response: the grounding rule — the verified solution is supplied in the prompt and is the only math the model may state.
- The 1B model produced a generated question with a wrong answer key. Response: check questions are drawn from the bank first, and anything generated must pass the blind self-solve audit — on screen it costs one silent retry; on a printed sheet it would cost a parent's evening.
- The 1B model under-detects shallow reasoning that the 12B model catches reliably — same architecture, same prompts. Model size is a quality dial, switched with the `GEMMA_MODEL` environment variable.
- Asked to choose a destination, a small model will happily narrate a history the student never had. Response: the director prompt states that the supplied evidence is the complete record, and code validates the choice against the candidate list.

## File map

- `app.py` — Streamlit UI and stage router: onboarding, citadel hub, encounter, quiz, results, mastery, boss arena, skirmishes, coaching, finale, letters home
- `onboarding.py` — the skippable first-run introduction: a five-beat 3D scene (title, the roster of five with their strands, how a battle is won, the Collector in colder light, the on-device promise) rendered with the real monster models, with its own looping theme
- `agent.py` — agent controller: grade_quiz, analyze (priority trick, escalation), build_study_guides, direct_next (the director), the Gemma-written report for mum and dad (`teacher_report`)
- `mastery.py` — autonomous mastery loop: MasterySession state machine, teach, next_check, submit_answer, reasoning grading and reaction, rationale, escalation report
- `tutor.py` — study-guide cards: diagnosis lookup, grounded explanation, bank-first practice picker, hint ladder
- `practice_sheet.py` — printable practice sheets for one trick: bank-first selection, audited generation, standalone print HTML with an answer key
- `rewards.py` — the creative layer: relic forging on mastery, battle memory lines for encounters
- `gemma_client.py` — the one door to the model: ask_gemma (Ollama HTTP), plainify, report formatting, stub fallback
- `data/questions.json` — 55 verified questions inside the EQAO Grade 9 assessment's coverage, each mapped to a published MTH1W expectation, every wrong option tagged with its trick (ground truth)
- `data/letters/` — the letters home, one JSON file per challenger, on this machine only
- `static/` — vendored three.js and loaders, CC0 monster models, the audio themes
- `.streamlit/config.toml` — theme and hot-reload settings
- `docs/` — slides, notebook walkthrough, handoff, this document
