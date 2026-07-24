# GEMMA MONSTERS

*An on-device math adventure powered by Gemma — built for the GDG Windsor Build with AI hackathon, Edge/On-Device track.*

## Screenshots

<!-- drop the four PNGs into docs/screens/ to light these up -->

![The Citadel — five monsters guard their strands beneath the sealed golden gate](docs/screens/citadel.png)
*The Citadel: drag to orbit the castle; five monsters wait on their floating platforms.*

![A full-screen encounter — the monster addresses you by name and remembers your last battle](docs/screens/encounter.png)
*An encounter: the monster calls you by name, and Gemma writes what it remembers about you.*

![The battle report — exactly which tricks got you, with a Gemma-grounded study guide](docs/screens/battle-report.png)
*The battle report: what got you, why it felt right, and the study guide that fixes it.*

![The Collector — a giant skull boss running a mental-math speed trial](docs/screens/collector.png)
*The Collector: three lives, a speed trial, and no patience for slow arithmetic.*

## The story

The Citadel is locked from the outside. Someone is trapped in the keep behind a golden gate, and five monsters hold the seal — each one perched on a floating platform, guarding one strand of Grade 9 math. Every monster plants a trick in your head: a wrong idea that feels right, which is exactly why it works. You cannot beat a monster by luck. You beat it by proving its trick doesn't fool you anymore: two fresh questions in a row, with reasoning that holds up.

Defeat all five and the seal breaks, the gate opens, and the rescue is yours. Fail too often, though, and the monsters' boss takes an interest. They call him the Collector. They do not joke about him.

## Your first minute

A new challenger opens on a short introduction, in the same 3D world as the game: the title, the five monsters standing in a row with the strand each one guards, how a battle is actually won, the Collector arriving in colder light, and the promise that all of it runs on this laptop. Five beats, its own theme, a **Skip intro** button in the corner, and it never shows twice in a sitting.

## The monsters

| Monster | Strand | Its trick |
|---|---|---|
| **Fractis** | Number | Whispers "just add fractions straight across." Tops with tops, bottoms with bottoms. Feels tidy. Totally wrong. It fears a common denominator. |
| **Equazor** | Algebra | Twists your equations so signs flip the wrong way when you move things across the equals sign. Hates when you balance both sides. |
| **Statiq** | Data | Blurs mean and median into one fuzzy word so you grab the wrong one. Falls apart the moment you put the data in order. |
| **Polygor** | Geometry & Measurement | Hoards angles and hands you stolen area formulas that almost fit. One honest diagram and it crumbles. |
| **Ledgerling** | Financial Literacy | Skims your interest while you sleep and hopes you never check the math. A sharp budget cuts it down. |

And above them all: **THE COLLECTOR**, a giant skull who runs mental-math speed trials — three lives, incoming attacks — with three lieutenants softening you up in the training grounds: **Twinfang** (doubles), **The Niner** (nines), and **Splitjaw** (make-a-ten).

## How to play

1. Watch the introduction, or skip it. Then enter your hero name — the monsters will use it, and they will remember you.
2. Enter the Citadel. Drag to orbit the castle, then click a monster on its platform. **Sound: on** in the header turns the music and the battle audio off and on; every arena honours it.
3. The encounter takes over the screen. The monster taunts you by name; come back after a loss and it gloats about last time.
4. Face its quiz. The battle report shows exactly which tricks got you, then a Gemma-grounded study guide explains each one — with real fraction and exponent notation, never recomputed math.
5. Now the agent steps in: it teaches, then puts a fresh check question to you and reads both your answer and your typed reasoning. Say how you got there and the citadel answers you back, in its own voice, naming the idea you got right or the one that slipped. A right answer with wobbly reasoning does not count. When a lesson doesn't land, Gemma switches teaching strategies and tells you why.
6. Master the trick and Gemma forges you a relic — a trophy written from your actual battle. Struggle too long and the Collector is summoned instead, along with a Gemma-written note for mum and dad.
7. Gemma also decides where you go next: after a battle it names the monster worth hunting and says what in your run made that the answer, and outside the Collector's arena it picks which lieutenant to drill.
8. Between battles, hit the training grounds: 90-second war-clock skirmishes against the lieutenants, with streaks that raise the stakes. Gemma whispers each lane's mental strategy before the fight, and afterward **GET COACHED BY GEMMA** names your miss pattern, teaches the fix, and sets a three-question drill.
9. Defeat all five monsters to break the seal on the golden gate and free whoever is locked in the keep.

