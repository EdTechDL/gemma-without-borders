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
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("GEMMA_MODEL", "gemma3:1b")
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
