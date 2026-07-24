# GEMMA MONSTERS - deck script

16 slides. Slide-by-slide: what is said, what is on screen, and why the slide is in the
deck.

## Why this shape

The backbone is draft 3, because a small model being a good judge and an unreliable
authority is a claim we watched come true in testing, and every structure in the project
follows from it, which gives the deck one argument to make instead of a tour to give.
From draft 2 we took the single traced run, so the evidence slides carry real questions,
real wrong answers and real strings from the app rather than descriptions of a format.
From draft 1 we took the teaching ladder drawn as a ladder, the mastery bar drawn as a
strip of check slots, and the habit of putting the rejection path on every diagram rather
than only the happy path. We cut the six-decision map slide, which was a table of contents
for an argument the audience is already following, and we cut the closing failure recap,
because each of the four failures now sits on the slide it produced.

House vocabulary: the named wrong idea is a snare. A monster sets a snare, a student gets
snared, a snare is beaten.

---

## Slide 1 - Gemma Monsters runs a Grade 9 maths tutor on one offline laptop

**Says:**
GEMMA MONSTERS

An autonomous Grade 9 EQAO mathematics tutor, wrapped in a three.js monster game.

Kaggle "Build with AI - Gemma Hackathon", GDG Windsor. Track: Edge / On-Device.
Gokulakrishnan, Padmanabha, Taha, Naimah, Amarah.

Everything runs on one machine. Streamlit serves the app, three.js and GSAP are vendored
and served from the same process, and Gemma answers through Ollama on localhost:11434.
The monster models are CC0 Quaternius assets, the audio is ours. No CDN, no account, no
sign-in, no telemetry, and nothing leaves the device. If Ollama is not running at all,
the app still opens and every screen still works, with clearly marked placeholder text
where the model's words would be.

Five monsters guard a citadel, one for each Ontario MTH1W strand. Fractis holds Number,
Equazor holds Algebra, Statiq holds Data, Polygor holds Geometry and Measurement,
Ledgerling holds Financial Literacy. Each one is out to make you slip in its own
particular way, and you beat it by proving that the way it catches people no longer works
on you.

**Shows:** The citadel hub as it actually renders, the orbitable nexus with the five
monster models lit against the dark, title lock-up bottom left. Along the bottom, a
five-cell strip pairing each monster name with its strand and its colour. Top right, a
small plain box listing the running parts: Streamlit, three.js (vendored), Ollama on
localhost:11434, gemma3. The track and team line sits as small text along the bottom
edge.

**Why it is here:** Establishes that everything on the following slides is running
locally, before any claim depends on it, and gets the five strands named once so no later
slide has to stop and explain what a monster is.

---

## Slide 2 - We watched the model report a count that belonged to something else

**Says:**
On the page written for parents, the model is asked for two or three sentences about how
the session is going. In testing it told a parent their child had beaten three snares.

One had been beaten. The three was real, and it was on the same page. It was the number
of notes the agent had written home.

Nothing about that sentence looks wrong. The figure was accurate, the noun attached to it
was not, and a parent has no way to tell which. Every guard we had at the time let it
through, because every guard we had at the time was checking whether numbers were true.

We hit the same shape of error three more times while building. The rest of this deck is
what we did about it.

**Shows:** Two panels side by side. Left panel headed "what the session record actually
held", showing three rows of computed facts: snares beaten, 1; notes written home, 3;
speed drills fought, 0. Right panel headed "what the model wrote", showing the sentence
with the count highlighted. A curved arrow from the highlighted count back to the wrong
row of the left panel.

**Why it is here:** The architecture lands harder if the audience has seen the failure
before they see the structure built around it. This is the one slide that should feel
uncomfortable.

---

## Slide 3 - We split the system between what code owns and what Gemma judges

**Says:**
gemma3 at this size reads a student's typed reasoning and tells you honestly whether it
holds up. Show it four teaching approaches and a student's own words, and the one it
picks is usually the right one. As a judge it is genuinely good.

Hand it a fact to own, a number or an answer key or a count or a destination, and every
so often it hands back something confident and wrong.

