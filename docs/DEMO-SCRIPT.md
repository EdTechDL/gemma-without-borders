# Gemma Monsters — screen recording script

A shot-by-shot script for a screen recording. Roughly **2 minutes 45 seconds** at a
comfortable pace. Cut marks are noted if you need to land under 90 seconds.

Read the **Before you record** section first. Two of those steps will save you a retake.

---

## Before you record

**Launch it fresh, with the big model.**

```bash
cd ~/gemma-without-borders
pkill -9 -f "streamlit run app.py"; sleep 2
GEMMA_MODEL=gemma4:12b GEMMA_TIMEOUT_S=300 ./.venv/bin/streamlit run app.py --server.headless true --server.port 8501
```

Then open `http://localhost:8501` in a **fresh browser window**, not a tab in your
working window. Hide bookmarks. Zoom to 100%.

**Warm the model up.** Before recording, play one battle end to end and enter the
training loop once. The first call after a cold start is the slowest one you will ever
see, and you do not want it on camera.

**Start from a clean session.** Reload the page so you land on the introduction with no
name saved and no letters waiting.

**Decide the vocabulary question below.** It is the only thing that can make you
contradict your own screen.

**Have the Wi-Fi menu reachable.** The last shot turns it off on camera.

---

## One decision before you record

The written brief calls a named wrong answer a **snare**. The app on screen still says
**trick** in a few places — the mastery screen title, and the line naming what caught the
student most.

Pick one, because a judge reading the brief and watching the video will notice:

- **Option A — record now.** Say *"the wrong idea that caught you"* out loud and never say
  either word. The script below is written this way, so it is safe either way.
- **Option B — rename first**, then say *snare* freely and match the brief exactly.

Option A costs nothing and is what the script assumes.

---

## The script

Timings are cumulative. `[DO]` is what you click. `[SAY]` is what you say over it.

---

### 1 · Open on the problem — 0:00 to 0:15

`[DO]` Start on the introduction screen, beat 1. Do not click yet.

`[SAY]`
> "Ask a Grade 9 student for two thirds plus one quarter, and a lot of them will tell you
> three sevenths. Tops with tops, bottoms with bottoms. That student isn't being careless
> — they're applying a rule that feels completely right. Marking it wrong teaches them
> nothing, because they already believed it."

---

### 2 · What the game is — 0:15 to 0:35

`[DO]` Type your name in the field. Press Enter. Wait for **Welcome, <name>** to appear.
Click **NEXT** twice, pausing on the roster of five monsters.

`[SAY]`
> "So we built the wrong ideas into monsters. Five of them, one for each strand of the
> Ontario Grade 9 curriculum, and each one has a favourite way of tripping you up. You
> beat a monster by proving its trap doesn't work on you any more."

`[DO]` Click **NEXT** twice more to reach the Collector beat, then **ENTER THE CITADEL**.

`[SAY]` *(over the Collector beat)*
> "And this one turns up when a student keeps slipping."

---

### 3 · Into a battle — 0:35 to 0:50

`[DO]` The citadel loads. Click one monster — **Equazor (Algebra)** is a good choice.
Its card opens. Click **Begin challenge**, then **FACE EQUAZOR**.

`[SAY]`
> "Everything you're about to see is running on this laptop. Streamlit, three.js, and
> Gemma through Ollama on localhost. No account, no server, nothing leaving the machine."

---

### 4 · Answer wrong on purpose — 0:50 to 1:10

`[DO]` On **question 1** (`Simplify 3(2x - 4) - 5x`), choose **A) 11x - 12**.
Answer the rest however you like, but get at least two wrong. Click **SUBMIT**.

`[SAY]`
> "I'm going to get this wrong the way a real student does — distribute the 3, then forget
> the 5x. Watch what the app does with that, because this is the part that matters."

`[DO]` Wait for the battle report. It scrolls to the top by itself.

---

### 5 · The wrong answer names the wrong idea — 1:10 to 1:35

`[DO]` Point at the banner naming what caught you, then scroll slowly to the first study
guide card. Open **See the worked solution**.

`[SAY]`
> "It didn't just mark it wrong. Every wrong option in our question bank carries the exact
> faulty thinking that produces it, written when the question was written. So naming what
> went wrong is a table lookup — no model call, no guessing. Gemma's job starts *after*
> that: it explains why my method fails, and the verified worked solution is already in
> the prompt, so it never does the arithmetic itself."

`[CUT IF SHORT ON TIME]` — skip the worked solution expander.

---

### 6 · The training loop — 1:35 to 2:15 *(the most important 40 seconds)*

`[DO]` Click **Defeat the monster — practice to mastery**. Wait for the lesson.

`[SAY]`
> "Now it teaches. And this is the part I'd point at: it doesn't just ask another
> question — it asks me to say *how* I got my answer."

`[DO]` Answer the check question **correctly**, and type something deliberately thin in the
reasoning box — *"I just did it in my head"*. Click **Check my answer**.

`[SAY]` *(as the verdict appears)*
> "Right answer. But look — it doesn't count. Gemma read what I typed, judged the
> reasoning as thin, and the streak doesn't move. You can't luck your way through this;
> two in a row, with reasoning that holds up."

`[DO]` Answer the next one **wrong**. Wait for the new lesson.

`[SAY]`
> "And when I miss it, it doesn't repeat itself louder. Gemma reads my own words, picks a
> genuinely different teaching approach from a fixed set of four, and tells me why it's
> switching."

---

### 7 · The parent side — 2:15 to 2:35

`[DO]` Click the round mark at the bottom-left, then **Make a practice sheet** on any
trick listed. While it builds, keep talking. Open the downloaded sheet if it finishes.

`[SAY]`
> "Everything the agent learns goes home in plain language — what happened tonight, and
> three things to try at the kitchen table. And a parent can print a worksheet on exactly
> the thing their kid is stuck on. Verified questions go on first. Anything Gemma writes
> has to solve its own question again, blind, without seeing the answer it just wrote —
> and if it disagrees with itself, that question never reaches the paper."

`[CUT IF SHORT ON TIME]` — skip the worksheet, just show the letters page.

---

### 8 · Close with the Wi-Fi — 2:35 to 2:45

`[DO]` Open the Wi-Fi menu **on camera** and switch Wi-Fi **off**. Go back and click a
monster, or answer one more question, so something clearly still works.

`[SAY]`
> "One last thing. Wi-Fi off — and it keeps going. A fourteen-year-old's mistakes never
> leave the house, and this runs on the hardware a family already owns."

---

## If something is slow on camera

Model calls take a few seconds. Don't apologise for the pause — fill it:

> "That's the model thinking on-device, no cloud round-trip."

If a lesson comes back as clearly-marked placeholder text, the timeout was hit. Say
nothing, stop recording, restart with `GEMMA_TIMEOUT_S=300`, and pick up from that shot.

---

## What each shot is quietly doing for you

Never say any of this out loud. It is why the shots are ordered this way.

| Shot | What it demonstrates |
|---|---|
| 4 → 5 | Gemma is doing judgement work, not decoration, and the app is built so it can't invent the maths |
| 6 | The reasoning gate and the fixed strategy ladder — the thing nobody else will have |
| 5, 7 | Guardrails that exist because the model failed in testing, not in theory |
| 3, 8 | It genuinely runs, offline, on one machine |
| 1 | A real, local, specific problem rather than a generic demo |

---

## Cut-down 90-second version

Shots **1, 4, 5, 6, 8**. Drop the introduction walkthrough, the parent side and the
worksheet. Shot 6 keeps its full 40 seconds — it is the one that wins the argument.
