# Submission: Gemma Monsters

**Team:** Gokulakrishnan, Padmanabha, Taha, Naimah, Amarah
**Event:** Build with AI - Gemma Hackathon, GDG Windsor · **Track:** Edge / On-Device

An autonomous Grade 9 EQAO maths tutor wrapped in a three.js monster game, running on one laptop through Ollama.

## Inspiration - what local problem are you solving?

Every Grade 9 student in Ontario sits a provincial mathematics assessment on the MTH1W course. Around Windsor-Essex that is a household deadline, and the help on offer is a tutor at sixty dollars an hour or an app that marks answers. The thing the apps miss: a wrong answer is not noise, but evidence of a specific wrong idea that feels right. Ask for 2/3 + 1/4 and watch for 3/7. Tops with tops, bottoms with bottoms — tidy, symmetric, and wrong. Marking it wrong teaches nothing, because the student who wrote 3/7 already believed 3/7. That is not carelessness but a rule applied faithfully. We call each one a trick.

Cloud tutors explain better, but they need connectivity, and a fourteen-year-old's worked-out mistakes should not leave the house. All of this runs on the family's own hardware.

Five monsters hold the citadel, each out to get the student in its own favourite way. Fractis whispers "just add straight across". Equazor waits for a sign to cross the equals sign. Statiq blurs mean and median together. You do not get past one by luck, but by showing its favourite trap no longer works on you.

## How we built it - which Gemma model, RAG, prompt engineering or fine-tuning, what frameworks?

**Model.** `gemma3:12b` served locally by Ollama. `gemma3:1b` is one environment variable away (`GEMMA_MODEL`), and every call site switches with it. We developed against both, because what the 1b gets wrong told us where the guardrails had to go: on identical prompts it under-detects thin reasoning that the 12b catches reliably, so the code, never the model, owns the streak and the caps.

**No fine-tuning. No vector RAG.** Retrieval is a deterministic tag lookup against a verified bank — similarity search was never needed, because the payload is an exact answer key. Everything else is prompt engineering wrapped in code that refuses bad replies.

**Frameworks.** Python and Streamlit for the agent and shell; three.js vendored into `static/vendor`; CC0 Quaternius models; original audio. No CDN, no external request, no account, no telemetry.

**The game.** A skippable five-beat introduction opens onto an orbitable citadel with the five monsters posted on it, one per MTH1W strand; choosing one drops you into a torch-lit hall for the encounter. Above them sits the Collector, a giant skull running a ninety-second mental-maths speed trial on three lives, with three lieutenants to drill first — Twinfang on doubles, The Niner on nines, Splitjaw on make-a-ten. Break all five seals and the gate opens for the rescue.

**The shape: deterministic control flow, Gemma at the judgment points.** Every model call the app makes passes through one function, `ask_gemma()`, each site constrained by the code around it.

- **The mastery loop** (`mastery.py`) runs TEACH -> CHECK -> EVALUATE -> ADAPT against a *fixed* four-rung strategy ladder: Direct correction, Visual walkthrough, Side-by-side contrast, Real-world analogy. Gemma picks the next rung from the remaining list and states its reason; an unparseable reply advances one rung in plain code.
- **The mastery bar** is two fresh correct in a row. The reasoning box under each answer is optional, and the submit button never waits on it; when the student does explain their thinking, that explanation is graded, and a thin one leaves the streak where it is. Three caps end a session: four check attempts, twelve model calls, or an exhausted ladder.
- **The grounding rule.** On the curriculum path — the bank-backed teaching and checking — Gemma never recomputes the maths. The verified worked solution rides in the prompt as the only arithmetic it may state; its job is to explain *why* the student's method fails. The Collector's mental-maths lanes are the exception: the strategy whisper before a drill and the coach's read of the misses afterwards teach without a key in hand, and neither marks a student's work.
- **Bank first, generation under audit.** Check questions come from the 55-item bank before anything is written. A Gemma-authored question is shown only if Gemma solves it again blind — without seeing the key it just wrote — and agrees with itself (`mastery._self_check`).
- **The reasoning grader** (`mastery._grade_reasoning`) classifies a typed explanation into a closed label set — RESOLVED, SHALLOW, SAME_ERROR — and fails open: parse trouble returns RESOLVED, so a model hiccup cannot cost a student a streak. `mastery._reaction` then has the citadel answer those words in character.
- **The director** (`agent.direct_next`) lets Gemma decide *where the student goes next* — which monster to hunt, which lieutenant to drill — citing its evidence. Code owns the candidate list and rejects any reply that does not name a real, still-open fight.
- **Letters home** persist to `data/letters/<challenger>.json`, behind a button on every screen. Notes go home after any battle with mistakes, on a hand-off, and on wins — a parent who only hears from us on the worst day cannot see a pattern. From that page one button builds a printable worksheet (`practice_sheet.py`): up to ten questions on one trick, working space under each, answer key on its own page, bank first and audited generation.

