"""
selection.py  —  ONE rule for choosing a follow-up question.

Every follow-up in this app has the same job: give the student another go at
the ONE idea that just caught them. The study guide's "now you try", the
mastery loop's check question, and the printable sheet a parent works through
all need it, and each used to answer it separately.

They drifted, in the way duplicated logic does. Every version ended with a
generous fallback so that a question always came back, and the fallbacks were
where the harm lived:

  * "any unused item" reached across strands entirely. Data holds five items,
    a battle uses all five, and every follow-up after that was a Number
    question. A student sent to practise medians was handed exponents.
  * "any unused item from the same strand" looks disciplined and is not. Slope
    from two points and the distributive property are both Algebra; percent of
    a number and the exponent laws are both Number. Same strand, different
    idea, and a student who just got caught by one is not helped by the other.

So the rule here is narrower than either, and it is the only rule:

  1. an unused item carrying the SAME snare       - exactly the idea, ground truth key
  2. an unused item carrying a SIBLING snare      - the same idea at another depth
                                                    (NUM-6 and NUM-6b are one idea)
  3. an unused item carrying the same snare NAME  - the bank names an idea more
                                                    consistently than it ids it
  4. nothing

Returning nothing is a real answer. The caller then writes a question under
audit, or stops and says so. Neither is as bad as practising the wrong thing.
"""
from __future__ import annotations


def snare_family(snare_id) -> str:
    """NUM-6 and NUM-6b are the same idea at two depths, so they share a family.
    The trailing letter is the depth marker used throughout the bank."""
    return str(snare_id or "").rstrip("abcdefghijklmnopqrstuvwxyz")


def snare_key(name) -> str:
    """Two items can describe the same idea under different ids: the bank holds
    105 ids but only 109 names, and 'Median as midpoint of extremes' is carried
    by two items whose ids differ. The name is the better identity, so it is
    matched too, normalised so spacing and case cannot split one idea in two."""
    return " ".join(str(name or "").lower().split())


def _snare_ids(item: dict) -> set:
    return {o.get("trick_id") for o in item.get("options", []) if o.get("trick_id")}


def _snare_names(item: dict) -> set:
    return {snare_key(o.get("trick_name")) for o in item.get("options", [])
            if o.get("trick_name")}


def on_idea_pool(questions, snare_id, used_ids, snare_name=None, topic=None) -> list:
    """Every unused item that works this idea, closest first.

    When a topic is given, it is a HARD filter, not a preference. The same wrong
    idea is tagged on questions about solving equations and about y-intercepts,
    because a sign can be slipped in either - so without the topic the closest
    match by tag can still be the wrong lesson entirely.
    """
    used = set(used_ids or ())
    family = snare_family(snare_id)
    want_name = snare_key(snare_name)
    want_topic = snare_key(topic)
    exact, sibling, by_name = [], [], []
    for q in questions or []:
        if q.get("id") in used:
            continue
        if want_topic and snare_key(q.get("topic")) != want_topic:
            continue
        ids = _snare_ids(q)
        if snare_id and snare_id in ids:
            exact.append(q)
        elif family and any(snare_family(t) == family for t in ids):
            sibling.append(q)
        elif want_name and want_name in _snare_names(q):
            by_name.append(q)
    return exact + sibling + by_name


def next_on_idea(questions, snare_id, used_ids, snare_name=None, topic=None):
    """The next verified question on this idea, or None if the bank is out.

    None is not a failure to handle quietly - it is the signal to write one
    under audit, or to tell the student the bank has nothing further.
    """
    pool = on_idea_pool(questions, snare_id, used_ids, snare_name, topic)
    return pool[0] if pool else None
