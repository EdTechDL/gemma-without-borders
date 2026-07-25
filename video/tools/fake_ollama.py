"""Canned Ollama stand-in for demo-footage capture.

Serves the two endpoints gemma_client.py uses. Every response is dispatched on
the TASK: tag the app embeds in its prompts, shaped exactly the way each call
site parses it, and written to read like a good Gemma answer on camera.
"""
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 11434

# Practice variants cycle so repeat checks never show the same question twice.
# All the same kind as the seed (simplify a(bx - c) - dx); option texts are
# what real students produce, and the sign-snare option is always present.
VARIANTS = [
    {"stem": "5(3x - 2) - 8x",
     "question": "Simplify the expression: 5(3x - 2) - 8x.",
     "options": {"A": "23x - 10", "B": "7x - 10", "C": "-7x + 10", "D": "7x - 2"},
     "correct": "B"},
    {"stem": "4(2x - 3) - 6x",
     "question": "Simplify the expression: 4(2x - 3) - 6x.",
     "options": {"A": "14x - 12", "B": "2x - 3", "C": "2x - 12", "D": "-2x + 12"},
     "correct": "C"},
    {"stem": "6(2x - 1) - 9x",
     "question": "Simplify the expression: 6(2x - 1) - 9x.",
     "options": {"A": "3x - 6", "B": "21x - 6", "C": "3x - 1", "D": "-3x + 6"},
     "correct": "A"},
]
STATE = {"practice": 0}


def tag(prompt, key):
    for line in prompt.splitlines():
        if line.strip().upper().startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return ""


def respond(prompt):
    task = tag(prompt, "TASK").lower()
    trick = tag(prompt, "TRICK") or "the wrong idea"

    if task == "explain":
        if "mental-math snare" in prompt:
            return ("Warrior, halve one number and double the other before you strike - "
                    "16 x 25 becomes 8 x 50, and the blade falls clean. Keep the easy "
                    "half in your head and the battle is already won.")
        return (
            "Here is what happened, and it is a very common slip. When you "
            "distribute 3(2x - 4) you get 6x - 12 - that part was right. The snare "
            "is in the next step: the - 5x has to be SUBTRACTED from 6x, not added "
            "to it. Adding gives 11x, but the verified solution keeps the sign: "
            "6x - 5x = x, so the answer is x - 12.\n\n"
            "The rule, once: a minus sign in front of a term travels with that term "
            "everywhere it goes. Before you combine like terms, read each term WITH "
            "its sign - 6x and -5x - and only then combine. Try whispering the sign "
            "out loud as you write each term; it feels silly and it works."
        )

    if task == "practice":
        v = VARIANTS[STATE["practice"] % len(VARIANTS)]
        STATE["practice"] += 1
        return json.dumps({
            "question": v["question"], "options": v["options"],
            "correct": v["correct"], "targets": trick,
        })

    if task == "solve":
        for v in VARIANTS:
            if v["stem"] in prompt:
                return v["correct"]
        return "B"

    if task == "grade":
        return "RESOLVED"

    if task == "react":
        if "thin or missing" in prompt:
            return ("Did it in your head, did you? The citadel counts reasoning it can "
                    "read, not luck it cannot - show the steps and the streak will follow.")
        if "still caught" in prompt or "was wrong" in prompt:
            return ("You added 6x and 5x again - that minus sign is still riding the 5x, "
                    "and it does not let go just because the step feels familiar.")
        return ("Keeping the minus with the 5x before combining - that is exactly the "
                "habit that beats this monster. The citadel remembers reasoning like that.")

    if task == "choose":
        m = re.search(r"<one of: ([^>]+)>", prompt)
        name = (m.group(1).split(",")[0].strip() if m else "a concrete example")
        return json.dumps({
            "strategy": name,
            "why": ("Their own words show the rule was memorized rather than pictured, "
                    "so showing it with real numbers should make it land."),
        })

    if task == "parent":
        return (
            "Tonight's battle was about simplifying expressions, and one specific idea "
            "kept getting in the way: when a minus sign sits in front of a term, it has "
            "to travel with that term. Given 3(2x - 4) - 5x, the 6x and the 5x were "
            "added instead of subtracted. That is not carelessness - it is a rule that "
            "feels right until someone shows you why it is not. After two guided rounds "
            "the last answer came with the sign handled correctly and the reasoning "
            "written out in full.\n\n"
            "Try at home:\n"
            "1. Ask them to read an expression out loud with the signs attached - "
            "'six x, minus five x' - before combining anything.\n"
            "2. Give them 4(2x - 3) - 6x on paper and ask only for the first step, "
            "nothing more.\n"
            "3. Ask them to explain to YOU why 6x - 5x is x, not 11x - teaching it "
            "is the strongest check there is."
        )

    if task == "coach":
        return (
            "Every miss in that battle was a doubling chain that broke at the third "
            "double - the pattern is fatigue at 8x, not the doubling itself. The snare "
            "that fixes it: double, then double, then STOP and say the number you are "
            "holding out loud before the last double. Saying it pins the number down "
            "so the final step starts from solid ground.\n"
            "Mini drill: 1) 6 x 8   2) 7 x 8   3) 9 x 8"
        )

    if task == "relic":
        return ("NAME: Lantern of Even Signs\n"
                "POWER: Carry this light, Maya - the trap that once turned your minus "
                "signs against you shattered the moment you saw through it.")

    if task == "taunt":
        m = re.search(r"player ([A-Za-z0-9 _'-]+?) at the start", prompt)
        name = (m.group(1).strip() if m else "Challenger")
        return f"Back again, {name}? My signs have been sharpening since your last visit."

    return ("The agent looked at this battle, found the one idea doing the damage, "
            "and lined up the next lesson to strike exactly there.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/tags"):
            self._send({"models": [{"name": "gemma4:12b"}]})
        else:
            self._send({})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if self.path.startswith("/api/generate"):
            self._send({"response": respond(data.get("prompt", ""))})
        elif self.path.startswith("/api/chat"):
            self._send({"message": {"content": "2/3 + 1/4 = 3/7"}})
        else:
            self._send({})


if __name__ == "__main__":
    print(f"fake ollama on :{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