So the system is split on exactly that line, and the split is the same everywhere. Code
owns what is true: the answer keys, the name of the snare a wrong option carries, every
figure on every page, every candidate list, the mastery bar, every cap, every state
transition. Gemma owns what is judged: whether an explanation holds up, which lesson to
try next, which fight is worth having, what an evening means for a parent, and what to
say to the student.

The mechanism is one function. Every model call in the app goes through
gemma_client.ask_gemma, and every reply comes back as one of four shapes: one word from a
closed set, JSON naming something from a list code supplied, prose with LaTeX stripped
out, or nothing usable, which means a fallback written in plain Python. Temperature is
0.2, every loop has a call budget, and every budget has a defined behaviour when it runs
out.

Every structure on the following slides is one application of that split.

**Shows:** A two-column table with a heavy vertical rule between the columns. Left column
headed "code owns", right column headed "Gemma owns", each carrying the items listed
above one per line. The rule between them is labelled "nothing crosses". Underneath, one
wide bar: the ten call sites (teach, grade reasoning, choose strategy, react, direct next,
coach, parent note, progress reading, write question, blind self-solve) converging into a
single box labelled ask_gemma, with the four typed exits leaving its right-hand side.

**Why it is here:** This is the thesis. Everything after it is evidence, so it should be
the slide the audience can still recite at the end.

---

## Slide 4 - A session starts in the citadel and ends with a letter home

**Says:**
We follow one student, Sarah, through one evening. The run traced across the next six
slides is a real path through the code.

The nexus is a 3D hub she can orbit. Clicking a monster raises its card. She picks
Ledgerling, Financial Literacy, and the monster speaks before any question does. Its
scripted lines are in the code:

"Ah, a new account. Name: Sarah. Balance: doubtful."
"I skim a little interest off every mistake, Sarah. Business is booming."

If the session already has something to remember, code assembles the facts and asks Gemma
for one extra line to put first. The facts it is handed are the only facts it has: the
snares already beaten, the monsters already defeated, the last score, how many times she
has walked into this fight, and how many times she has walked away from it. Walking away
costs nothing, but the citadel counts it, and the monster brings it up when she comes
back.

Then a battle: five questions from the verified bank, all from that monster's strand.
After the battle the agent looks across every wrong answer, finds the snare that caught
her most often, and starts tutoring on that one.

**Shows:** A left-to-right flow of six boxes: [citadel hub] to [encounter hall, the
monster speaks first] to [battle, five bank questions] to [results, the snare that caught
them most] to [mastery loop] to a fork of [beaten, the monster drops a relic] and [handed
off to the parents]. From the fork's second branch, a downward arrow to [the Collector],
labelled "when the loop has spent every approach". A dotted return arrow from both fork
outcomes back to the citadel hub. Behind the flow, the Ledgerling card as it renders: the
unit chip reading FINANCIAL LITERACY, the monster on its stage in the card's amber, the
lore line "I collect mistakes, and I charge interest", and the Begin challenge button.

**Why it is here:** The audience needs the shape of a session in their heads before the
engineering slides, or the guards have nothing to attach to. It is also the only slide
that spends time on the game as a game.

---

## Slide 5 - Every wrong option carries the thinking that produces it

**Says:**
The bank holds 55 verified questions across the five strands, audited against the
published MTH1W expectations and the EQAO framework. Every item carries a worked
solution, and every wrong option carries the faulty thinking that produces it, written at
the same time as the question.

Sarah's first question, from the bank:

"Priya has a part-time job in Barrie and earns $800 each month. She saves 3% of her
earnings every month. How much money will she have saved in total after 6 months?"
A. $14,400.00   B. $4,656.00   C. $144.00   D. $24.00

The worked solution, as stored: "Each month Priya saves 3% of $800: 0.03 x 800 = $24.
Over 6 months she saves 6 x 24 = $144."

The item's own words on two of the wrong answers: "$24.00 is only one month of savings,
it ignores the 6-month period." "$14,400.00 uses 3 instead of 0.03, giving 800 x 3 =
$2,400 per month and 6 x 2,400 = $14,400."

