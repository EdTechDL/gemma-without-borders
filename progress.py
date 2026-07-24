"""
progress.py  —  the progress summary at the top of the letters-home page.

THE RULE THIS MODULE EXISTS TO ENFORCE: CODE COMPUTES THE NUMBERS, GEMMA ONLY
INTERPRETS THEM. Every count, every best and latest drill score, every trend
and the headline itself are worked out here in plain Python from the session's
own records. The model is never asked how many, how often or whether something
went up — it is handed the finished facts and writes the sentences a parent
reads. This is the same guardrail used everywhere else in the app: the model
never recomputes the maths, and it never owns a figure.

Three things follow from that split:

  * The prose is checked before it ships. Gemma is not allowed to state a
    figure at all — the counts are printed by code right beside its words — so
    any number in the reply, in digits or spelled out, means the reply is
    discarded and a deterministic sentence, built from the same facts, goes out
    instead. Prose vague enough to fit any child on any day is discarded the
    same way, and so is prose that contradicts the record — 'improving
    quickly' about a drill fought once is a claim no parent can check.
  * Those refusals are not a failure mode, they are the feature. On the small
    1b model the deterministic sentence goes out often; it is composed from the
    same facts, so the page reads the same and every word of it is true.
  * The page can never break. If Ollama is not running, or the call raises, or
    the reply comes back empty, the fallback sentence is used and the parent
    still sees a complete summary.

Written for mum and dad, in the app's house language: a "trick" is the wrong
idea that feels right, and a single question is a "check question".
"""
from __future__ import annotations

import re

from gemma_client import ask_gemma, gemma_available, plainify

# The speed-drill lanes, in the parents' words rather than the code's.
# Unknown lanes fall through to the raw key so a new drill still reports.
LANE_LABELS = {
    "doubles": "doubling and halving",
    "nines": "nines, fast",
    "split": "making tens",
}

# What each note home was about, said the way a parent would say it.
LETTER_KINDS = {
    "quiz": "after the diagnostic quiz",
    "mastery": "celebrating a trick beaten",
    "escalation": "asking for your help with a trick",
    "report": "a progress note",
}
LETTER_KIND_ORDER = ["quiz", "mastery", "escalation", "report"]

# Gemma's own vocabulary sometimes drifts; plainify() already fixes the big
# ones, and these keep the rest of the page speaking the house language.
_HOUSE_WORDS = [
    (re.compile(r"\bprobing\b", re.I), "checking"),
    (re.compile(r"\bprobes?\b", re.I), "check question"),
    (re.compile(r"\b(?:learning|knowledge|skill)\s+gaps?\b", re.I),
     "the trick that caught them"),
    (re.compile(r"\bgaps?\b", re.I), "the trick that caught them"),
]

# THE READING MAY NOT STATE A FIGURE AT ALL. Checking each number against the
# record is not enough: "beaten three tricks" borrows the 3 that belongs to the
# notes count and reads as perfectly true. Pairing a number to the right noun
# is exactly the judgement a 1b model gets wrong, and we watched it do so. So
# the rule is absolute and needs no judgement to enforce — every count on this
# page is printed by code beside Gemma's words, and Gemma writes only about
# what they mean. Any digit or spelled-out number in the reply means the reply
# is discarded.
_SPELLED_NUMBERS = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|dozen|couple|several|once|twice|handful)\b", re.I)


