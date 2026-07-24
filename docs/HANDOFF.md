# GEMMA MONSTERS — Full Project Handoff
Last updated: July 24, 2026. Written so any Claude session (or teammate) can pick up instantly.

## What we are building
An autonomous AI study agent for the Grade 9 EQAO math assessment (Ontario MTH1W curriculum),
built for the GDG Windsor "Build with AI — Gemma Hackathon" on Kaggle.
Track: EDGE / ON-DEVICE (a personal study assistant; Gemma runs locally — privacy story).
Team: Gokulakrishnan (frontend), Padmanabha (data/architecture), Taha (backend Python),
Naimah (testing/validation/writing), Amarah (coordination, integration, GitHub, this machine).

Core flow: first-run introduction → citadel → pick a monster → encounter → that strand's quiz
→ agent diagnoses WHICH trick caused each wrong answer (ground-truth lookup from a verified
tagged question bank — never model guessing) → Gemma writes a personalized study guide
(explanation grounded in the verified solution + fresh practice + hints) → "Practice until
mastery": an autonomous loop (TEACH → CHECK → EVALUATE → ADAPT) that teaches, poses fresh
check questions, grades AND answers typed reasoning, switches teaching approach when one
fails (Gemma picks the next one and says why), and stops at mastery (2 fresh correct in a
row with sound reasoning) or hands off to mum and dad with an actionable Gemma-written
report. Gemma then directs where the student goes next. Every agent decision shows an
evidence-based "why" (explainable AI).

GEMMA MONSTERS is the front door; simple mode (the plain quiz app, same brain) is one click
away from the intro screen.

## Where everything is
- Repo (private): https://github.com/EdTechDL/gemma-without-borders  (gh CLI is logged in as EdTechDL on this Mac)
- Local checkout: /Users/amarah/gemma-without-borders
- This handoff also lives in the repo: docs/HANDOFF.md (keep both updated)
- Slide decks (Beamer): docs/slides/gwb-demo.tex and docs/slides/gwb-judges.tex + PDFs
- Older working docs (brainstorm, test kits, Kaggle guides): /Users/amarah/remotion/
- Kaggle fallback demo notebook: gemma-tutor-CLEAN.ipynb in /Users/amarah/remotion/ (imported on Kaggle; teammate also has a Gradio version with 12B)

## File map (repo root)
- app.py           — Streamlit UI + router. Stages: onboard, intro (simple mode), map (citadel),
                     encounter, quiz, results, mastery, boss, skirmish, coach, finale, parents.
                     Also holds MONSTERS/_LIEUTENANTS, the three.js templates, the letters-home
                     store (save_letter/load_letters) and the pinned "For mum and dad" button.
- onboarding.py    — the skippable first-run introduction: five beats (title; the roster of five
                     with their strands; how a battle is won; the Collector in colder light; the
                     on-device promise) in a 3D hall with the real GLB models, its own looping
                     theme, and the shared gm_mute switch. Leaves via ?onboarded=1.
- agent.py         — grade_quiz, analyze (priority trick, escalation), build_study_guides,
                     direct_next (THE DIRECTOR: Gemma picks the next monster/lieutenant from a
                     code-owned candidate list and names the evidence), teacher_report