Sarah ticks D. Naming what went wrong is a lookup on the option she ticked, so it happens
in plain Python with no model call in it, and there is no opportunity for the model to
name the wrong thing.

The answer key across the bank is balanced 14 / 14 / 14 / 13 over A to D, which removes
the single-letter guessing edge. It does not make the bank ungameable.

**Shows:** The Priya question rendered the way it appears in a battle, with all four
options and the Ledgerling taunt bubble in the corner. Under each wrong option, a smaller
line in a second colour carrying the bank's own sentence about it. To the right, a callout
box: "the student ticks an option, code reads the snare authored on that option, the tutor
knows what to teach. Table lookup, no model call."

**Why it is here:** The bank is where the model's authority is replaced by ours, and one
real item makes that concrete faster than any description of the format.

---

## Slide 6 - The agent counts the wrong answers and picks the snare to work on first

**Says:**
Sarah scores 2 of 5. Three answers are wrong.

On the Priya question she chose D, $24.00, one month of savings instead of six. On the
depreciation question she chose C, $20,400, the car's value after one year when the
question asked for two. On the fifth she chose A, $837.

Code reads the snare off each option she picked. Two of the three are the same one,
"Time-period mishandling", so that is where the agent starts. This step is arithmetic in
plain Python, there is no model call in it, and the reason shown to Sarah is composed
from the count: it caught her twice tonight, more than anything else did.

The app then builds one study card per missed question. The correct answer and the worked
solution come from the bank. Gemma writes the explanation of why her method fails, and a
hint that is a nudge rather than a step.

**Shows:** A three-column trace. Left column, the three items she missed with the option
letter she picked. Middle column, an arrow labelled "lookup, no model call" into the snare
named on that option, twice "Time-period mishandling" and once "Incomplete budget". Right
column, an arrow labelled "count across the battle" into a two-row tally, Time-period
mishandling 2 and Incomplete budget 1, with the top row boxed and labelled "worked on
first". Beneath, one study card as it renders in the app, with each region tagged by
origin: "bank" on the correct answer and the worked solution, "Gemma" on the explanation
and the hint.

**Why it is here:** The moment the evening turns from a quiz into a tutor, and the
cleanest place to be explicit that a decision this important is better made without the
model.

---

## Slide 7 - The mastery loop teaches, checks and adapts until a cap stops it

**Says:**
mastery.py. Four steps, repeated until something ends it.

TEACH. Gemma writes one lesson in the style of the current rung of the ladder.

CHECK. A fresh question she has not seen. Bank first, always: an unused item carrying the
same snare, then any unused item from the same strand, and only if both run dry, a
generated one. Sarah has already seen the five battle questions, so those are excluded,
and the first tier finds the compound interest question about two accounts paying 6% over
two years, which carries the same snare on option A.

EVALUATE. The multiple choice is graded against the bank's key in code. Gemma grades the
typed reasoning, if there is any.

ADAPT. Plain code decides what happens next: another rung, mastery, or a hand-off to the
parents.

The bar for mastery is two fresh correct in a row. Three caps guarantee the loop
terminates: four check questions, twelve model calls, and the ladder itself running out.
Whichever trips first ends the session and writes the note home.

**Shows:** A four-node ring, arrows clockwise. TEACH (marked Gemma), CHECK (marked bank),
EVALUATE (a node split down the middle, half marked code for the multiple choice, half
marked Gemma for the reasoning), ADAPT (marked code). Three arrows leave ADAPT: upward to
[MASTERED, two fresh correct in a row], rightward to [HANDED OFF, ladder spent, or 4
checks, or 12 calls], and back into TEACH labelled "next rung". Beside CHECK, a funnel of
three stacked bands: "unused bank item with the same snare", ticked and labelled "ground
truth key and worked solution"; "unused bank item from the same strand", greyed and
labelled "not needed tonight"; "Gemma writes one", greyed, with a padlock labelled "only
under audit, slide 12".

**Why it is here:** This is the core loop of the product, and the caps are the answer to
the first question any engineer asks about an autonomous loop.

---

## Slide 8 - Gemma chooses the next teaching approach from a fixed ladder

