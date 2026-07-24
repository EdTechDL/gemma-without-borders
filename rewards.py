"""
rewards.py  —  Gemma-powered creative features for GEMMA MONSTERS.

Two small pieces of on-device flavor that make the game layer feel alive:

  * forge_relic()        — after a monster's trick is mastered, Gemma forges a
                           unique collectible relic tied to the exact skill won.
  * battle_memory_line() — at an encounter, the monster speaks ONE line that
                           references the player's real history (past wins,
                           past losses, how many tries this fight has taken).

Design rules (same as the rest of the app):
  * Every function has a canned fallback in a try/except — a model failure can
    NEVER break the app.
  * Every human-facing string goes through plainify(): no LaTeX, no "$".
  * Output is parsed defensively; anything malformed falls back.
"""
from __future__ import annotations

from gemma_client import ask_gemma, plainify

RELIC_NAME_MAX_WORDS = 5
MEMORY_LINE_MAX_WORDS = 25


def _clean_line(text: str) -> str:
    """plainify + strip wrapping quotes/markdown a small model loves to add."""
    return plainify(text or "").strip().strip('"“”‘’\'*_` ').strip()


# ------------------------------------------------------------------ RELICS
def forge_relic(player_name, monster_name, trick_name, attempts, strategies_tried):
    """Forge a unique collectible relic for defeating a monster's trick.

    Returns {"name": str, "power": str}. The name is a short mythic item name
    (max 5 words); the power is one sentence, addressed to the player, tied to
    the exact skill mastered. Falls back to a canned relic on any failure.
    """
    fallback = {
        "name": f"{monster_name}'s Broken Fang",
        "power": (f"Snapped from {monster_name} the moment you conquered "
                  f"'{trick_name}', {player_name} — that trick can never bite "
                  f"you the same way again."),
    }
    try:
        strategies = ", ".join(strategies_tried) if strategies_tried else "sheer persistence"
        raw = ask_gemma(
            f"TASK: relic\n"
            f"A player named {player_name} just defeated the monster {monster_name} "
            f"by mastering this exact math skill: {trick_name}.\n"
            f"Victory took {attempts} attempt(s), won using: {strategies}.\n"
            f"Invent ONE unique collectible fantasy relic awarded for this victory.\n"
            f"Rules:\n"
            f"- The relic name is a short mythic item name, {RELIC_NAME_MAX_WORDS} words "
            f"maximum (like 'Denominator Shard' or 'Lantern of Even Signs').\n"
            f"- The power is ONE sentence, spoken directly to {player_name}, about "
            f"having BEATEN that wrong idea. Note that '{trick_name}' names the "
            f"MISTAKE the monster relies on, not a rule worth learning.\n"
            f"- STATE NO MATHEMATICAL RULE AT ALL. Do not explain how the maths "
            f"works, do not say what to multiply, divide, add or keep. A relic "
            f"that repeats the monster's own wrong idea as advice is worse than "
            f"no relic. Write about the victory, not the method.\n"
            f"- Plain text only: no dollar signs, no LaTeX, no markdown, no emoji.\n"
            f"Reply with EXACTLY two lines and nothing else:\n"
            f"NAME: <relic name>\n"
            f"POWER: <one sentence>",
            max_new_tokens=120,
        )

        name, power = "", ""
        for line in raw.splitlines():
            stripped = line.strip().lstrip("*-# ").strip()
            upper = stripped.upper()
            if upper.startswith("NAME:") and not name:
                name = stripped.split(":", 1)[1]
            elif upper.startswith("POWER:") and not power:
                power = stripped.split(":", 1)[1]

        name = _clean_line(name)
        power = _clean_line(power)
        if not name or not power:
            return fallback

        words = name.split()
        if len(words) > RELIC_NAME_MAX_WORDS:
            name = " ".join(words[:RELIC_NAME_MAX_WORDS])
        if not power.endswith((".", "!", "?")):
            power += "."
        return {"name": name, "power": power}
    except Exception:
        return fallback


