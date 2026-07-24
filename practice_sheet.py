"""
practice_sheet.py  —  a printable practice sheet for ONE trick.

The mastery loop lives on a screen; a kitchen table does not. This module takes
a single trick (the wrong idea that feels right) and lays out a sheet a parent
can print and work through with their child: numbered questions with room to
write, then an answer key on its own page.

Two rules decide what goes on the paper, in this order:

  1. BANK FIRST. Verified items tagged with the trick, then items from the same
     strand. They carry a ground-truth answer key AND a worked solution, so the
     parent is never left arguing with the paper about who is right.
  2. GENERATION LAST, AND ONLY UNDER AUDIT. If the bank runs dry, Gemma writes
     the remainder one at a time, and each one must survive a blind self-solve
     (mastery._self_check applied to paper): the model solves its own question
     WITHOUT seeing the key it just wrote, and the question is thrown away
     unless the two agree. A small model marking its own wrong key is a real
     failure mode we caught in testing — on screen it costs one retry, on a
     printed sheet it would cost a parent's evening.

Hard call caps mean a sheet always finishes. If generation cannot fill the
quota, the sheet comes back short — never with a question we could not verify.
"""
from __future__ import annotations
import html
import json
import re

from gemma_client import ask_gemma, plainify

ATTEMPTS_PER_ITEM = 3    # tries (write + audit) before we give up on one slot
MAX_MODEL_CALLS = 24     # absolute ceiling for a whole sheet, belt and braces
GEN_TOKENS = 320         # enough for one question plus four options as JSON
AUDIT_TOKENS = 48        # the blind solve answers with a single letter


class _Budget:
    """The ceiling that guarantees build_sheet() returns. Every model call goes
    through spend(); when it says no, the sheet simply ends early."""

    def __init__(self, limit: int = MAX_MODEL_CALLS):
        self.left = limit

    def spend(self) -> bool:
        if self.left <= 0:
            return False
        self.left -= 1
        return True


def build_sheet(trick_id: str, trick_name: str, strand: str, questions: list,
                want: int = 10, exclude_ids=()) -> dict:
    """Build one printable practice sheet for a single trick.

    Returns {"items": [...], "html": "<...>", "counts": {"bank": n, "generated": m}}
    where "html" is a complete standalone document ready for the printer."""
    exclude = set(exclude_ids or ())
    items = _bank_items(trick_id, strand, questions or [], want, exclude)
    bank_count = len(items)

    if len(items) < want:
        seed = items[0]["question"] if items else ""
        items += _generated_items(trick_name, strand, seed, want - len(items), items)

    return {
        "items": items,
        "html": _render(trick_name, strand, items),
        "counts": {"bank": bank_count, "generated": len(items) - bank_count},
    }


# ------------------------------------------------------------------- BANK
def _bank_items(trick_id: str, strand: str, questions: list, want: int,
                exclude: set) -> list:
    """Verified items, most on-target first: tagged with THIS trick, then the
    same strand. We stop at the strand — a sheet titled with one trick should
    not quietly fill up with unrelated topics."""
    picked, taken = [], set(exclude)

    def take(q):
        taken.add(q["id"])
        picked.append(_from_bank(q))

    for q in questions:
        if len(picked) >= want:
            return picked
        if q["id"] in taken:
            continue
        if any(o.get("trick_id") == trick_id for o in q.get("options", [])):
            take(q)
    for q in questions:
        if len(picked) >= want:
            return picked
        if q["id"] not in taken and q.get("strand") == strand:
            take(q)
    return picked


def _from_bank(q: dict) -> dict:
    correct = next((o for o in q["options"] if o.get("is_correct")), None)
    return {
        "source": "bank",
        "id": q["id"],
        "question": q["question"],
        "options": [{"label": o["label"], "text": o["text"],
                     "is_correct": bool(o.get("is_correct"))}
                    for o in q["options"]],
        "correct": q.get("correct", correct["label"] if correct else ""),
        "answer": correct["text"] if correct else "",
        "solution": q.get("solution", ""),
    }