**Says:**
Sarah picks A, $127.20. Wrong. The correct answer is D, $7.20, because $127.20 compares
the second account at two years against the first at one. A missed check question means
the current explanation is not landing, so something genuinely different has to be tried.

The four approaches are written by us and fixed in code. Direct correction: state the
wrong move plainly, give the rule, show one worked example. Visual walkthrough: a number
line, an area model, groups of objects, a table. Side-by-side contrast: the wrong method
and the right method on the same problem, line by line, pointing at the step where they
part. Real-world analogy: money, pizza slices, game scores, then map it back.

Attempt one is always the first rung. After that, Gemma is shown only the rungs not yet
used and the student's own typed words, and asked for JSON: which one, and one sentence
saying why. It picks Side-by-side contrast, and Sarah sees that sentence on the next
lesson under "Why this approach", so the choice is visible rather than silent.

Then code checks it. The reply has to parse, and it has to name a rung still on the list.
If it does not, the session advances exactly one rung and says plainly that it is moving
to the next approach. That path has no model in it. The model chooses the route. It
cannot invent a destination, it cannot go backwards, and it cannot stall.

**Shows:** A vertical ladder with the four rungs named, rung 1 at the bottom and already
greyed out. On the left, a box holding Sarah's typed line and her wrong answer, feeding a
Gemma node. From the Gemma node, a dashed arrow labelled "proposed" toward rung 3, and the
JSON shape underneath it. Between the dashed arrow and the ladder, a diamond gate: "names
a rung still on the list?" Yes passes through to rung 3, which lights. No diverts to a
solid arrow landing on rung 2, labelled "plain code, no model call". Both routes arrive at
the same node, "TEACH again".

**Why it is here:** It applies the split from slide 3 to pedagogy, and it answers the
assumption that the app just reprompts until something sticks. The set of moves is fixed
and inspectable, and only the choice among them is the model's.

---

## Slide 9 - Gemma grades the typed explanation into three labels

**Says:**
Under every check question there is one optional box: in one line, how did you get your
answer? A student who leaves it empty is graded on the answer alone and nothing is held
against them.

Sarah uses it. Second lesson, Side-by-side contrast, and the check question is the sneaker
that grows 10% of its current value each year. She answers C, $181.50, correct.

Because she typed something, Gemma reads it and has to reply with exactly one word from a
closed set. RESOLVED, the reasoning shows the idea is genuinely understood. SHALLOW, right
answer, but the reasoning is missing, circular or lucky. SAME_ERROR, the reasoning still
shows the snare. The grader is given the correct answer and asked only to classify the
reasoning. It is never asked to redo the mathematics.

It comes back SHALLOW, and the screen says so: "You got it right, but your explanation was
thin, so it does not count toward mastery yet. Show your reasoning on the next one."

What each label does is code. RESOLVED advances the streak, SHALLOW neither advances nor
resets it, SAME_ERROR resets it to zero. An unparseable reply is read as RESOLVED, so a
model hiccup can never cost a student their streak.

A second, separate call answers what she actually typed, in the citadel's voice, naming
the idea in her sentence that held up or did not, and calling out joking or off-topic text
playfully. It is the most freeform call in the app and it is safe because it decides
nothing. The label is already assigned, the streak has already moved, the next lesson is
already chosen.

**Shows:** Three bands. Top: the check question with Sarah's typed line under it. Middle:
a Gemma node with three exit arrows carrying the three label tokens, SHALLOW taken.
Bottom: three outcome boxes wired to the arrows, "streak + 1", "streak unchanged, mastery
not demonstrated", "streak back to zero". Off to one side, a dotted box: "reply
unparseable, treated as RESOLVED, which fails in the student's favour". To the right, a
separate speech bubble showing the in-character reply, with a bar under it reading "state
changed by this call: none".

**Why it is here:** This is the difference between a quiz and a tutor, and the closed
label set is what makes it safe to let the model near it.

---

## Slide 10 - Two fresh correct answers in a row end the fight

**Says:**
Third check. Correct, and the explanation holds up. Streak 1. Fourth check, drawn from the
same strand. Correct again, reasoning holds. Streak 2.