- mastery.py       — the autonomous loop: MasterySession, teach, next_check (bank-first),
                     submit_answer (deterministic grading + Gemma reasoning-grader
                     RESOLVED/SHALLOW/SAME_ERROR + _reaction, which answers the student's typed
                     words in the citadel's voice + Gemma approach choice + hard caps),
                     rationale (explainable AI), escalation_report
- tutor.py         — study_guide cards: grounded explanation, bank-first practice picker, hint ladder
- practice_sheet.py— printable parent worksheets for ONE trick: bank items first, then Gemma-written
                     questions that must pass a BLIND self-solve (_blind_solve_agrees) before they
                     reach the paper; renders a standalone print-ready HTML doc with an answer key
                     on its own page. Caps: 3 attempts per slot, 24 model calls per sheet.
- rewards.py       — forge_relic (mastery trophy), battle_memory_line (encounter greeting)
- gemma_client.py  — THE ONE DOOR to the model: ask_gemma (Ollama HTTP), plainify (LaTeX stripper +
                     house vocabulary + per-sign currency rule), format_teacher_report, availability
                     checks, stub fallback. transcribe_image (12B vision) still ships here; no screen
                     calls it today.
- data/questions.json — 55 verified questions, all inside what the EQAO Grade 9 assessment covers,
                     each mapped to a published MTH1W expectation, every wrong option tagged with its
                     trick (ground truth; multi-agent verified twice). Key balanced 14/14/14/13 across
                     A-D. Wrong-answer notes live in a "traps" list keyed to the ANSWER TEXT, never the
                     letter, so option order can change safely.
- data/letters/    — the letters home, one JSON file per challenger (gitignored territory: real
                     student text, keep it local)
- static/          — vendor three.js + loaders, Quaternius CC0 monster GLBs, audio themes
                     (nexus-theme, onboarding, collector-theme, correct cue)
- .streamlit/config.toml — theme + runOnSave=true
- docs/            — slides, notebook walkthrough, ARCHITECTURE.md (judge doc), WRITEUP.md
                     (Kaggle submission, HARD 1500-word limit), HANDOFF.md

## How to run it (this Mac)
```bash
cd /Users/amarah/gemma-without-borders
GEMMA_MODEL=gemma3:12b ./.venv/bin/streamlit run app.py --server.headless true --server.port 8501
```
- Ollama must be running (it autostarts; `ollama list` shows gemma3:1b and gemma3:12b installed).
- No model? App still runs with placeholder text (stub fallback).
- If port 8501 is stuck: `lsof -ti :8501 | xargs kill -9` then relaunch (KEEP 8501 — the team's tunnel URL points at it).

Useful direct routes: `?onboarded=1` (skip the intro), `?station=<strand>`, `?boss=1`,
`?skirmish=doubles|nines|split`, `?coach=<lane>&misses=...`, `?finale=1`, `?parents=1`, `?exit=1`.

## Team access (tunnel)
Amarah runs a Cloudflare quick tunnel pointing at localhost:8501:
```bash
cloudflared tunnel --url http://localhost:8501
```
It prints an https://….trycloudflare.com URL — share in team chat. Dies when the process
stops; just rerun and share the new URL (log at /tmp/gwb_tunnel.log). runOnSave=true means
file edits hot-reload for viewers; restarts keep the same URL as long as port 8501 is reused.
Teammates can also clone + run locally (README has steps; 1B model is an 815MB pull).

## Current state (what is DONE and verified)
- Quiz → results → study guide → mastery loop: working live on gemma3:12b (0.8s/call)
- Diagnosis = table lookup on tagged options (100% deterministic); answer keys from bank
- Explanations/hints grounded in verified solutions (model may not invent numbers — we
  caught the 1B inventing wrong math and architected around it; good writeup material)
- Reasoning grader: right answer + shaky typed reasoning does NOT count toward mastery
  (works on 12B; under-detects on 1B — documented finding). Alongside it, mastery._reaction
  answers the student's own words in the citadel's voice, including a playful callout when
  the box is filled with jokes.
- Teaching ladder: Direct correction → Visual walkthrough → Side-by-side contrast →
  Real-world analogy; Gemma chooses the next rung from the student's own words + why
- Hard caps: 4 check attempts, 12 Gemma calls, ladder exhaustion → hand-off to mum and dad
- THE DIRECTOR (agent.direct_next): after results, Gemma names the next monster to hunt; on the
  boss page, which lieutenant to drill. Code supplies candidates (still-open fights only) and
  rejects any reply that does not name one; evidence lines are declared the complete record so
  the model cannot narrate a history the student never had.
- LETTERS HOME (stage "parents"): every agent-written note kept for the session AND persisted to
  data/letters/<challenger>.json. Pinned "For mum and dad" button on every screen. Notes go home
  after ANY battle with mistakes, on hand-off, and on mastery wins (good news travels too).
  Download-all button. Deduped on body text.
- PRINTABLE PRACTICE (practice_sheet.py): one button per diagnosed trick on the letters page →
  up to 10 questions, working space, answer key on its own page, standalone HTML for the printer.
  Bank first; generated items must pass the blind self-solve.
- Question bank audited against the official MTH1W expectations and the EQAO Grade 9 framework
  (plus the November 2025 released questions); balanced answer key; traps keyed to answer text.
- Audio: nexus theme, onboarding theme, Collector theme (all local mp3s in static/audio, fetched
  as blobs because Streamlit serves .mp3 as text/plain), a short correct-answer cue in the speed
  arenas, procedural WebAudio stingers. ONE mute switch: localStorage key `gm_mute`, toggled from
  the citadel header button, read by the onboarding scene and every arena.
- Display: stacked KaTeX fractions; currency renders literally; LaTeX stripped from all model
  output (plainify); no emojis anywhere.
- Fresh-practice guarantee: "Now you try" never repeats a question the student saw;
  solution hidden until they attempt it
- Game: citadel hub, encounters with battle memory lines, relics, the Collector's speed trial,
  three lieutenant skirmishes + Gemma coaching, rescue finale

## Known TODO / next steps
1. Finish the full browser QA sweep of every screen (task #1) — onboarding → citadel → encounter →
   quiz → results → mastery → boss → skirmish → coach → letters → practice sheet download.
2. Adaptive difficulty using the bank's difficulty tags (Easy 22 / Medium 25 / Hard 8) — next
   agreed feature candidate.
3. Demo recording (90s script is in the deck) — record once QA is clean.
4. Kaggle submission: writeup ≤1500 words (docs/WRITEUP.md is currently 1495 — check with
   `wc -w` after ANY edit), attach PUBLIC repo (flip visibility before deadline!) + demo.
   ONE writeup per team, must click Submit (drafts don't count).
5. Don't reuse krish4uu/threeJs-monsters-world — no license + trademarked characters.

## Hackathon requirements (from the brief)
- Kaggle Writeup (max 1500 words) with track selected; attach public code repo + live
  demo (hosted URL, terminal recording, or fully functional Kaggle notebook)
- Judging: Gemma Integration 30% (is the model core?), Innovation & Impact 30%,
  Functionality 20% (does it actually work?), Presentation & Writeup 20%
- Edge track wants: Gemma core, local/minimal cloud, useful UX, creativity + impact
- Our Gemma-core argument: 11 call sites (direction, study guides, mastery lessons, reasoning
  grading, answering the student, approach choice, generated check questions, printable practice,
  relics/greetings, skirmish coaching, parent reports) — all guardrailed; the model is never the
  source of math truth. Tables in README and docs/ARCHITECTURE.md.

## Models on this machine
- ollama: gemma3:1b (fast, text-only), gemma3:12b (main — quality, 0.8s/call after load)
- Switch via env var GEMMA_MODEL (default 1b; run the demo on 12b)

## Working agreements
- No emojis anywhere in the product.
- Vocabulary rule: the wrong idea that feels right is always a "trick" — never a clinical
  synonym, and never a word that says the student is muddled. The loop stage is CHECK
  (TEACH → CHECK → EVALUATE → ADAPT) and a single item the agent poses is a "check question".
  A student's weak spot is "the trick that caught them". Reports address mum and dad, never
  teachers. README is game-voice; docs/ARCHITECTURE.md is the professional judge doc.
- Judge-facing material describes the product as it stands — never what changed.
- One feature at a time, discussed before building. Verify in browser before pushing.
- Commit style: descriptive, with Co-Authored-By: Claude line. Push after each verified change.

## Implementation notes worth remembering
- Streamlit sandboxes component iframes without ancestor-navigation, so in-scene links use
  target="_top" with a URL rebuilt at click time from window.parent / document.referrer.
- three.js is vendored and INLINED into each srcdoc iframe: Streamlit serves .js as text/plain
  and Chrome refuses to execute it from a <script src>.
- Audio is fetched as a blob for the same content-type reason, and autoplay needs a gesture, so
  every theme starts on the first pointer/key interaction.
- Monster placement is self-fitting: measure the Box3, normalise on max(sz.y, 0.62*max(sz.x,sz.z))
  so squat and winged models come out alike; per-monster `lift` nudges rest poses that splay.
- Animation clips are read by exact name from the GLBs (clip_ambient/clip_fight + speeds in
  MONSTERS): calm idle everywhere, aggression only in the fight minigame.
