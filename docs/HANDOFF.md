# GEMMA WITHOUT BORDERS — Full Project Handoff
Last updated: July 24, 2026. Written so any Claude session (or teammate) can pick up instantly.

## What we are building
An autonomous AI study agent for the Grade 9 EQAO math assessment (Ontario MTH1W curriculum),
built for the GDG Windsor "Build with AI — Gemma Hackathon" on Kaggle.
Track: EDGE / ON-DEVICE (a personal study assistant; Gemma runs locally — privacy story).
Team: Gokulakrishnan (frontend), Padmanabha (data/architecture), Taha (backend Python),
Naimah (testing/validation/writing), Amarah (coordination, integration, GitHub, this machine).

Core flow: student takes a short quiz → agent diagnoses WHICH trick caused each
wrong answer (ground-truth lookup from a verified tagged question bank — never model
guessing) → Gemma writes a personalized study guide (explanation grounded in the verified
solution + fresh practice + hints) → "Practice until mastery": an autonomous loop that
teaches, probes with fresh questions, grades typed reasoning, SWITCHES teaching strategy
when one fails (Gemma picks the next one and says why), and stops at mastery (2 fresh
correct in a row with sound reasoning) or hands off to a teacher with an actionable
Gemma-written report. Every agent decision shows an evidence-based "why" (explainable AI).

Game layer (in progress): "GEMMA MONSTERS" — each unit is guarded by a monster that
personifies the trick (Fractis/Number, Equazor/Algebra, Statiq/Data,
Polygor/Geometry, Ledgerling/Financial). 3D three.js nexus hub with bloom, click a
monster → game card → its unit's real quiz. Tricks are announced as
"A Gemma Monster got you!" with the monster shown big, then tiny next to each question.
The game is ADDITIVE — behind a "Play GEMMA Monsters (beta)" button on the intro; the
professional app is untouched without it.

## Where everything is
- Repo (private): https://github.com/EdTechDL/gemma-without-borders  (gh CLI is logged in as EdTechDL on this Mac)
- Local checkout: /Users/amarah/gemma-without-borders
- This handoff also lives in the repo: docs/HANDOFF.md (keep both updated)
- Slide deck (Beamer): docs/slides/gwb-demo.tex + PDF (also /Users/amarah/remotion/GWB-Hackathon-Demo-Slides.pdf)
- Older working docs (brainstorm, test kits, Kaggle guides): /Users/amarah/remotion/
- Kaggle fallback demo notebook: gemma-tutor-CLEAN.ipynb in /Users/amarah/remotion/ (imported on Kaggle; teammate also has a Gradio version with 12B)

## File map (repo root)
- app.py           — Streamlit UI: intro / quiz / results / mastery / map (game hub) stages + router
- agent.py         — grade_quiz, analyze (priority trick, escalation), build_study_guides, Gemma teacher_report
- mastery.py       — the autonomous loop: MasterySession, teach, next_probe (bank-first), submit_answer (deterministic grading + Gemma reasoning-grader RESOLVED/SHALLOW/SAME_ERROR + Gemma strategy choice + hard caps), rationale (explainable AI), escalation_report
- tutor.py         — study_guide cards: grounded explanation, bank-first practice picker, hint ladder
- gemma_client.py  — THE ONE DOOR to the model: ask_gemma (Ollama HTTP), plainify (LaTeX stripper), transcribe_image (12B vision, on-device photo of written work), format_teacher_report, availability checks, stub fallback
- data/questions.json — 36 verified EQAO-style questions, every wrong option tagged with its trick (this is the ground truth; multi-agent verified twice)
- .streamlit/config.toml — theme + runOnSave=true
- docs/            — slides, notebook walkthrough, HANDOFF.md