# ------------------------------------------------------- GENERATION + AUDIT
def _generated_items(trick_name: str, strand: str, seed: str, need: int,
                     already: list) -> list:
    """Fill the remaining slots one question at a time, each one audited before
    it is allowed onto the paper. Multiple choice is deliberate: the blind
    re-solve can be scored exactly (letter against letter), which a free-text
    answer cannot."""
    budget = _Budget()
    made = []
    for _ in range(need):
        item = _one_generated(trick_name, strand, seed, already + made, budget)
        if item is None:
            break  # budget spent or three failed audits: return a shorter sheet
        made.append(item)
    return made


def _one_generated(trick_name: str, strand: str, seed: str, sofar: list,
                   budget: _Budget) -> dict | None:
    avoid = " | ".join(i["question"][:80] for i in sofar[-3:])
    for _ in range(ATTEMPTS_PER_ITEM):
        if not budget.spend():
            return None
        raw = ask_gemma(
            f"TASK: practice\n"
            f"TRICK: {trick_name}\n"
            f"Write ONE new Grade 9 {strand} multiple-choice question, in English, "
            f"working the SAME idea as: {seed or trick_name}\n"
            f"Introduce NO new concept, formula or skill. If the idea is about "
            f"exponents, do not write a percentage question; if it is about the "
            f"median, do not write one about probability. Sharing a strand is NOT "
            f"the same idea, and a question on a different idea is useless on this "
            f"sheet, because every question here has to give the student another "
            f"go at one thing.\n"
            f"One wrong option must be the answer a student lands on when they fall "
            f"for this: {trick_name}. Exactly one option is correct.\n"
            f"Use different numbers from these questions: {avoid or 'none yet'}\n"
            f"Plain text math only - fractions as 3/4, powers as 2^3, real dollar "
            f"signs for money, no LaTeX and no special formatting.\n"
            f"Return ONLY JSON, no other text, exactly this shape:\n"
            f'{{"question": "...", "options": {{"A": "...", "B": "...", '
            f'"C": "...", "D": "..."}}, "correct": "A"}}',
            max_new_tokens=GEN_TOKENS,
        )
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            continue
        try:
            data = json.loads(m.group())
            opts = {str(k).strip().upper(): str(v) for k, v in data["options"].items()}
            key = str(data["correct"]).strip().upper()[:1]
            question = plainify(str(data["question"])).strip()
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            continue
        if key not in opts or len(opts) < 3 or not question:
            continue
        if any(question.lower() == i["question"].lower() for i in sofar):
            continue
        if not _blind_solve_agrees(question, opts, key, budget):
            continue
        return {
            "source": "generated",
            "id": f"GEN-{len(sofar) + 1}",
            "question": question,
            "options": [{"label": k, "text": plainify(v).strip(), "is_correct": k == key}
                        for k, v in sorted(opts.items())],
            "correct": key,
            "answer": plainify(opts[key]).strip(),
            "solution": "",   # nothing verified to show, so the key stays silent
        }
    return None


def _blind_solve_agrees(question: str, opts: dict, key: str,
                        budget: _Budget) -> bool:
    """The audit. Gemma solves the question it just wrote WITHOUT being shown
    which option it marked correct, and the question only survives if the two
    answers match. Anything else — a disagreement, an unreadable reply, an
    exhausted budget — fails closed and the question is discarded."""
    if not budget.spend():
        return False
    listing = "\n".join(f"{k}) {v}" for k, v in sorted(opts.items()))
    verdict = ask_gemma(
        f"TASK: solve\n"
        f"Solve this and reply with ONLY the letter of the correct option.\n"
        f"{question}\n{listing}",
        max_new_tokens=AUDIT_TOKENS,
    )
    m = re.search(r"\b([A-F])\b", verdict.upper())
    return bool(m) and m.group(1) == key