Fresh means a question she has not seen. The bar is met, the loop stops, and the screen
prints the agent's own reason: "Two fresh questions correct in a row, and your reasoning
showed real understanding, that is the bar for mastery, so we can stop."

The recap prints the record of the run: the snare, four check questions answered, a final
streak of two, and the approaches used, Direct correction then Side-by-side contrast.

Three things follow. Gemma forges a relic named for the exact skill she won, which is the
only permanent reward in the game and can only be earned this way; if the model fails, a
canned relic drops instead. Financial Literacy is marked cleared, which changes what the
agent may offer her next. And a letter goes home saying what was beaten and how. Clear all
five strands and the fifth seal breaks, the gate opens, and the finale plays.

**Shows:** A horizontal strip of four check slots left to right. Slot 1 wrong, tagged with
the rung change from 1 to 3. Slot 2 correct with a SHALLOW tag and a small note "streak
does not advance". Slots 3 and 4 correct with RESOLVED tags, the pair bracketed and
labelled "the bar". Under each slot, the streak value at that point: 0, 0, 1, 2. At the
right, the mastery panel as it renders, with the relic name and its one-line power, and
three outcome chips fanning out beneath: "relic drops", "strand cleared", "letter home
written".

**Why it is here:** Defines what winning means in this app, and shows that the stopping
condition is evidence rather than a number of attempts.

---

## Slide 11 - The verified solution rides in the prompt so the model never redoes the arithmetic

**Says:**
First failure. Asked to explain a missed question, the model would redo the sums, and the
numbers it produced were sometimes not the right ones.

The fix was to stop asking it to. On every explanation call on the curriculum path, the
verified worked solution rides in the prompt, and the prompt ends: "Any numbers you
mention must come from the verified solution above, do NOT invent new calculations or
results."

From the bank, in Geometry and Measurement: "A 13 m ladder leans against a vertical wall.
The foot of the ladder is 5 m from the base of the wall. How far up the wall does the
ladder reach?" The solution carried in the prompt: "The ladder is the hypotenuse, so the
height is a leg: h squared = 13 squared minus 5 squared = 169 - 25 = 144, giving h = 12
m."

A student picks 8 m. The model's job is to explain why subtracting the two lengths is not
what the theorem says. The 12 was already on the page before the model was called.

Hints follow the same rule. Level one is a nudge with no step revealed, level two gives
the first concrete step, and both are grounded in the same verified solution.

**Shows:** An anatomy diagram of one prompt. A tall box divided into four stacked bands,
the first three shaded as code-supplied: [the question, from the bank], [the option the
student ticked, from the session], [the verified worked solution, from the bank], and
unshaded at the bottom [the instruction: explain why this method fails, state no other
number]. An arrow out of the box into a Gemma node, and out of that into the
student-facing explanation card. A margin note against the third band: "this is the only
maths on the screen".

**Why it is here:** The first of the four failures, and the one that turns the thesis into
a prompt-level rule an engineer can copy.

---

## Slide 12 - A generated question has to survive a blind re-solve before a student sees it

**Says:**
Second failure. When the bank ran out of unused items and we let the model write a
question, it sometimes marked the wrong option as the answer. On screen that costs a
student a wrong "wrong". On a sheet a parent has already printed, it costs their evening.

So generation is bank first and audited. When the bank cannot supply a fresh check
question, Gemma writes one as JSON with four options and a key. The key is then stripped,
and the same model is handed the question and the four options and asked to solve it and
reply with a single letter. The question is used only if the two letters agree. Multiple
choice is deliberate here: a letter can be compared exactly, a free-text answer cannot.

The audit fails closed. A disagreement, an unreadable reply, or an exhausted call budget
all discard the question, and the loop writes another.

Third failure, on the same calls. The model sometimes replied in Spanish on the open
generation prompts. Those four prompts now say English.

The printable parent sheet runs the same rule under its own budget, three attempts per
slot and twenty-four model calls for the whole sheet. If it cannot fill ten slots, the
sheet comes back short rather than with a question we could not verify.

