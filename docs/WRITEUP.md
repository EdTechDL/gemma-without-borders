# GEMMA MONSTERS — an on-device math adventure powered by Gemma

*Edge / On-Device track. An autonomous local tutor in a monster-battling castle: Gemma hunts the trick — the wrong idea that feels right — behind every wrong answer, and teaches until it is gone.*

## The problem

Grade 9 students preparing for Ontario's EQAO assessment (MTH1W) do not fail randomly. Behind most wrong answers sits a specific trick — a wrong idea that feels right: "add fractions straight across," "mean and median are basically the same." Typical practice apps mark the answer wrong and move on; the trick stays. Cloud tutors can do better, but they need connectivity, ship a child's work to a server, and confidently invent mathematics when they hallucinate. A school-ready tutor needs three things at once: a diagnosis of *why* the student was wrong, teaching that adapts when the first explanation fails, and complete privacy on modest local hardware.

## The game

The front door is the Citadel: a gothic castle nexus built in three.js, with a drag-orbit camera and five monsters idling on floating platforms — Quaternius CC0 models with hand-curated animations. Each guards one curriculum strand: Fractis (Number), Equazor (Algebra), Statiq (Data), Polygor (Geometry & Measurement), Ledgerling (Financial Literacy). At the heart of the castle stands a sealed golden gate. Someone is locked in the keep; defeating all five monsters breaks the seal — the rescue arc and finale.

The game captures your hero name once. Click a monster and it confronts you in a full-screen encounter cinematic, by name — and because Gemma writes a battle memory line from your record, it *remembers* you: return after a loss and it gloats. The battle is the strand's quiz from a verified 55-question bank; the battle report shows exactly what got you, then hands off to a Gemma-grounded study guide with real exponent and fraction notation.

Mastery drops a relic — a trophy Gemma forges from what you actually overcame. Struggle, and escalation summons THE COLLECTOR: a giant skull boss running a client-side mental-math speed trial — three lives, under attack. His three lieutenants hold the training grounds — Twinfang (doubles), The Niner (nines), Splitjaw (make-a-ten) — each a 90-second war-clock skirmish with streak escalation. Before a skirmish, Gemma whispers the lane's mental strategy; after, miss and latency telemetry feed GET COACHED BY GEMMA: Gemma names your miss pattern, teaches the fix, sets a three-question drill. A procedural WebAudio soundscape — no audio files — scores it all.

## The agent under the hood

Beneath the game runs an autonomous mastery loop: TEACH → PROBE → EVALUATE → ADAPT. The agent teaches against the diagnosed trick through a fixed ladder of pedagogies, probes with a fresh question the student has never seen, and evaluates both the answer *and* the student's typed reasoning — a right answer with shaky reasoning does not count toward mastery. When a lesson does not land, Gemma picks the next strategy from the remaining ladder and states its rationale on screen. Every agent decision — strategy switch, count/no-count, mastery, escalation — shows its why. Mastery ends with a forged relic. Ladder exhaustion ends with the Collector *and* a Gemma-written teacher report: what was diagnosed, what was tried, what to try in class. The agent never gives up silently — it hands the student to a human.

## Where Gemma does the thinking

Every model call passes through one auditable door — `ask_gemma()` in `gemma_client.py` — each site constrained so a model mistake cannot corrupt the loop:

| Call site | What Gemma does | Guardrail |
|---|---|---|
| Study-guide explanations | Explains the student's specific error | Facts come from the verified bank; never recomputes or states new numbers |
| Mastery lessons | Writes a strategy-specific lesson per ladder rung | Recipe fixed by the ladder; grounded in the verified worked solution |
| Reasoning grading | Classifies typed reasoning: RESOLVED / SHALLOW / SAME_ERROR | Closed label set; fails open; shaky reasoning blocks mastery, never punishes |
| Strategy choice | Picks the next teaching strategy, with a stated rationale | Restricted to the remaining ladder; deterministic fallback on parse failure |
| Fresh probes | Authors a new check question as JSON when the bank runs dry | Must pass a blind self-solve audit before a student ever sees it |
| Relic forging | Names and inscribes the relic from the student's real battle | Flavor only; may not make mathematical claims |
| Battle memory lines | One encounter line recalling the student's history | Grounded in logged results; a stock line stands in if generation fails |
| Strategy whispers | Teaches the lane's mental strategy before a skirmish | Strategy fixed per lane; Gemma phrases it, never picks it |
| Telemetry coaching | Reads miss + latency data, names the miss pattern, sets a 3-question drill | Telemetry computed client-side; drill stays inside the lane's fact family |
| Teacher reports | Interprets the record; proposes classroom interventions | Scores, diagnosed tricks, and strategies tried are computed deterministically and injected; Gemma writes only interpretation |

Equally deliberate is what Gemma may *not* do: grade multiple-choice answers (ground-truth key), diagnose the trick behind a wrong answer (every wrong option is trick-tagged in the bank), or decide loop termination (hard caps in plain code). The model does the thinking; it is never the source of mathematical truth.

## Reliability engineering

- **Verified bank.** All 55 questions carry worked solutions, and every wrong option is tagged with the trick it reveals — diagnosis is a deterministic table lookup.
- **Grounding rule.** The model never recomputes math shown to students. Every generation prompt carries the verified solution with an explicit instruction: do not invent numbers or redo the calculation.
- **Bank-first, audit-second.** Fresh probes prefer unused verified items. When Gemma must author one, it is used only if Gemma can then solve it blind — without seeing its own answer key — and agree with itself. Failures are discarded.
- **Hard caps.** Probe attempts, a model-call budget, and ladder exhaustion each force teacher hand-off. The loop terminates regardless of model behavior.
- **Fail-open grading.** An unparseable grader reply defaults to RESOLVED; a model hiccup can never punish a student.

Testing across model sizes shaped this architecture. The 1B invented wrong arithmetic while re-explaining a solution — hence the grounding rule. It generated a question with a wrong answer key — hence bank-first plus the blind audit. And it under-detects shallow reasoning that the 12B catches on identical prompts — evidence that the guardrails, not the model, carry correctness, while model size dials quality.

## Edge story

Everything runs on-device. Gemma serves locally through Ollama: `gemma3:12b` is the primary brain; `gemma3:1b` is the light option for modest hardware — `GEMMA_MODEL` switches every call site in place. The three.js library and all monster models are vendored into the repo; the soundscape is synthesized in WebAudio, so there are no audio files, no CDNs, no external requests. The whole experience works offline. No accounts, no data collection: a student's work never leaves their machine. A companion Kaggle notebook reproduces the agent loop on cloud GPU with Gemma 4 12b-it.

## Challenges overcome

- **Sandboxed component iframes.** Streamlit renders components in iframes that cannot navigate their parent page. We redesigned the flow around what the sandbox allows instead of fighting the platform.
- **The model inventing arithmetic.** The 1B confidently produced wrong math mid-explanation. We stopped asking the model to compute at all: the verified solution rides in every prompt as the only math it may state.
- **Wrong generated answer keys.** Caught in testing; solved structurally with the blind self-solve audit rather than prompt tweaks.
- **Notation rendering.** Model output arrived studded with LaTeX. We strip it, render true stacked fractions and exponents ourselves, and fixed currency dollar signs being parsed as math delimiters.
- **Animation curation.** CC0 packs ship dozens of clips per model, most wrong for a castle guard; each monster's ambient and fight clips were hand-picked and re-timed.

## What's next

Adaptive difficulty from the bank's difficulty tags; a walkable hero in the Citadel; more lieutenants for more fact families; multi-grade banks; a classroom pilot where teacher reports land with real teachers.

## Credits

Built with Google's Gemma, running locally via Ollama. Monster and boss models by Quaternius, CC0 public domain.