## How to run it (this Mac)
```bash
cd /Users/amarah/gemma-without-borders
GEMMA_MODEL=gemma3:12b ./.venv/bin/streamlit run app.py --server.headless true --server.port 8501
```
- Ollama must be running (it autostarts; `ollama list` shows gemma3:1b and gemma3:12b installed).
- No model? App still runs with placeholder text (stub fallback).
- Vision (photo of handwritten work) needs the 12B (1b is text-only).
- If port 8501 is stuck: `lsof -ti :8501 | xargs kill -9` then relaunch (KEEP 8501 — the team's tunnel URL points at it).

## Team access (tunnel)
Amarah runs a Cloudflare quick tunnel pointing at localhost:8501:
```bash
cloudflared tunnel --url http://localhost:8501
```
It prints an https://….trycloudflare.com URL — share in team chat. Dies when the process
stops; just rerun and share the new URL. runOnSave=true means file edits hot-reload for
viewers; restarts keep the same URL as long as port 8501 is reused.
Teammates can also clone + run locally (README has steps; 1B model is an 815MB pull).

## Current state (what is DONE and verified)
- Quiz → results → study guide → mastery loop: all working live on gemma3:12b (0.8s/call)
- Diagnosis = table lookup on tagged options (100% deterministic); answer keys from bank
- Explanations/hints grounded in verified solutions (model may not invent numbers — we
  caught the 1B inventing wrong math and architected around it; good writeup material)
- Reasoning grader: right answer + shaky typed reasoning does NOT count toward mastery
  (works on 12B; under-detects on 1B — documented finding)
- Strategy ladder: Direct correction → Visual walkthrough → Side-by-side contrast →
  Real-world analogy; Gemma chooses the next rung from the student's own words + why
- Hard caps: 4 attempts, 12 Gemma calls, strategy exhaustion → teacher hand-off. Cannot loop forever.
- Explainable AI: every decision (priority choice, count/not-count, strategy switch,
  mastery, hand-off) shows an evidence-based reason
- Teacher reports (both paths): Gemma-written narrative + 3 concrete "Try in class"
  interventions, informed by which tutoring strategies already failed; clean wrapping
  layout + Download button (preamble stripped, inline numbering split into bullets)
- Vision: upload/photo of handwritten work → 12B transcribes on-device (transcribe-only,
  bank judges correctness); "What Gemma read from your photo" shown; live-tested at 3.1s
- Display polish: stacked KaTeX fractions everywhere; $ currency escaped (Financial
  Literacy bug fixed); LaTeX stripped from all model output (plainify); no emojis;
  serif/ivory/clay professional design
- Fresh-practice guarantee: "Now you try" never repeats a question the student saw;
  solution hidden until they attempt it
- Game: 3D GEMMA Monsters hub written into app.py (_HUB_TEMPLATE) — nexus, 5 monsters
  with eyes, bloom, auto-orbit, game-card panel, ?station= routing, ?exit=1, monster-got-you
  banner + tiny monster badges on results (adventure mode only). JUST restarted —
  NOT YET VERIFIED IN BROWSER at time of writing. Verify: intro → "Play GEMMA Monsters".
- All committed & pushed through commit "monster-got-you flow" (check `git log`).

## Known TODO / next steps
1. VERIFY the monsters hub renders + full loop (portal → quiz → results shows monster banner)
2. Main character: user is downloading a free CC-BY "Ninja" model (by BRUNO 365,
   Sketchfab) — GLB format is the right one. Put it at repo public path, load with
   GLTFLoader, credit "Ninja by BRUNO 365 (CC-BY)" in README. Candidate: walkable
   character in hub instead of pure orbit camera.
3. three.js loads from CDN — contradicts airplane-mode story; consider vendoring
   three.min.js into repo for the demo (honesty: game layer needs the file local).
4. Team feature list (one at a time, discussed): next candidate = #1 adaptive difficulty
   (easier/harder question selection in mastery loop using bank difficulty tags).
5. Demo recording (90s script is slide 10 of the deck) — record once stable.
6. Kaggle submission: writeup <1500 words (use README "Where Gemma does the thinking"
   table + blueprint doc sentences), attach PUBLIC repo (flip visibility before deadline!)
   + demo. ONE writeup per team, must click Submit (drafts don't count).
7. Don't reuse krish4uu/threeJs-monsters-world — no license + trademarked characters.

## Hackathon requirements (from the brief)
- Kaggle Writeup (max 1500 words) with track selected; attach public code repo + live
  demo (hosted URL, terminal recording, or fully functional Kaggle notebook)
- Judging: Gemma Integration 30% (is the model core?), Innovation & Impact 30%,
  Functionality 20% (does it actually work?), Presentation & Writeup 20%
- Edge track wants: Gemma core, local/minimal cloud, useful UX, creativity + impact
- Our Gemma-core argument: 8 call sites (lessons, explanations, reasoning grading,
  strategy choice, question generation w/ self-audit, hints, teacher reports, vision
  transcription) — all guardrailed; model never the source of math truth. README table.

## Models on this machine
- ollama: gemma3:1b (fast, text-only), gemma3:12b (main — quality + vision, 0.8s/call after load)
- Switch via env var GEMMA_MODEL / GEMMA_VISION_MODEL (defaults: 1b text, 12b vision)

## Working agreements
- No emojis anywhere in the product. Professional serif/ivory/clay design in the app;
  the game world is exempt (dark, warm-tinted neon).
- One feature at a time, discussed before building. Verify in browser before pushing.
- Commit style: descriptive, with Co-Authored-By: Claude line. Push after each verified change.


## Addendum (July 24, late)
- GEMMA MONSTERS is fully wired: nexus hub (bloom, slow orbit, whole-platform click
  targets) -> game card -> challenge. IMPORTANT: Streamlit sandboxes component iframes
  without ancestor-navigation, so the in-card Begin button opens a NEW TAB (allowed),
  and the reliable single-tab path is the five PORTAL KEY buttons under the canvas.
- Adventure mode has a full dark game skin (looks only); quiz page = "Face <Monster>",
  results = "The Battle Report", practice = "TRAINING GROUNDS". Classic mode unchanged.
- Vocabulary rule (user): never the words "trick" or "confusion" anywhere
  student-facing or in README - monsters "make you forget your math", each has a
  "trick"; README is game-voice; docs/ARCHITECTURE.md is the professional judge doc.
- Team tunnel: cloudflared quick tunnel on :8501 (URL in /tmp/gwb_tunnel.log).

## Addendum - July 24 (late-3)
- THE COLLECTOR boss arena (stage "boss", debug entry ?boss=1): giant Quaternius CC0
  skull (static/monsters/skull.glb) in a cold blue-violet arena, entrance animation,
  Flying_Idle loop with Headbutt attack + screen shake on miss. Speed trial: 10
  client-side quick-fire questions (times tables 2-12, add/subtract), 8s timer bar,
  3 life pips, taunts on hit/miss (missed answer revealed), win/lose end cards.
  Deterministic JS math - no model in the loop. Reached from the training grounds
  when attempts run out (adventure mode): "THE AIR GOES COLD" note + challenge
  button; teacher hand-off unchanged beneath it. Each monster's encounter now ends
  with a whispered warning about him (foreshadowing).
- Curated animation system: exact clip names read from the GLBs; per-monster
  clip_ambient/clip_fight + speeds in MONSTERS; calm idle everywhere, aggression
  only in the fight minigame. Statiq no longer flops frantically.
- Nexus designer pass: vignette + color grade, denser fog, layered beveled
  platforms at varied heights with slow bobbing, colored rim light behind each
  monster, floating debris field, nebula dome + beacons (subtle), dimmer core.