**Shows:** A pipeline read left to right. [Unused bank item available?] with a "yes" arrow
straight to [use it, key is ground truth]. The "no" arrow goes to [Gemma writes question,
four options, key], then to [key stripped], drawn as a scissors cut across the JSON, then
to [same model solves it blind], then to a diamond [letters match?]. Yes goes to [shown to
the student]. No loops back to the writing step through a box [discard, budget minus one].
A footer strip: "budget exhausted, the sheet ends short, never unverified".

**Why it is here:** The guard that turns a model-shaped bug into a retry instead of a
student-facing error, and the one whose cost is easiest for a room to picture.

---

## Slide 13 - Gemma chooses where the student goes next from a list code builds

**Says:**
Everywhere else the model reacts to one question. In agent.direct_next it shapes the
session.

After a battle it is handed the monsters still standing and a short factual account of
tonight's run: what was just scored, which snares have been beaten, which strands are
cleared, what has never been attempted, and the snare that caught the student most today.
It picks the next fight and gives one sentence in the citadel's voice naming the evidence.

The prompt is blunt about the limits of what it knows: "THE COMPLETE RECORD of this
student's run, there is nothing else, and anything not listed here has NOT happened." That
is not what makes this safe.

What makes it safe is that code builds the candidate list from the actual session state,
so a monster already cleared is never on it, and code rejects any reply that does not name
a candidate. On a rejection the first candidate is taken and the reason says plainly what
it is. When only one fight is left there is no model call at all.

The same function picks which of the Collector's lieutenants to drill, from the drills
actually fought that session and the misses those runs produced.

**Shows:** Three horizontal bands. Top band labelled "code": session state feeding a
filter "still-open fights only", producing two outputs, a list of named candidates with
the cleared monsters struck through, and a list of factual evidence lines. Middle band
labelled "Gemma": one node taking both inputs and emitting JSON with a choice and a why.
Bottom band labelled "code": a diamond gate "does the choice name a candidate?", yes going
to [route the student, show the sentence], no going to [take the first candidate, state
the plain reason] on a red edge. Beside the gate, two margin notes: "cleared monsters are
never on the list" and "one candidate left means no model call". Bottom right, the output
as it appears on screen, a note headed "The citadel sends you to ..." with a button under
it.

**Why it is here:** This is the slide that earns the word agent, and it shows the same
guard pattern applied to routing rather than to content.

---

## Slide 14 - The Collector arrives when the tutoring loop has spent every approach

**Says:**
Sarah got there. Plenty of students will not, and that branch is built. When the ladder
runs out, or the attempt cap or the call budget is reached, the loop stops and hands off,
and the student sees why: "Handing off to your parents because every teaching strategy has
been tried, drilling further is unlikely to help more than a person can."

In the game, the warning the monsters have been making since the introduction comes true.
The Collector does not test new ideas. He tests the arithmetic a Grade 9 student is
supposed to already own, and he tests it against a clock: ten questions, eight seconds
each, three lives. Nothing in his trial counts against the curriculum record. It is speed,
not content.

Losing sends the student to one of three lieutenants, ninety seconds each. Twinfang drills
doubling and halving, The Niner drills nines, Splitjaw drills making tens. Afterwards
Gemma is handed the exact questions that were missed, names the pattern in them, teaches
the one shortcut that fixes it, and writes three practice questions of that type.

Losing costs nothing. Retreating costs nothing either, but the citadel counts it.

**Shows:** A state diagram. [Mastery loop hands off] with two arrows leaving it, one to [a
letter goes home] and one to [the Collector's trial, 10 questions, 8 seconds each, 3
lives]. From the trial, "win" goes to [basics returned, back to the citadel] and "lose"
goes to [lieutenant chosen by direct_next] to [90-second drill] to [Gemma reads the actual
misses and coaches] and back to the trial. A separate small path from any battle screen
labelled [retreat] to [the citadel], annotated "free, and remembered". Behind the diagram,
the Collector's chamber as it renders, with the war clock overlay, and in the corner one
in-game line in quotes: "You walked out on me once. I kept your seat warm."

**Why it is here:** The demo shows a win, so the failure path has to be shown rather than
left to be asked about. It is also the demo's second act.

---