# ------------------------------------------------------------------ PRINT
_CSS = """
:root { color-scheme: light; }
body {
  font-family: Georgia, "Times New Roman", Times, serif;
  color: #191512; background: #ffffff;
  max-width: 46em; margin: 0 auto; padding: 2.2rem 1.6rem 3rem;
  line-height: 1.5;
}
h1 { font-size: 1.55rem; margin: 0 0 .3rem; line-height: 1.25; }
h2 { font-size: 1.25rem; margin: 0 0 .6rem; }
.meta { margin: 0 0 1rem; font-size: .92rem; letter-spacing: .02em; }
.guide {
  margin: 0 0 1.6rem; padding: .7rem .9rem;
  border: 1px solid #b9b2a8; font-size: .95rem;
}
.guide strong { letter-spacing: .03em; }
hr { border: 0; border-top: 1px solid #b9b2a8; margin: 1.4rem 0; }
ol.sheet, ol.key-list { padding-left: 1.6rem; margin: 0; }
ol.sheet > li { margin: 0 0 1.2rem; page-break-inside: avoid; }
ol.key-list > li { margin: 0 0 .9rem; page-break-inside: avoid; }
.q { margin: 0 0 .5rem; }
ul.options { list-style: none; padding: 0; margin: 0 0 .6rem; }
ul.options li { margin: .15rem 0; }
.work { min-height: 30mm; border: 1px solid #cdc6bb; margin: .4rem 0 0; }
.answer { margin: 0; }
.answer .label { letter-spacing: .04em; }
.solution { margin: .2rem 0 0; font-size: .95rem; }
.key { page-break-before: always; break-before: page; }
.key-note { font-size: .92rem; margin: 0 0 1.1rem; }
.origin { font-size: .88rem; }
footer { margin-top: 2rem; font-size: .85rem; }

@page { margin: 18mm; }
@media print {
  body {
    max-width: none; margin: 0; padding: 0;
    color: #000; background: #fff; font-size: 11.5pt;
  }
  .guide, .work { border-color: #000; }
  .work { min-height: 34mm; }
  ol.sheet > li { margin-bottom: 9mm; }
  hr { border-top-color: #000; }
  a { color: #000; text-decoration: none; }
}
"""


def _render(trick_name: str, strand: str, items: list) -> str:
    """A complete standalone document: inline CSS, no fonts, no images, no
    scripts, so it prints the same on any machine that opens the file."""
    guidance = (
        f"Watch how they get there, not only what they write down: every question "
        f"here is built around a single trick - {trick_name or 'this one'} - so the "
        f"moment that idea shows up in their working, stop and talk that one step "
        f"through together."
    )
    head = (
        f"<header>\n"
        f"<h1>Practice sheet: {_esc(trick_name)}</h1>\n"
        f'<p class="meta">Strand: {_esc(strand)} &middot; Grade 9 &middot; '
        f"{len(items)} question{'' if len(items) == 1 else 's'} &middot; "
        f"answer key on the last page</p>\n"
        f'<p class="guide"><strong>For mum and dad:</strong> A trick is a wrong '
        f"idea that feels right. {_esc(guidance)}</p>\n"
        f"</header>"
    )

    body = ['<ol class="sheet">']
    for item in items:
        body.append("<li>")
        body.append(f'<p class="q">{_esc(item["question"])}</p>')
        if item.get("options"):
            body.append('<ul class="options">')
            for o in item["options"]:
                body.append(f'<li>{_esc(o["label"])}) {_esc(o["text"])}</li>')
            body.append("</ul>")
        body.append('<div class="work"></div>')
        body.append("</li>")
    body.append("</ol>")

    key = ['<section class="key">', "<h2>Answer key</h2>",
           '<p class="key-note">Every answer below comes from the verified '
           'question bank or from a question Gemma wrote and then solved again '
           'blind to check its own key. Where the bank supplies working, it is '
           'printed with the answer.</p>',
           '<ol class="key-list">']
    for item in items:
        key.append("<li>")
        label = f'{_esc(item["correct"])}) ' if item.get("correct") else ""
        key.append(f'<p class="answer"><span class="label">Answer:</span> '
                   f'{label}{_esc(item.get("answer", ""))}</p>')
        if item.get("solution"):
            key.append(f'<p class="solution">Working: {_esc(item["solution"])}</p>')
        elif item.get("source") == "generated":
            key.append('<p class="solution origin">Written fresh by Gemma and '
                       'checked by solving it again without the key.</p>')
        key.append("</li>")
    key += ["</ol>", "</section>"]

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Practice sheet - {_esc(trick_name)}</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"{head}\n<hr>\n" + "\n".join(body) + "\n" + "\n".join(key) +
        "\n<footer>Made by GEMMA MONSTERS. Every question on this sheet was "
        "verified before it was printed.</footer>\n</body>\n</html>\n"
    )


def _esc(text) -> str:
    return html.escape(str(text or ""), quote=False).replace("\n", "<br>")
