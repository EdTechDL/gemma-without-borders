"""
gemma_client.py  —  THE ONE DOOR TO GEMMA.

Everywhere the app needs AI, it calls ask_gemma(). Right now this returns clean
PLACEHOLDER text so we can build and demo the whole app WITHOUT the model running.

Later, integrating Gemma is a single change: flip USE_REAL_GEMMA = True and fill in
_real_gemma(). Nothing else in the app has to change.
"""

USE_REAL_GEMMA = False   # flip to True once Gemma is wired in (Ollama or transformers)


def ask_gemma(prompt: str, max_new_tokens: int = 600) -> str:
    """Text in, text out. The only function that talks to the model."""
    if USE_REAL_GEMMA:
        return _real_gemma(prompt, max_new_tokens)
    return _stub(prompt)


# --------------------------------------------------------------------------
# STUB — remove or ignore once Gemma is connected.
# It reads a "TASK:" and "MISCONCEPTION:" hint from the prompt so the demo
# shows something sensible in each spot Gemma will eventually fill.
# --------------------------------------------------------------------------
def _stub(prompt: str) -> str:
    task = _tag(prompt, "TASK") or "explain"
    misc = _tag(prompt, "MISCONCEPTION") or "this misconception"
    if task == "practice":
        return ("_(Gemma will generate a fresh practice question here — one that targets "
                f"'{misc}', so the student can prove they've got it.)_")
    if task == "visual":
        return ("_(Gemma will describe a visual/step-by-step explanation here — the agent "
                f"escalates to this strategy when the plain explanation didn't land for '{misc}'.)_")
    if task == "grade":
        return "PLACEHOLDER"  # the agent's evaluate step; real Gemma returns a label
    return ("_(Gemma will write a friendly, personalized explanation here: what the student "
            f"did wrong for '{misc}' and how to think about it correctly.)_")


def _tag(prompt: str, key: str) -> str:
    for line in prompt.splitlines():
        if line.strip().upper().startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return ""


# --------------------------------------------------------------------------
# REAL GEMMA — fill this in at integration time. Sketch of the two options:
#
#   Local (Edge / on-device) via Ollama:
#       import requests
#       r = requests.post("http://localhost:11434/api/generate",
#                         json={"model": "gemma3:4b", "prompt": prompt, "stream": False})
#       return r.json()["response"]
#
#   Kaggle / transformers: reuse the ask_gemma() from gemma-tutor-CLEAN.ipynb.
# --------------------------------------------------------------------------
def _real_gemma(prompt: str, max_new_tokens: int) -> str:
    raise NotImplementedError("Wire real Gemma here — see the sketch above.")