# ------------------------------------------------------------------ helpers
def _int(value):
    """Scores arrive from the browser and may be missing or junk."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _lane_label(lane: str) -> str:
    return LANE_LABELS.get(lane, lane.replace("_", " "))


def _join(names: list) -> str:
    """'a', 'a and b', 'a, b and c' — for prose, not for a table cell."""
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _dedupe(items) -> list:
    seen, out = set(), []
    for item in items or []:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


# ------------------------------------------------------- the computed facts
def _letter_facts(letters) -> dict:
    """How many notes went home, and what each one was about."""
    counts = {}
    titles = []
    for letter in letters or []:
        if not isinstance(letter, dict):
            continue
        kind = str(letter.get("kind") or "report").strip().lower()
        counts[kind] = counts.get(kind, 0) + 1
        title = str(letter.get("title") or "").strip()
        if title:
            titles.append(title)
    ordered = [k for k in LETTER_KIND_ORDER if k in counts]
    ordered += sorted(k for k in counts if k not in LETTER_KIND_ORDER)
    breakdown = [{"kind": k, "about": LETTER_KINDS.get(k, "a progress note"),
                  "count": counts[k]} for k in ordered]
    return {"total": sum(counts.values()), "breakdown": breakdown,
            "titles": titles}


def _drill_facts(skirmish_log) -> list:
    """Best and latest score per lane, and whether it is improving.

    'Improving' is the latest run measured against the FIRST run on that lane:
    that is the comparison a parent actually cares about (is this getting
    better since they started), and it needs no judgement call from a model.
    One run alone is not a trend, and says so."""
    lanes: dict = {}
    for entry in skirmish_log or []:
        if not isinstance(entry, dict):
            continue
        lane = str(entry.get("lane") or "").strip()
        if not lane:
            continue
        lanes.setdefault(lane, []).append({
            "score": _int(entry.get("score")),
            "streak": _int(entry.get("streak")),
            "misses": [str(x) for x in (entry.get("misses") or []) if x],
        })

    rows = []
    for lane, runs in lanes.items():
        scores = [r["score"] for r in runs if r["score"] is not None]
        streaks = [r["streak"] for r in runs if r["streak"] is not None]
        first, latest = (scores[0], scores[-1]) if scores else (None, None)
        if len(scores) < 2:
            trend = "too early to tell"
        elif latest > first:
            trend = "improving"
        elif latest < first:
            trend = "slipping"
        else:
            trend = "holding steady"
        rows.append({
            "lane": lane,
            "label": _lane_label(lane),
            "runs": len(runs),
            "best": max(scores) if scores else None,
            "first": first,
            "latest": latest,
            "best_streak": max(streaks) if streaks else None,
            "trend": trend,
            "recent_misses": runs[-1]["misses"][:4],
        })
    return rows


def _overall_trend(drills: list) -> str:
    """One word for the drills as a whole, computed from the per-lane trends."""
    if not drills:
        return ""
    trends = {d["trend"] for d in drills}
    if "improving" in trends and "slipping" not in trends:
        return "improving"
    if "slipping" in trends and "improving" not in trends:
        return "slipping"
    if "improving" in trends and "slipping" in trends:
        return "mixed"
    if trends == {"too early to tell"}:
        return "too early to tell"
    return "holding steady"


def _relic_facts(relics) -> list:
    out = []
    for relic in relics or []:
        if not isinstance(relic, dict):
            continue
        name = str(relic.get("name") or "").strip()
        if not name:
            continue
        out.append({"name": name,
                    "power": str(relic.get("power") or "").strip(),
                    "monster": str(relic.get("monster") or "").strip()})
    return out


# ------------------------------------------------------------- the table
def _build_rows(tricks, letter_facts, drills, relics) -> list:
    """Small uniform dicts, ready for st.table / st.dataframe."""
    rows = [{
        "What": "Tricks beaten",
        "Count": len(tricks),
        "Details": _join(tricks) or "none yet",
    }, {
        "What": "Notes written for you",
        "Count": letter_facts["total"],
        "Details": ", ".join(f"{b['count']} {b['about']}"
                             for b in letter_facts["breakdown"]) or "none yet",
    }]
    for drill in drills:
        detail = []
        if drill["best"] is not None:
            detail.append(f"best {drill['best']}")
        if drill["latest"] is not None:
            detail.append(f"latest {drill['latest']}")
        detail.append(drill["trend"])
        rows.append({
            "What": f"Speed drill: {drill['label']}",
            "Count": drill["runs"],
            "Details": ", ".join(detail),
        })
    if not drills:
        rows.append({"What": "Speed drills", "Count": 0,
                     "Details": "none fought yet"})
    rows.append({
        "What": "Relics earned",
        "Count": len(relics),
        "Details": _join([r["name"] for r in relics]) or "none yet",
    })
    return rows


def _build_chart(drills: list) -> dict:
    """A dict of plain series, keyed by lane, ready for st.bar_chart.

    Empty when there are no drills — the caller should check before plotting.
    No plotting library and no numpy: just dicts of numbers."""
    best = {d["label"]: d["best"] for d in drills if d["best"] is not None}
    latest = {d["label"]: d["latest"] for d in drills if d["latest"] is not None}
    if not best and not latest:
        return {}
    return {"Best score": best, "Latest score": latest}


def _build_headline(tricks, letter_facts, drills, relics, trend) -> str:
    """Computed by code, never by the model."""
    if not tricks and not letter_facts["total"] and not drills and not relics:
        return "Nothing to show yet — the first battle has not been fought."
    bits = [_plural(len(tricks), "trick") + " beaten" if tricks
            else "no tricks beaten yet"]
    if letter_facts["total"]:
        bits.append(_plural(letter_facts["total"], "note") + " written for you")
    if relics:
        bits.append(_plural(len(relics), "relic") + " earned")
    if drills:
        runs = sum(d["runs"] for d in drills)
        bits.append(_plural(runs, "speed drill") + " fought")
    line = _join(bits)
    tail = {"improving": " — the drills are improving",
            "slipping": " — the drills have slipped",
            "mixed": " — the drills are mixed",
            "holding steady": " — the drills are holding steady",
            "too early to tell": " — too early to call the drills"}.get(trend, "")
    return line[0].upper() + line[1:] + tail + "."


# --------------------------------------------------------------- the facts
def _facts_lines(tricks, letter_facts, drills, relics, trend, last_score) -> list:
    """The complete, computed record handed to Gemma. Nothing else is."""
    lines = []
    if tricks:
        lines.append(f"Tricks beaten so far: {len(tricks)} "
                     f"({_join(tricks)}).")
    else:
        lines.append("Tricks beaten so far: 0.")
    if letter_facts["total"]:
        about = ", ".join(f"{b['count']} {b['about']}"
                          for b in letter_facts["breakdown"])
        lines.append(f"Notes written home: {letter_facts['total']} ({about}).")
    else:
        lines.append("Notes written home: 0.")
    for drill in drills:
        parts = [_plural(drill["runs"], "run")]
        if drill["best"] is not None:
            parts.append(f"best score {drill['best']}")
        if drill["latest"] is not None:
            parts.append(f"latest score {drill['latest']}")
        if drill["best_streak"] is not None:
            parts.append(f"best streak {drill['best_streak']}")
        parts.append(drill["trend"])
        lines.append(f"Speed drill '{drill['label']}': " + ", ".join(parts) + ".")
    if drills:
        lines.append(f"Speed drills overall: {trend}.")
    else:
        lines.append("Speed drills: none fought yet.")
    if relics:
        lines.append(f"Relics earned: {len(relics)} "
                     f"({_join([r['name'] for r in relics])}).")
    else:
        lines.append("Relics earned: 0.")
    if str(last_score).strip():
        lines.append(f"Most recent quiz score: {str(last_score).strip()}.")
    return lines


# ------------------------------------------------------------- the reading
def _fallback_reading(tricks, letter_facts, drills, relics, trend) -> str:
    """Two or three sentences composed straight from the computed facts, used
    whenever the model is unavailable, fails, states a figure of its own or
    oversteps the record. The page always has something true to show."""
    if tricks:
        first = (f"So far {_plural(len(tricks), 'trick')} has been beaten"
                 if len(tricks) == 1 else
                 f"So far {len(tricks)} tricks have been beaten")
        first += f" ({_join(tricks)})"
        first += (f", and {_plural(letter_facts['total'], 'note')} "
                  "went home about the work"
                  if letter_facts["total"] else "")
        first += "."
    elif letter_facts["total"]:
        first = (f"No tricks have been beaten yet, and "
                 f"{_plural(letter_facts['total'], 'note')} has gone home about "
                 "the work so far." if letter_facts["total"] == 1 else
                 f"No tricks have been beaten yet, and "
                 f"{_plural(letter_facts['total'], 'note')} have gone home about "
                 "the work so far.")
    else:
        first = "This session is just beginning, so there is little to read yet."

    if drills:
        named = drills[0]
        second = "On the speed drills, "
        if named["best"] is not None and named["latest"] is not None:
            second += (f"'{named['label']}' is at a best of {named['best']} "
                       f"and a latest of {named['latest']}")
        else:
            second += (f"'{named['label']}' has been fought "
                       + _plural(named["runs"], "time"))
        second += f", and overall the drills are {trend}."
    else:
        second = ("No 90-second speed drills have been fought yet, so there is "
                  "no timing history to read.")

    if any(b["kind"] == "escalation" for b in letter_facts["breakdown"]):
        third = ("The note asking for your help is the one to open first: it "
                 "names the trick that caught them and gives three things to "
                 "try at the kitchen table.")
    elif tricks:
        third = (f"A good next step is to ask them to explain {tricks[-1]} back "
                 "to you in their own words.")
    elif drills:
        third = ("A good next step is one more 90-second drill, so there is a "
                 "second score to compare against.")
    else:
        third = ("A good next step is the diagnostic quiz, which is what gives "
                 "the tutor something to work with.")
    return " ".join([first, second, third])


def _states_a_figure(text: str) -> bool:
    """True if the reading puts a number of its own on the page, in digits or
    in words. Code owns every figure here, so this is always a refusal."""
    return bool(re.search(r"\d", text) or _SPELLED_NUMBERS.search(text))


def _contradicts_record(text: str, tricks: list, drills: list, relics: list,
                        trend: str, has_escalation: bool) -> bool:
    """True if the reading says something the record does not support.

    Refusing an invented number is not enough on its own: a small model will
    write 'improving quickly' about a single drill run, and a parent has no way
    to know that was never in the record. Code owns the trend, so the model is
    not allowed to contradict it. The claims checked here are the ones this
    page exists to make, so they are the ones worth refusing."""
    low = text.lower()
    # 'progress' is deliberately not here: "we cannot see how those are
    # progressing yet" is the record agreeing with itself, not overclaiming.
    if re.search(r"\b(?:improv|faster|getting better|speeding up)", low) \
            and trend != "improving":
        return True
    if re.search(r"\b(?:slipp|slow(?:er|ing)|worse|declin|falling behind|"
                 r"struggl|behind)", low) and trend != "slipping" \
            and not has_escalation:
        return True
    if re.search(r"\b(?:beat|master|conquer|defeat|overcome)", low) and not tricks:
        return True
    if "relic" in low and not relics:
        return True
    if "drill" in low and not drills:
        return True
    return False


def _is_grounded(text: str, names: list) -> bool:
    """True if the reading actually reads THIS session.

    A small model asked to be encouraging will happily produce warm filler that
    would fit any child on any day. That is not a reading of these facts, so it
    is refused too: the prose has to name something from the record — the trick
    that was beaten, the drill that was fought, the relic that was earned."""
    low = text.lower()
    return any(name.lower() in low for name in names if len(name) > 3)


def _house_language(text: str) -> str:
    for pattern, replacement in _HOUSE_WORDS:
        text = pattern.sub(replacement, text)
    return text


def _ask_for_reading(facts_text: str) -> str:
    """The ONE model call in this module. It receives the finished facts and
    writes prose about them — it is never asked for a figure or a trend."""
    raw = ask_gemma(
        "TASK: parent\n"
        "A Grade 9 student is working through a maths game with an on-device "
        "tutor. In this game a 'trick' is a wrong idea that feels right, and "
        "beating a trick means two fresh check questions were answered "
        "correctly with reasoning that held up.\n"
        "THE COMPLETE RECORD of this student's progress — anything not listed "
        "here has NOT happened:\n"
        + facts_text + "\n\n"
        "Write TWO or THREE sentences to the student's mum and dad, in plain "
        "everyday language with no teaching jargon: what this record means for "
        "their child, and the one thing worth doing next.\n"
        "Rules you must not break:\n"
        "- Use NO numbers at all, in digits or in words. The parents are "
        "already looking at every count in a table beside your sentences, so "
        "your job is only to say what they mean. Name the trick, the drill or "
        "the relic itself instead of counting them.\n"
        "- Name at least one thing from the record: the trick, the drill or "
        "the relic, by the exact words used above.\n"
        "- Claim no progress, no struggle, no habit and no result that is not "
        "in the record above.\n"
        "- If the record is thin, say so plainly rather than filling it in.\n"
        "- Say 'your child' or 'them'. Do not assume a son or a daughter.\n"
        "- Warm and matter-of-fact, never alarming, and never vague praise.\n"
        "- Plain text only: no LaTeX, no dollar signs, no markdown, no emoji, "
        "no headings, no bullet points, no quotation marks.\n"
        "Reply with the sentences themselves and nothing else.",
        max_new_tokens=220)
    return _house_language(plainify(raw or "")).strip().strip('"“”\'*_` ').strip()


# ------------------------------------------------------------------ PUBLIC
def summarise(letters: list, mastered_names: list, skirmish_log: list,
              relics: list, last_score: str = "") -> dict:
    """The progress summary shown to parents on the letters-home page.

    Everything numeric is computed here from the session's own records:
    the tricks beaten and their names, how many notes went home and what each
    was about, the best and latest speed-drill score per lane and whether it
    is improving, and the relics earned. Gemma is then handed those finished
    facts and writes 'reading' — two or three sentences of interpretation for
    mum and dad. It is asked to work out no figure and is not allowed to state
    one; anything it writes that names a number is discarded unread.

    Returns:
        rows     — list of {"What", "Count", "Details"} dicts for a table
        chart    — {"Best score": {lane: n}, "Latest score": {lane: n}}, ready
                   for st.bar_chart; empty dict when no drills have been fought
        headline — one computed line summing the session up
        reading  — Gemma's prose, or a deterministic sentence built from the
                   same facts if the model is unavailable or oversteps
    """
    tricks = _dedupe(mastered_names)
    letter_facts = _letter_facts(letters)
    drills = _drill_facts(skirmish_log)
    relic_facts = _relic_facts(relics)
    trend = _overall_trend(drills)

    rows = _build_rows(tricks, letter_facts, drills, relic_facts)
    chart = _build_chart(drills)
    headline = _build_headline(tricks, letter_facts, drills, relic_facts, trend)

    facts = _facts_lines(tricks, letter_facts, drills, relic_facts, trend,
                         last_score)
    facts_text = "\n".join(f"- {line}" for line in facts)
    fallback = _fallback_reading(tricks, letter_facts, drills, relic_facts, trend)

    reading = ""
    if gemma_available():
        try:
            reading = _ask_for_reading(facts_text)
        except Exception:      # a model hiccup must never break the page
            reading = ""
        # the stub text a model-less machine returns is not a reading
        if reading.startswith("_(") or "Install Ollama" in reading:
            reading = ""
        named = (tricks + [r["name"] for r in relic_facts]
                 + [d["label"] for d in drills])
        escalated = any(b["kind"] == "escalation"
                        for b in letter_facts["breakdown"])
        if reading and (_states_a_figure(reading)
                        or not _is_grounded(reading, named)
                        or _contradicts_record(reading, tricks, drills,
                                               relic_facts, trend, escalated)):
            reading = ""
    if not reading:
        reading = fallback

    return {"rows": rows, "chart": chart, "headline": headline,
            "reading": reading}


# ------------------------------------------------------------- SMOKE TEST
if __name__ == "__main__":
    import json
    import sys

    mod = sys.modules[__name__]
    real_ask, real_available = mod.ask_gemma, mod.gemma_available

    LETTERS = [
        {"n": 1, "title": "After the quiz — adding fractions straight across",
         "body": "...", "kind": "quiz", "trick_id": "T1",
         "trick_name": "adding fractions straight across", "strand": "Number"},
        {"n": 2, "title": "Beat the trick: adding fractions straight across",
         "body": "...", "kind": "mastery", "trick_id": "T1",
         "trick_name": "adding fractions straight across", "strand": "Number"},
        {"n": 3, "title": "Still stuck on moving a sign across the equals",
         "body": "...", "kind": "escalation", "trick_id": "T2",
         "trick_name": "moving a sign across the equals", "strand": "Algebra"},
    ]
    MASTERED = ["adding fractions straight across"]
    SKIRMISH = [{"lane": "doubles", "score": 9, "streak": 4, "misses": ["7 x 8"]},
                {"lane": "doubles", "score": 12, "streak": 6, "misses": []}]
    RELICS = [{"name": "Denominator Shard",
               "power": "Common ground first, always.", "monster": "Fractis"}]

    # ---- the model is unavailable: the page still gets a full summary ----
    mod.gemma_available = lambda: False
    out = summarise(LETTERS, MASTERED, SKIRMISH, RELICS, last_score="3 of 5")
    print(json.dumps(out, indent=2))
    assert out["headline"].startswith("1 trick beaten"), out["headline"]
    assert out["chart"] == {"Best score": {"doubling and halving": 12},
                            "Latest score": {"doubling and halving": 12}}, out["chart"]
    assert len(out["rows"]) == 4, out["rows"]
    assert out["reading"] and "improving" in out["reading"], out["reading"]

    # ---- the model raises: same deterministic reading ----
    def _boom(prompt, max_new_tokens=600):
        raise RuntimeError("model down")

    mod.gemma_available = lambda: True
    mod.ask_gemma = _boom
    assert summarise(LETTERS, MASTERED, SKIRMISH, RELICS)["reading"] == \
        summarise(LETTERS, MASTERED, SKIRMISH, RELICS, "3 of 5")["reading"]

    # ---- the model invents a number: the reading is refused ----
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "Your child has beaten 7 tricks this week and scored 41 on the drills.")
    refused = summarise(LETTERS, MASTERED, SKIRMISH, RELICS, "3 of 5")["reading"]
    assert "7 tricks" not in refused, refused
    assert refused.startswith("So far"), refused

    # ---- warm filler that names none of the facts: also refused ----
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "Your child is doing well and making good progress. Keep encouraging them.")
    vague = summarise(LETTERS, MASTERED, SKIRMISH, RELICS, "3 of 5")["reading"]
    assert vague.startswith("So far"), vague

    # ---- a count spelled out is refused too: it cannot be checked ----
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "Your child has beaten three tricks with adding fractions straight "
        "across, and earned a relic. Keep going.")
    spelled = summarise(LETTERS, MASTERED, SKIRMISH, RELICS, "3 of 5")["reading"]
    assert "three tricks" not in spelled, spelled

    # ---- even a TRUE figure is refused: code prints the counts, not Gemma ----
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "Your child has beaten 1 trick, adding fractions straight across.")
    true_but_numeric = summarise(LETTERS, MASTERED, SKIRMISH, RELICS,
                                 "3 of 5")["reading"]
    assert true_but_numeric.startswith("So far"), true_but_numeric

    # ---- the model claims a trend the record does not show: refused ----
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "Your child is improving quickly on the doubling and halving drill.")
    ONE_RUN = [{"lane": "doubles", "score": 9, "streak": 4, "misses": []}]
    trendy = summarise(LETTERS, MASTERED, ONE_RUN, RELICS, "3 of 5")["reading"]
    assert "improving quickly" not in trendy, trendy

    # ---- the model behaves: its prose is used, and cleaned ----
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        '"Good news: adding fractions straight across is behind them now, and '
        'the doubling and halving drill is moving the right way. The note '
        'asking for your help is still open — it flags a learning gap around '
        '$\\frac{a}{b}$ and moving signs."')
    kept = summarise(LETTERS, MASTERED, SKIRMISH, RELICS, "3 of 5")["reading"]
    assert kept.startswith("Good news"), kept
    assert "gap" not in kept and "$" not in kept, kept
    assert "the trick that caught them" in kept, kept

    # ---- an empty session must not crash ----
    empty = summarise([], [], [], [], "")
    assert empty["chart"] == {} and empty["rows"], empty
    assert empty["headline"].startswith("Nothing to show yet"), empty["headline"]

    mod.ask_gemma, mod.gemma_available = real_ask, real_available
    print("progress.py smoke test: all assertions passed")
