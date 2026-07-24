# GEMMA MONSTERS — an on-device math adventure powered by Gemma

*Edge / On-Device track. A local tutor in a monster-battling castle: Gemma hunts the trick — the wrong idea that feels right — behind every wrong answer, teaches until it is gone, and writes home to mum and dad.*

## The problem

Grade 9 students preparing for Ontario's EQAO assessment (MTH1W) do not fail randomly. Behind most wrong answers sits a specific trick — a wrong idea that feels right: "add fractions straight across," "mean and median are basically the same." Practice apps mark the answer wrong and move on; the trick stays. Cloud tutors do better, but they need connectivity, ship a child's work to a server, and invent mathematics when they hallucinate. A school-ready tutor needs four things at once: a diagnosis of *why* the student was wrong, teaching that adapts when the first explanation fails, a parent who can see it, and privacy on modest local hardware.

## The game

A new challenger opens on a skippable five-beat introduction, staged in the game's 3D world with the real models: the title, the five in a row with the strand each guards, how a battle is won, the Collector arriving in colder light, and the promise that every question and answer stays on this laptop.

Then the Citadel: a gothic castle nexus in three.js, drag to orbit, five Quaternius CC0 monsters idling on floating platforms with hand-curated animations — Fractis (Number), Equazor (Algebra), Statiq (Data), Polygor (Geometry & Measurement), Ledgerling (Financial Literacy) — under a sealed golden gate. Someone is locked in the keep; beating all five breaks the seal. Click a monster and it confronts you full-screen, by name, and because Gemma writes its greeting from your record it *remembers* you: return after a loss and it gloats. The battle is that strand's quiz from the verified bank; the report names what got you, then hands off to a Gemma-grounded study guide.

Mastery drops a relic Gemma forges from what you overcame. Struggle, and escalation summons THE COLLECTOR: a giant skull running a client-side mental-math speed trial — three lives, under attack, his own looping theme. His lieutenants hold the training grounds — Twinfang (doubles), The Niner (nines), Splitjaw (make-a-ten) — 90-second skirmishes with a cue on every correct answer, Gemma whispering the lane's strategy first and coaching from your misses after. One **Sound** switch in the citadel header governs all of it.

## The agent under the hood

Beneath the game runs an autonomous mastery loop: TEACH → CHECK → EVALUATE → ADAPT. The agent teaches the diagnosed trick through a set ladder of pedagogies, poses a check question the student has never seen, and evaluates both the answer *and* the typed reasoning — a right answer with shaky reasoning does not count. Gemma answers that reasoning out loud too, in the citadel's voice, naming the idea in their own words that held up or slipped; fishing for compliments earns a warning that the monsters ahead only fall to real reasoning. When a lesson does not land, Gemma picks the next approach and says why. Every decision shows its evidence.

Gemma also directs the session: after a battle it chooses which monster to hunt next, outside the Collector's arena which lieutenant to drill, and names the evidence from the run. Plain code owns the candidate list — real, still-open fights only — and rejects any answer that does not name one, so the director can never invent a destination or send a student somewhere already beaten.

## The parents

Every note the agent writes goes to a letters-home page, reachable from a button pinned to each screen. Notes go home after **any** battle where something was missed — not only when a run falls apart — because a parent who hears from us only on the worst days cannot see a pattern, or progress. Beating a trick is a letter too, with the evidence behind the call. Letters persist to disk, so closing the tab does not lose them.

From that page a parent presses one button and gets a printable practice sheet: up to ten questions on one trick, working space under each, an answer key on its own page — a standalone document, no fonts, no scripts, no requests. Verified bank items fill it first; anything Gemma writes must solve its own question again, blind to the key it just wrote, and agree, or it never reaches the paper. On screen a bad key costs one silent retry; on a printed sheet it would cost a parent's evening.

## Where Gemma does the thinking

Every model call passes through one auditable door — `ask_gemma()` — each site constrained so a model mistake cannot corrupt the loop:

| Call site | What Gemma does | Guardrail |
|---|---|---|
| Direction | Picks the next monster or lieutenant, naming the evidence | Candidates built in code, any other reply refused; the record it gets is declared complete, so no history can be invented |
| Study guides | Explains the student's specific error | Facts come from the bank; never recomputes or states new numbers |
| Mastery lessons | A lesson per rung of the teaching ladder | Recipe set by the ladder; grounded in the verified solution |
| Reasoning grading | Classifies typed reasoning: RESOLVED / SHALLOW / SAME_ERROR | Closed label set; fails open; shaky reasoning blocks mastery |
| Answering the student | Reacts to their typed words | Comment only; the grader decides what counts |
| Approach choice | Picks the next rung, and why | Restricted to the remaining ladder; deterministic fallback |
| Fresh check questions | Authors one as JSON when the bank runs dry | Must pass a blind self-solve audit first |
| Printable practice | Fills a parent's sheet when the bank runs short | Same audit, plus a call budget: a short sheet beats an unverified one |
| Relics and greetings | Names the trophy; recalls the student's history | Flavour only; no mathematical claims |
| Skirmish coaching | Names the miss pattern and sets a drill | Telemetry computed client-side; the drill stays in the lane |
| Reports for mum and dad | Interprets the record; proposes kitchen-table activities | Scores, tricks and approaches tried are computed in code |

Equally deliberate is what Gemma may *not* do: grade multiple-choice answers, diagnose the trick behind a wrong answer, choose a destination off the list, or decide when the loop ends. It does the thinking; it is never the source of mathematical truth.

## Reliability engineering

- **Verified bank.** 55 questions, every one inside what the EQAO Grade 9 assessment covers and mapped to a published MTH1W expectation, each with a worked solution and every wrong option tagged with the trick it reveals — so diagnosis is a table lookup, not a guess. The key is balanced across A–D so it cannot be gamed, and wrong-answer notes are keyed to the answer's *text*, never its letter, so they stay true however options are ordered.
- **Grounding rule.** The model never recomputes math shown to students; the verified solution rides in every prompt as the only math it may state.
- **Bank-first, audit-second.** Verified items are always preferred; anything generated must survive the blind self-solve, on screen and on paper.
- **Hard caps.** Check attempts, call budgets and ladder exhaustion each force termination — the hand-off to mum and dad, or a shorter sheet.
- **Fail-open grading.** An unparseable grader reply defaults to RESOLVED; a hiccup can never punish a student.
- **Clean notation.** Model output arrives studded with LaTeX. We strip it, render true stacked fractions and exponents ourselves, and decide per dollar sign whether it is money or a delimiter.

Testing across model sizes shaped every one of those rules. The 1B invented arithmetic while re-explaining a solution; it wrote a question with a wrong answer key; asked to choose a destination, it narrated a history the student never had. Hence grounding, the blind audit, the closed candidate list. It also under-detects shallow reasoning the 12B catches on identical prompts: the guardrails carry correctness, model size dials quality.

## Edge story

Everything runs on-device. Gemma serves through Ollama: `gemma3:12b` is the primary brain, `gemma3:1b` the light option — `GEMMA_MODEL` switches every call site in place. three.js, the monster models and the audio themes are vendored into the repo; battle stingers are synthesized in WebAudio. No CDNs, no external requests, no accounts, no data collection. The letters written about a child stay on that family's machine. A companion Kaggle notebook reproduces the loop on cloud GPU.

## What's next

Adaptive difficulty from the bank's difficulty tags; a walkable hero in the Citadel; more lieutenants; multi-grade banks; a home pilot where the letters land with real parents.

## Credits

Built with Google's Gemma via Ollama. Monster models by Quaternius, CC0. Themes generated with ElevenLabs.