# ------------------------------------------------------- BATTLE MEMORY LINES
def battle_memory_line(player_name, monster_name, memory_facts):
    """One in-character line the monster says at the encounter, grounded in the
    player's REAL history. Competitive and teasing, never mean or discouraging.

    memory_facts is a dict like:
        {"mastered_tricks": [...], "defeated_monsters": [...],
         "last_score": "3 of 5", "attempts_here": 2}

    Falls back to a canned line built straight from the facts on any failure.
    """
    facts = memory_facts or {}
    mastered = [str(t) for t in (facts.get("mastered_tricks") or [])]
    defeated = [str(m) for m in (facts.get("defeated_monsters") or [])]
    walked = int(facts.get("walked_away_here") or 0)
    last_score = str(facts.get("last_score") or "")
    try:
        attempts_here = int(facts.get("attempts_here") or 0)
    except (TypeError, ValueError):
        attempts_here = 0

    # canned fallback, composed directly from the facts
    if walked and monster_name not in defeated:
        canned = (f"You walked out on me once, {player_name}. I kept your seat "
                  f"warm.")
    elif monster_name in defeated:
        canned = (f"Back again, {player_name}? You beat me once — "
                  f"let's see if it was luck.")
    elif attempts_here > 0:
        canned = (f"Round {attempts_here + 1}, {player_name}? I admire the "
                  f"stubbornness. It won't be enough.")
    elif defeated:
        canned = (f"So you toppled {defeated[-1]}, {player_name}. Cute. "
                  f"I am not {defeated[-1]}.")
    elif last_score:
        canned = (f"{last_score} last time, {player_name}? Bring better "
                  f"numbers than that to MY lair.")
    else:
        canned = (f"Fresh meat! Welcome, {player_name} — everyone starts "
                  f"brave. Few stay that way.")

    try:
        fact_lines = []
        if mastered:
            fact_lines.append(f"- Skills the player has already mastered: {', '.join(mastered)}")
        if defeated:
            fact_lines.append(f"- Monsters the player has already defeated: {', '.join(defeated)}")
        if last_score:
            fact_lines.append(f"- The player's last quiz score: {last_score}")
        if attempts_here:
            fact_lines.append(f"- Attempts the player has already made against THIS monster: {attempts_here}")
        if walked:
            fact_lines.append(f"- Times the player walked away from THIS monster "
                              f"mid-battle: {walked} (tease this - never shame it)")
        if not fact_lines:
            fact_lines.append("- This is the player's very first battle.")

        raw = ask_gemma(
            f"TASK: taunt\n"
            f"You are {monster_name}, a playful math-game monster, greeting the "
            f"player {player_name} at the start of a battle.\n"
            f"True facts about this player's history:\n"
            + "\n".join(fact_lines) + "\n"
            f"Write ONE line {monster_name} says, referencing at least one of the "
            f"facts above (mock a past loss, or be wary of a past win).\n"
            f"Rules:\n"
            f"- {MEMORY_LINE_MAX_WORDS} words maximum, a single line.\n"
            f"- Call the player by name: {player_name}.\n"
            f"- Competitive and teasing, but NEVER mean or discouraging — the "
            f"player should smile and want to win.\n"
            f"- Do not invent facts. Plain text only: no LaTeX, no markdown, "
            f"no emoji, no quotation marks.\n"
            f"Reply with the line itself and nothing else.",
            max_new_tokens=60,
        )

        line = ""
        for candidate in raw.splitlines():
            cleaned = _clean_line(candidate)
            if cleaned:
                line = cleaned
                break
        if not line:
            return canned
        words = line.split()
        if len(words) > MEMORY_LINE_MAX_WORDS:
            line = " ".join(words[:MEMORY_LINE_MAX_WORDS]).rstrip(",;:") + "..."
        if player_name.lower() not in line.lower():
            return canned
        return line
    except Exception:
        return canned


# ------------------------------------------------------------------ SMOKE TEST
if __name__ == "__main__":
    import sys

    mod = sys.modules[__name__]
    real_ask = mod.ask_gemma
    facts = {"mastered_tricks": ["adding fractions straight across"],
             "defeated_monsters": ["Equazor"],
             "last_score": "3 of 5",
             "attempts_here": 2}

    # ---- fallback paths: the model raises ----
    def _boom(prompt, max_new_tokens=600):
        raise RuntimeError("model down")

    mod.ask_gemma = _boom
    relic = forge_relic("Amina", "Fractis", "adding fractions straight across",
                        3, ["Direct correction", "Visual walkthrough"])
    assert relic["name"] == "Fractis's Broken Fang", relic
    assert "adding fractions straight across" in relic["power"], relic
    assert "Amina" in relic["power"], relic

    line = battle_memory_line("Amina", "Fractis", facts)
    assert isinstance(line, str) and "Amina" in line, line
    line = battle_memory_line("Amina", "Equazor", facts)   # rematch branch
    assert "beat me once" in line, line
    line = battle_memory_line("Amina", "Fractis", {})      # empty facts branch
    assert "Amina" in line, line

    # ---- fallback paths: the model returns garbage ----
    mod.ask_gemma = lambda prompt, max_new_tokens=600: "hmm, interesting question!"
    relic = forge_relic("Amina", "Fractis", "adding fractions straight across", 3, [])
    assert relic["name"] == "Fractis's Broken Fang", relic
    line = battle_memory_line("Bee", "Fractis", facts)     # no player name in output
    assert "Bee" in line, line

    # ---- happy path: relic ----
    def _fake_relic(prompt, max_new_tokens=600):
        return ("NAME: Denominator Shard\n"
                "POWER: When fractions gather, Amina, this shard hums until "
                "you give them common ground first.")

    mod.ask_gemma = _fake_relic
    relic = forge_relic("Amina", "Fractis", "adding fractions straight across",
                        3, ["Direct correction"])
    assert relic["name"] == "Denominator Shard", relic
    assert relic["power"].startswith("When fractions gather, Amina"), relic
    assert len(relic["name"].split()) <= RELIC_NAME_MAX_WORDS

    # relic name gets truncated to 5 words, LaTeX gets plainified
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "NAME: The Ancient Golden Shard of Endless Denominators\n"
        "POWER: You tamed $\\frac{2}{3}$ forever, Amina")
    relic = forge_relic("Amina", "Fractis", "adding fractions straight across", 3, [])
    assert len(relic["name"].split()) == RELIC_NAME_MAX_WORDS, relic
    assert "$" not in relic["power"] and "\\frac" not in relic["power"], relic
    assert "2/3" in relic["power"], relic
    assert relic["power"].endswith("."), relic

    # ---- happy path: battle memory line ----
    def _fake_line(prompt, max_new_tokens=600):
        return '"So, Amina, slayer of Equazor... 3 of 5 last time? My waters are less forgiving."'

    mod.ask_gemma = _fake_line
    line = battle_memory_line("Amina", "Statiq", facts)
    assert "Amina" in line and "Equazor" in line, line
    assert len(line.split()) <= MEMORY_LINE_MAX_WORDS, line
    assert not line.startswith('"') and not line.endswith('"'), line

    # over-long output gets truncated to the word cap
    mod.ask_gemma = lambda p, max_new_tokens=600: (
        "Amina " + "word " * 40)
    line = battle_memory_line("Amina", "Statiq", facts)
    assert len(line.split()) <= MEMORY_LINE_MAX_WORDS, line

    mod.ask_gemma = real_ask
    print("rewards.py smoke test: all assertions passed")