Not in the mood for monsters? Simple mode (no game, same brain) is one click away.

## For mum and dad

There is a **For mum and dad** button pinned to every screen. It opens the letters home: every note the agent has written about your child, newest first.

- A note goes home after **any** battle where something was missed — not just the bad days — so the pattern and the progress are both visible.
- Beating a trick is a letter too. Good news gets sent, with the evidence the agent used to call it mastery.
- The notes are kept on this machine (`data/letters/`), so closing the tab does not lose them. They also download as one file.
- Each trick on the page offers **Make a practice sheet**: ten questions on that one trick, printable, with space to work and an answer key on its own page. Verified bank questions go on first; if Gemma writes any extras, it has to solve each one again — blind, without seeing the key it just wrote — and agree with itself before it reaches the paper.

## What GEMMA does behind the curtain

Gemma runs locally on your machine and does the actual thinking, one job per line:

| Job | What Gemma does |
|---|---|
| Rescue lessons | Writes the lesson that pulls you out after a monster gets you. |
| Reasoning check | Reads HOW you got your answer — a right answer with wobbly reasoning does not count. |
| Answering you back | Replies to your typed reasoning in the citadel's voice, naming what you actually said. |
| Next move | Picks its next teaching move and tells you why. |
| Where you go next | Chooses the monster to hunt or the lieutenant to drill, and names the evidence. |
| Fresh questions | Forges brand-new questions, then secretly re-solves them to check its own answer key. |
| Printable practice | Fills out a parent's practice sheet when the bank runs short — under the same blind audit. |
| Battle memory | Writes each monster's opening line from what it remembers about you. |
| Relic forging | Names and inscribes the relic you earn from the trick you beat. |
| Skirmish coaching | Reads your misses and hesitations, names the pattern, and sets your drill. |
| Strategy whispers | Teaches you each lieutenant's lane — doubles, nines, make-a-ten — before the fight. |
| Note for mum and dad | Writes your parents a note they can actually use at the kitchen table. |

One plain fact: the math answers always come from a bank of 55 verified questions — every one inside what the EQAO Grade 9 assessment covers and mapped to a published MTH1W expectation, with the answer key spread evenly across A to D so it cannot be gamed, and every wrong option tagged with the trick it reveals. Where a question explains its traps, those notes are keyed to the answer's text rather than its letter, so they stay true however the options are ordered. Never from the model guessing.

Engineers and judges: the serious version of all this lives in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional, for the live brain: install [Ollama](https://ollama.com) and pull a model —

```bash
ollama pull gemma3:1b     # small and fast
ollama pull gemma3:12b    # bigger brain
```

Without Ollama the app still runs, just with placeholder text instead of Gemma. Switch models any time with the `GEMMA_MODEL` environment variable:

```bash
GEMMA_MODEL=gemma3:12b streamlit run app.py
```

## Credits

- Built with Google's Gemma, running locally via Ollama.
- Monster models (Alien, Demon, Dragon Evolved, Fish, Frog) and the Collector's skull by Quaternius (quaternius.com), CC0 public domain — thank you Quaternius.
- three.js and its loaders are vendored into `static/vendor`.
- The citadel, introduction and Collector themes were generated with ElevenLabs by the team and ship in `static/audio`; battle stingers are procedural WebAudio. Nothing is fetched from the internet at runtime.

---
*Built for the GDG Windsor · Build with AI — Gemma Hackathon. Edge / On-Device track.*