**The bank** (`data/questions.json`): 55 items across the five MTH1W strands, audited against the published MTH1W expectations and the EQAO framework. The key is balanced 14/14/14/13 across A–D. Every wrong option carries a `trick_id` and the faulty thinking behind it.

## One wrong answer, traced end to end

`NUM-ITEM-04`: *Calculate 2/3 + 1/4.* The verified solution is in the bank: LCD 12, so 8/12 + 3/12 = 11/12.

A student in Fractis's battle picks **C, "3/7"**, tagged `NUM-6`, *Adding fractions straight across*. `tutor.diagnose()` is a pure lookup — no model call, no guess. Option **D**, "1/4 (that is, 3/12)", is a different trick on the same question, `NUM-6b`: *Common denominator found but numerators not rescaled*. Two students can miss one item for two reasons and get two different sessions.

`agent.analyze()` counts trick frequency across the battle and picks the priority; Fractis's report names it. The study guide goes out with the answer and worked solution already in the prompt, Gemma explaining only why tops-with-tops fails.

The mastery loop opens on rung one, Direct correction. `next_check` looks for an unused bank item tagged `NUM-6`, then falls to an unused Number item — the key stays ground truth either way. The student answers correctly and writes "I just added them properly this time": SHALLOW, the streak does not advance, and the citadel says so out loud. Write "I made twelfths and got 3/12" and it is SAME_ERROR against `NUM-6b`. Miss it outright, and Gemma reads those same words to pick rung two, Visual walkthrough, and says why it is switching.

Two fresh correct, and Gemma forges a relic from what was overcome. If the caps trip first, the session hands off: a letter to mum and dad naming the approaches already tried, plus a printable sheet on `NUM-6`.

## The Prototype

- **GitHub repo:** https://github.com/EdTechDL/gemma-without-borders
- **Demo video:** *[PLACEHOLDER — link to be added]*
- **Kaggle notebook:** *[PLACEHOLDER — link to be added]*

Run it with Ollama and `streamlit run app.py`.

## Challenges we ran into

**The model invented arithmetic inside its explanations.** Asked to re-explain a solved question, it would redo the sums and land somewhere new, in confident prose beside a correct answer. Hence the grounding rule.

**The model marked its own generated question with the wrong key.** A student would have been told they were wrong for being right. Hence the blind self-solve audit: on screen a disagreement costs a silent retry; on a printed sheet it would cost a parent's evening.

**The model answered in Spanish.** Mid-session, unprompted. Every prompt that asks for freshly written text — a new question, a line back about the student's reasoning — now says English explicitly.

**The model fabricated counts in prose.** It wrote "beaten three tricks" when one trick had been beaten, borrowing a number that belonged to a different count on the same page. Vetting figures one at a time cannot catch a real number paired to the wrong noun, so the rule is absolute: code prints every figure, the model prints none, and in `progress.py` any summary containing a digit is discarded for a deterministic sentence.

**58% of the bank's correct answers sat on option A.** A student who always guessed A would score well and learn nothing. Balancing the key to 14/14/14/13 removes that single-letter edge, and it meant the wrong-answer commentary could not lean on option letters — those notes are keyed to the answer's text, true however the options are ordered.

Underneath all five: a small model is a capable judge and an unreliable authority. Everything it says here is a judgment; nothing it says is the source of mathematical truth.