## Slide 15 - A letter goes home the same evening saying what happened

**Says:**
Three moments write to the parents' page: after a battle with mistakes, when the tutoring
loop hands off, and when a snare is beaten. Sarah's evening produced two.

Each note is about one evening. The facts in it are computed: the score, which snare,
which teaching approaches were tried and in what order, how many follow-up questions were
correct. Gemma writes the interpretation and three things to try at the kitchen table, and
on a hand-off note it is told which approaches already failed, so it does not suggest them
straight back. The prompt tells it plainly not to invent numbers.

Notes are kept for the session and written to data/letters/<challenger>.json on the same
machine, so a parent can read them after the child has closed the game. A read-only disk
loses the file, never the lesson.

From that page a parent presses one button and gets a printable sheet on one snare: up to
ten questions with room to write, and the answer key on its own page so the sheet can be
worked before it is marked. Verified bank items first, tagged with that snare, then the
same strand, and it stops at the strand rather than quietly filling with unrelated topics.
Anything generated to make up the number passes the blind audit from slide 12 first, and
the page says which questions came from where. It is a standalone HTML file with inline
styling, no fonts, no images and no scripts, so it prints the same on any machine.

It is a note about tonight and one thing to try.

**Shows:** Left, the letters-home page as it renders: the heading "For mum and dad", the
caption "2 notes from this session, newest first. Nothing left the device to write them.",
and the two notes stacked as expanders with the newest open, showing the code-written
header line, the prose, and the "Try at home" bullets. A single arrow to the right
labelled "one button", into the printed sheet in two parts: page one with numbered
questions and ruled working boxes, page two the answer key with the bank's working printed
under each answer. Along the bottom, three small tags: "after a battle with mistakes", "on
a hand-off", "on a win".

**Why it is here:** The output that leaves the screen, and the point where the blind audit
stops being an internal detail and starts protecting someone outside the app.

---

## Slide 16 - Code computes every figure on the parents' page and discards any reply that states one

**Says:**
Back to the sentence this deck opened with.

progress.py computes everything on that page: which snares were beaten and what they are
called, how many notes went home and what each was about, best and latest score for each
drill lane, whether the drills are improving measured against the first run on that lane,
and the relics earned. Those figures are printed by code, in a table, beside the prose.

Gemma is handed the finished facts and asked for two or three sentences of interpretation,
under one instruction it cannot negotiate: use no numbers at all, in digits or in words.
Any figure in the reply discards the whole reply, even a true one. So does prose that
contradicts a trend code has already computed, and so does warm filler that never names
anything from this session. A discarded reply is replaced by a deterministic sentence
built from the same facts. On the small model that happens often, and the page reads the
same either way.

Checking each number against the record would not have caught the sentence on slide 2,
because the number was true and only the noun was wrong. That is why the rule is absolute
rather than a check.

What we are not claiming. Nothing here measures retention and nothing times a session, and
no student has used it yet. The bank is audited against the published expectations, but
the items do not store an expectation code. Balancing the answer key removes the
single-letter guessing edge, which is not the same as making the bank ungameable. The app
runs on gemma3:12b, set through the GEMMA_MODEL environment variable, and the committed
default in the code is still gemma3:1b, one variable away; the same architecture and the
same prompts run either way, and the smaller model just trips the fallbacks more often,
which is what the fallbacks are for.

What we would do next: put it in front of real Grade 9 students, and find out which of
these decisions survives contact with them.

**Shows:** Left, the parents' progress panel as it renders, the computed table, the
best-against-latest bar chart, and the interpretation sentence underneath. Right, the
filter drawn as three gates a reply passes in order: [contains a digit or a number word?]
to discard, [contradicts the computed trend?] to discard, [names nothing from this
session?] to discard. All three discard arrows converge on one box, [deterministic
sentence, composed from the same facts], drawn as the wider path. Below both, the limits
as plain text on a clean background, no icons and no colour coding. Team names and the
hackathon line along the bottom edge.

**Why it is here:** Closes the loop opened on slide 2, and puts the limits on the same
slide as the strictest guard, in our own words rather than leaving them to be found in
questions.
