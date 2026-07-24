# Kaggle submission — field by field

Paste each block into the matching field. Two links still need filling in by hand;
they are marked **[YOU FILL IN]**.

One decision before you paste: the model line says **Gemma 4 (`gemma4:12b`)**. Only
paste that if a teammate has confirmed it actually runs. If not, change it to
**Gemma 3 (`gemma3:12b`)** — the paragraph reads correctly either way, and it is far
better to name the model you actually ran than to be caught by a judge who runs it.

---

## Inspiration — what local problem are you solving today?

Every Grade 9 student in Ontario sits EQAO, the province's mathematics assessment.
Around Windsor–Essex it is a date the whole household knows. The help on offer is a
tutor at sixty dollars an hour, or a practice app that puts a red X next to a wrong
answer and moves on.

The red X is the problem. A wrong answer in maths is almost never random. Ask a
fourteen-year-old for 2/3 + 1/4 and watch for 3/7 — tops with tops, bottoms with
bottoms. Tidy, symmetric, and wrong. Marking it wrong teaches nothing, because the
student who wrote 3/7 already believed 3/7. That is not carelessness; it is a rule,
applied faithfully. It is just the wrong rule.

We built **Gemma Monsters**: an EQAO tutor wrapped in a monster game that names the
specific wrong idea behind a wrong answer, teaches until that idea stops working, and
writes home to a parent — all on one laptop, with nothing leaving the machine. Five
monsters guard the five strands EQAO assesses. Each one embodies a way of being wrong
(adding fractions straight across, a sign that slips crossing the equals sign, mean
and median blurred together). You beat a monster by proving its trap no longer fools
you. We chose on-device deliberately: a family already owns the hardware, it works
where home internet is unreliable, and a fourteen-year-old's worked-out mistakes never
leave the house.

---

## How we built it

**Which Gemma model.** Gemma 4 (`gemma4:12b`), served locally through Ollama. The
model name lives in a single environment variable, so the whole app moves to a larger
or smaller Gemma with nothing else to edit — we developed against two sizes, because
what the smaller one gets wrong is exactly what told us where the guardrails had to go.

**RAG, prompt engineering, or fine-tuning?** No fine-tuning and no vector RAG.
Retrieval is a deterministic tag lookup against a verified question bank of 55 items —
which beats similarity search when the payload is an answer key, because the key has to
be exactly right, not merely close. Everything else is prompt engineering wrapped in
code that refuses bad replies.

**Frameworks.** Python and Streamlit for the agent and the game shell; three.js
(vendored, no CDN) for the 3D citadel and battles; Ollama for on-device inference. No
account, no external request, no telemetry — the app opens and runs with the Wi-Fi off.

**How Gemma is actually used.** Every model call passes through one function, and it is
used at ten points where the app needs judgement rather than fact: it writes each
lesson, explains why a wrong method felt right, judges whether the student's typed
reasoning genuinely holds up, chooses which of four fixed teaching approaches to try
next, decides which monster to face next, writes fresh questions when the bank runs
dry, and writes the note that goes home. The design rule underneath all of it: **code
owns what is true — every answer key, every figure, the caps — and Gemma owns what is
judged.** Nothing crosses that line. A mastery loop runs TEACH → CHECK → EVALUATE →
ADAPT against a fixed four-rung strategy ladder, with hard caps (two-in-a-row to win,
four attempts, twelve model calls) so it always terminates.

---

## The Prototype

- **2-minute demo video:** **[YOU FILL IN — link here]**
- **GitHub repository:** https://github.com/EdTechDL/gemma-without-borders
- **Kaggle notebook:** **[YOU FILL IN — link here]**

Run it locally with Ollama and `streamlit run app.py`. With the Wi-Fi off, the full
game still plays: the introduction, five monster battles, the mastery loop, the
Collector's timed trial and his three lieutenants, letters home, and printable practice
sheets.

---

## Challenges we ran into

The hardest part was not making the model talk — it was stopping it from being trusted
where it should not be. A small local model is a capable judge and an unreliable
authority, and almost every design decision came from watching it fail:

- **It invented arithmetic** inside its own explanations — redoing sums it had already
  been given and landing somewhere new, in confident prose next to a correct answer. Fix:
  the verified worked solution now rides inside every prompt, and the model may state no
  other number. It explains *why* a method fails; it never recomputes.
- **It marked its own generated question with the wrong answer.** A student would have
  been told they were wrong for being right. Fix: any question Gemma writes must solve
  itself again *blind* — without seeing the key it just wrote — and the two answers must
  match, or the question is destroyed and never shown.
- **It answered in Spanish**, unprompted, on open generation calls. Fix: those prompts
  now say English explicitly.
- **It fabricated a count** — "beaten three tricks" when one had been beaten, borrowing a
  real number that belonged to a different row on the same page. Fix: on the page that
  goes to a parent, code prints every figure and the model prints none; any reply
  containing a number is thrown away.

Doing all of this on one laptop, offline, in a day, meant every one of these had to be a
structural guard rather than a polite instruction — which is what turned a chatbot on top
of a quiz into an agent you can actually trust with a fourteen-year-old.

---

## Notes for whoever submits

- **Word budgets:** if a field is tight, the Inspiration and Challenges sections cut most
  cleanly — drop the last bullet of Challenges before touching How we built it, which
  carries the "did they effectively utilise Gemma" answer.
- **The two links** are the only blanks. The GitHub URL is real and live.
- **Honesty line to keep ready** in case a judge asks: no student has used it yet, and
  nothing in it measures whether the learning sticks — the next step is a small pilot with
  real Grade 9 students. Volunteering this lands better than being caught by it.
