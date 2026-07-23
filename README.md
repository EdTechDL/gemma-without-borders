# GEMMA MONSTERS

*An on-device math adventure powered by Gemma — built for the GDG Windsor Build with AI hackathon, Edge/On-Device track.*

## The story

Deep in the Nexus live five monsters. They are here to make you forget your math — each one plants a trick in your head, a wrong idea that feels right, which is exactly why it works. You cannot beat a monster by luck. You beat it by proving its trick doesn't fool you anymore: two fresh questions in a row, with reasoning that holds up.

## The monsters

| Monster | Unit | Its trick |
|---|---|---|
| **Fractis** | Number | Whispers "just add fractions straight across." Tops with tops, bottoms with bottoms. Feels tidy. Totally wrong. It fears a common denominator. |
| **Equazor** | Algebra | Twists your equations so signs flip the wrong way when you move things across the equals sign. Hates when you balance both sides. |
| **Statiq** | Data | Blurs mean and median into one fuzzy word so you grab the wrong one. Falls apart the moment you put the data in order. |
| **Polygor** | Geometry & Measurement | Hoards angles and hands you stolen area formulas that almost fit. One honest diagram and it crumbles. |
| **Ledgerling** | Financial Literacy | Skims your interest while you sleep and hopes you never check the math. A sharp budget cuts it down. |

## How to play

1. From the intro page, hit **Play GEMMA Monsters** to enter the Nexus.
2. Click a monster. Read its card. Press **Begin challenge** to face its quiz.
3. Miss questions and the monster **gets you** — its trick was in your head all along.
4. Now the agent steps in. It teaches you, checks if the lesson landed, and switches to a different teaching style when one doesn't work — until you defeat the monster.
5. Defeat = two fresh questions right in a row, with reasoning that holds up. No fluke wins.

Not in the mood for monsters? Classic mode (no game, same brain) is still right there on the intro page.

## What GEMMA does behind the curtain

Gemma runs locally on your machine and does the actual thinking, one job per line:

| Job | What Gemma does |
|---|---|
| Rescue lessons | Writes the lesson that pulls you out after a monster gets you. |
| Reasoning check | Reads HOW you got your answer — a right answer with wobbly reasoning does not count. |
| Next move | Picks its next teaching move and tells you why. |
| Fresh questions | Forges brand-new questions, then secretly re-solves them to check its own answer key. |
| Hints | Gives hints that nudge but never spoil. |
| Photo vision | Reads a photo of your paper work, right on your device. |
| Teacher note | Writes your teacher a note they can actually use. |

One plain fact: the math answers always come from a bank of verified questions, never from the model guessing.

Engineers and judges: the serious version of all this lives in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional, for the live brain: install [Ollama](https://ollama.com) and pull a model —

```bash
ollama pull gemma3:1b     # small and fast
ollama pull gemma3:12b    # bigger brain, plus photo vision
```

Without Ollama the app still runs, just with placeholder text instead of Gemma. Switch models any time with the `GEMMA_MODEL` environment variable:

```bash
GEMMA_MODEL=gemma3:12b streamlit run app.py
```

## Credits

- Built with Google's Gemma, running locally via Ollama.
- "Ninja by BRUNO 365 (Sketchfab), CC Attribution" — reserved for the upcoming player character.

---
*Built for the GDG Windsor · Build with AI — Gemma Hackathon. Edge / On-Device track.*
