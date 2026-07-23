# GEMMA MONSTERS — an on-device math adventure

*An autonomous Gemma tutor that hunts down the wrong idea behind every wrong answer — and teaches, in different ways, until it is gone. Edge / On-Device track.*

## The problem

Grade 9 students preparing for Ontario's EQAO math assessment do not fail randomly. Behind most wrong answers sits a specific wrong idea that feels right — "add fractions straight across," "flip the sign when you move it, or don't," "mean and median are basically the same." Typical practice apps mark the answer wrong and move on, leaving that wrong idea intact. Cloud AI tutors can do better, but they require connectivity, ship a child's work to a third-party server, and — critically — will confidently invent mathematics when they hallucinate. A school-ready tutor needs three things at once: a diagnosis of *why* the student was wrong, teaching that adapts when a first explanation fails, and complete privacy on modest local hardware.

## What we built

GEMMA MONSTERS is a Streamlit application in which each curriculum unit is guarded by a monster that personifies its signature trick — the wrong idea students fall for: Fractis (Number), Equazor (Algebra), Statiq (Data), Polygor (Geometry & Measurement), and Ledgerling (Financial Literacy). The student enters a three.js "Nexus" hub — five animated 3D monsters, bloom, orbit camera — clicks a monster, and faces its unit's real diagnostic quiz. Miss questions and the monster "gets you": its trick was in your head all along.

Then the agent takes over. The mastery loop is a TEACH → PROBE → EVALUATE → ADAPT state machine. It teaches against the diagnosed trick through a fixed ladder of four pedagogies (direct correction, visual walkthrough, side-by-side contrast, real-world analogy), probes with a fresh question the student has never seen, grades not just the answer but the student's *typed reasoning*, and — when a lesson does not land — Gemma picks the next teaching strategy from the remaining ladder and states why. The loop terminates deterministically: mastery is two consecutive fresh questions correct with reasoning that holds up (no fluke wins), and any failure path ends in a teacher hand-off with a Gemma-written report containing three concrete "try in class" interventions informed by which strategies already failed. Every agent decision — priority choice, count/not-count, strategy switch, mastery, hand-off — displays an evidence-based rationale. A Classic mode offers the identical agent without the game skin.

## How Gemma is used

Gemma (Gemma 3, running locally via Ollama) is not a text box bolted onto a quiz. It sits at every decision point of the agent loop, and every call in the system passes through one auditable door — `ask_gemma()` in `gemma_client.py` — always constrained so a model mistake cannot corrupt the loop. Eight call sites:

| Call site | What Gemma does | Capability | Guardrail |
|---|---|---|---|
| Study-guide explanation | Explains the student's specific error | Generation | Facts come from the verified bank; may not recompute or state new numbers |
| Practice picker | Fresh practice per mistake | Generation | Bank-first; generation is last resort and never produces an answer key |
| Mastery lessons | Strategy-specific lesson, 4 distinct pedagogies | Generation | Recipe fixed by the ladder; grounded in the verified solution |
| Reasoning grader | Classifies typed reasoning: RESOLVED / SHALLOW / SAME_ERROR | Reasoning, structured output | Closed label set; fails open; right answer + shaky reasoning does not count |
| Strategy chooser | Picks the next teaching strategy, with a stated reason | Decision-making | Restricted to the remaining ladder; deterministic fallback on parse failure |
| Probe generator | Authors a new check question as JSON when the bank is exhausted | Structured output | Must pass a blind self-solve audit before a student ever sees it |
| Hint ladder | Progressive hints — nudge, then first step | Generation | Grounded in the verified solution; may not invent numbers |
| Vision transcription | Reads a photo of handwritten work, on-device (12B) | Multimodal | Transcribes only; correctness is judged against the bank |

Teacher reports use the same door: scores, diagnosed tricks, and strategies tried are computed deterministically and injected into the prompt; Gemma writes only the interpretation and interventions.

Equally deliberate is what Gemma is *not* allowed to do: grade multiple-choice answers (ground-truth key), diagnose the trick behind a wrong answer (ground-truth tags on every wrong option), or decide loop termination (hard caps in plain code). The model does the thinking; it is never the source of mathematical truth. Model size is a dial, not a rewrite — `GEMMA_MODEL=gemma3:12b` upgrades every call site in place.

## Reliability engineering

- **Diagnosis is a table lookup.** All 36 bank questions have every wrong option tagged with the trick it reveals. Diagnosis reads the tag — 100 percent deterministic, verified twice by independent passes.
- **Grounding rule.** Every generation prompt carries the verified worked solution with an explicit instruction: do not invent numbers or redo the calculation. All output passes through `plainify()` before display.
- **Bank-first, audit-second.** Fresh probes prefer unused verified items. When Gemma must author a question, it is used only if Gemma can then solve it blind — without seeing its own answer key — and agree with itself. Failures are silently discarded.
- **Hard caps guarantee termination.** Four probe attempts, twelve model calls, and strategy-ladder exhaustion each independently force teacher hand-off. The loop cannot run forever regardless of model behavior.
- **Fail-open grading.** An unparseable grader reply defaults to RESOLVED; a model hiccup can never punish a student.

Testing across model sizes shaped this architecture. The 1B model invented wrong arithmetic when re-explaining a solution — hence the grounding rule. It generated a question with a wrong answer key — hence bank-first selection plus the blind self-solve audit. And it under-detects shallow reasoning that the 12B catches reliably on identical prompts — evidence that the guardrails, not the model, carry correctness, while model size purely dials quality.

## Edge / on-device

Everything runs locally. Gemma serves through Ollama on a laptop — 0.8 s per call on the 12B after load; the 1B (an 815 MB pull) runs the full text pipeline on modest hardware. Photo transcription of handwritten work runs on-device through the 12B's vision capability at about 3 s, so a student can snap their paper working and the app never uploads the image anywhere. The three.js library and all five monster models are vendored into the repo and served by Streamlit's static file serving, so the complete experience — game world included — works offline. No accounts, no telemetry, no student data leaving the machine. Without any model installed, the app still runs on a stub fallback, which made team development and demos resilient.

## Challenges we overcame

- **Sandboxed component iframes.** Streamlit renders custom components in iframes without ancestor-navigation permission, so the 3D hub cannot navigate its parent page. We redesigned the flow around what the sandbox *does* allow — the game card's Begin button opens the challenge in a new tab — instead of fighting the platform.
- **The model inventing arithmetic.** The 1B confidently produced wrong math mid-explanation. We stopped asking the model to compute at all: the verified solution rides in every prompt as the only math it may state.
- **Wrong answer keys on generated questions.** Caught in testing, solved structurally with the blind self-solve audit rather than prompt tweaks.
- **LaTeX in a plain-text UI.** Model output arrived studded with LaTeX; we built `plainify()` to strip it, rendered proper stacked fractions with KaTeX where we control the source, and fixed a Financial Literacy bug where dollar signs in currency were being parsed as math delimiters.

## What's next

Adaptive difficulty in the mastery loop using the bank's difficulty tags; a walkable player character in the Nexus; a larger multi-grade question bank; and a classroom pilot where teacher-report hand-offs land with real teachers.

## Credits

Built with Google's Gemma, running locally via Ollama. Monster models (Alien, Demon, Dragon Evolved, Fish, Frog) by Quaternius, CC0 public domain.
