"""
gemma_client.py  —  THE ONE DOOR TO GEMMA.

Everywhere the app needs AI, it calls ask_gemma(). The model runs locally via
Ollama (http://localhost:11434) — fully on-device, no data leaves the machine.

Model selection: set the GEMMA_MODEL environment variable to switch models with
zero code changes (e.g. GEMMA_MODEL=gemma3:12b once the larger pull finishes).

If Ollama isn't running (a teammate without it installed), the app still works:
it falls back to clearly-marked placeholder text instead of crashing.
"""
import os
import re
import requests

# --------------------------------------------------------------------------
# plainify(): strip LaTeX from model output so no raw "$" / "\frac" ever
# reaches the UI. The app's house style is plain-English math ("2/3", "2^3"),
# so we convert rather than render. Applied to every human-facing string
# Gemma produces (NOT to JSON responses, which are parsed, not shown).
# --------------------------------------------------------------------------
_SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")

_SYMBOLS = {
    r"\\times": "×", r"\\cdot": "·", r"\\div": "÷", r"\\pm": "±",
    r"\\leq": "≤", r"\\le": "≤", r"\\geq": "≥", r"\\ge": "≥",
    r"\\neq": "≠", r"\\ne": "≠", r"\\approx": "≈", r"\\pi": "π",
    r"\\circ": "°", r"\\degree": "°", r"\\%": "%",
    r"\\left": "", r"\\right": "", r"\\,": " ", r"\\;": " ", r"\\!": "",
    r"\\quad": "  ", r"\\qquad": "   ",
}


def plainify(text: str) -> str:
    if not text:
        return text
    t = text
    t = t.replace("$$", "").replace("$", "")          # math delimiters
    t = re.sub(r"\\[\(\)\[\]]", "", t)                 # \( \) \[ \]
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", "", t)
    t = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"\1/\2", t)  # fractions
    t = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"√(\1)", t)
    t = re.sub(r"\\(?:text|mathrm|mathbf|mathit|operatorname)\s*\{([^{}]*)\}", r"\1", t)
    for pat, rep in _SYMBOLS.items():
        t = re.sub(pat, rep, t)

    def _sup(match):
        s = match.group(1)
        return s.translate(_SUP) if all(c in "0123456789+-=()n" for c in s) else "^" + s
    t = re.sub(r"\^\{([^{}]*)\}", _sup, t)             # ^{...}
    t = re.sub(r"\^([0-9n])", lambda m: m.group(1).translate(_SUP), t)  # ^2
    t = re.sub(r"_\{([^{}]*)\}", r"_\1", t)            # _{...}
    t = t.replace("\\\\", " ")                          # LaTeX line breaks
    t = re.sub(r"\\([a-zA-Z]+)", r"\1", t)             # drop any leftover \command
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("GEMMA_MODEL", "gemma3:1b")
# Vision needs a multimodal Gemma (4b/12b/27b - the 1b is text-only).
VISION_MODEL = os.environ.get("GEMMA_VISION_MODEL", "gemma3:12b")
TIMEOUT_S = int(os.environ.get("GEMMA_TIMEOUT_S", "120"))


def ask_gemma(prompt: str, max_new_tokens: int = 600) -> str:
    """Text in, text out. The only function that talks to the model."""
    if gemma_available():
        return _ollama(prompt, max_new_tokens)
    return _stub(prompt)


_available = None

def gemma_available() -> bool:
    """True if the local Ollama server is reachable (checked once per process)."""
    global _available
    if _available is None:
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            _available = True
        except requests.RequestException:
            _available = False
    return _available


def _ollama(prompt: str, max_new_tokens: int) -> str:
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,      # low = consistent math
                "num_predict": max_new_tokens,
            },
        },
        timeout=TIMEOUT_S,
    )
    r.raise_for_status()
    return r.json()["response"].strip()


_PREAMBLE = re.compile(
    r"(?i)(here.?s a report|here is a report|please be aware|^okay[,!]|^sure[,!]|"
    r"as requested|based (only )?on the provided facts|this response|i will|below is)")


def format_teacher_report(header_md: str, narrative: str) -> str:
    """Turn a raw Gemma report into clean, wrapping markdown: a header line, the
    prose, and a bulleted 'Try in class' section. Strips model preamble and
    splits interventions even when the model numbers them inline."""
    # 1) drop leading preamble paragraphs ("Okay, here's a report...")
    paras = [p.strip() for p in re.split(r"\n\s*\n", narrative) if p.strip()]
    while len(paras) > 1 and _PREAMBLE.search(paras[0]):
        paras.pop(0)
    narrative = "\n\n".join(paras)

    # 2) split off the interventions
    low = narrative.lower()
    if "try in class" in low:
        i = low.index("try in class")
        prose = narrative[:i].strip()
        after = narrative[i:].split(":", 1)[1] if ":" in narrative[i:] else ""
        # split on bullet/number markers wherever they appear (incl. inline)
        items = [t.strip() for t in re.split(r"\s*(?:\d+[.)]|[-–*•])\s+", after) if t.strip()]
    else:
        prose, items = narrative.strip(), []

    md = header_md.strip() + "\n\n" + prose
    if items:
        md += "\n\n**Try in class**\n\n" + "\n".join(f"- {it}" for it in items)
    return md


def vision_available() -> bool:
    """True if a multimodal Gemma is installed locally."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        names = [m["name"] for m in r.json().get("models", [])]
        return any(n.startswith(VISION_MODEL.split(":")[0]) and "1b" not in n
                   for n in names) and any(VISION_MODEL in n for n in names)
    except requests.RequestException:
        return False


def transcribe_image(image_bytes: bytes) -> str:
    """Gemma reads a photo of handwritten work - on-device, like everything
    else. It TRANSCRIBES ONLY; judging correctness stays with the grader and
    the verified bank (transcription is where vision models are weakest, so
    we never let the photo decide what is mathematically true)."""
    import base64
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": ("Transcribe this handwritten math work verbatim, one "
                            "line per step, as plain text like 2/3 + 1/4 = 3/7. "
                            "Do NOT correct any mistakes. If a line is illegible, "
                            "write [illegible]. Output only the transcription."),
                "images": [base64.b64encode(image_bytes).decode()],
            }],
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=TIMEOUT_S,
    )
    r.raise_for_status()
    return plainify(r.json()["message"]["content"].strip())


# --------------------------------------------------------------------------
# Fallback stub — used only when no local model is available, so the app
# still runs for teammates without Ollama installed.
# --------------------------------------------------------------------------
def _stub(prompt: str) -> str:
    task = _tag(prompt, "TASK") or "explain"
    misc = _tag(prompt, "MISCONCEPTION") or "this misconception"
    if task == "practice":
        return ("_(Gemma will generate a fresh practice question here — one that targets "
                f"'{misc}'. Install Ollama and pull a Gemma model to see it live.)_")
    return ("_(Gemma will write a personalized explanation here for '"
            f"{misc}'. Install Ollama and pull a Gemma model to see it live.)_")


def _tag(prompt: str, key: str) -> str:
    for line in prompt.splitlines():
        if line.strip().upper().startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return ""
