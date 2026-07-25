# Kaggle notebook cells — Gemma Monsters, public via cloudflared

## FIRST: one correction to the premise you gave me

You told me to assume `gemma4` is probably not a real Ollama tag. **I checked, and that is wrong — but the underlying worry is still right, for a different reason.** Getting this right matters, so here is what I actually found:

- **`gemma4` IS a real published Ollama model**, and **`gemma4:12b` IS a real, pullable tag** (7.6 GB, 256K context). The repo's new code default will pull successfully. Real gemma4 tags are `e2b`, `e4b`, `12b`, `26b`, `31b` (plus `cloud` / `-mlx` / quant variants).
- **But `gemma4:1b` and `gemma4:27b` — which `README.md` lines 119-121 tell you to `ollama pull` — are NOT real tags.** Gemma 4 has no `1b` and no `27b`; it has `e2b`/`e4b` and `26b`/`31b`. Those two commands fail outright.
- The reason is visible in the git history: commit `47e0ebe` *"Docs only: every front-facing Gemma 3 mention now reads Gemma 4"* was a mechanical find-replace, and `f02bc8b` then pushed that rename into the code default. `gemma3:1b`→`gemma4:1b` and `gemma3:27b`→`gemma4:27b` became invalid; `gemma3:12b`→`gemma4:12b` happened to land on a tag that coincidentally exists. `docs/slides/DECK-SCRIPT.md:598` still claims the committed default is `gemma4:1b`, which is not a thing.
- Corroborating this: the repo's own CI (`.github/workflows/demo-backup.yml`) pins `gemma3:12b` **"regardless of the repo default"**, and `demo-tunnel.yml` defaults to `gemma3:4b`. The team's own working demo path never used gemma4.

**So the real Kaggle risk is not a failed pull — it is a silent timeout.** I traced it in `/home/user/gemma-without-borders/gemma_client.py`:

```python
def gemma_available() -> bool:      # line 123 — only checks the SERVER is up
    requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)   # never checks the MODEL exists
```

`ask_gemma()` (line 113) trusts that, calls `_ollama()`, and `_ollama()` does `r.raise_for_status()`. A missing model returns **404**, and `requests.HTTPError` is a subclass of `requests.RequestException`, which line 116 catches → `_stub(prompt)` → placeholder text. **Identically**, a 12B model on Kaggle's 4-core CPU blows the 120 s default `GEMMA_TIMEOUT_S`, raises `Timeout` (also a `RequestException`), and lands in the same silent stub. Either way the app looks fine and quietly shows fake AI output. Hence the hard verification cell below.

Two more gotchas I found in the same file:
- `_available` is cached process-wide (line 121). If Streamlit makes its first Gemma call before Ollama is up, it caches `False` **forever** and never rechecks. **Ollama must be serving before Streamlit starts** — the cell order below enforces this.
- `VISION_MODEL` (line 100) is a *separate* env var, `GEMMA_VISION_MODEL`, also defaulting to `gemma4:12b`. Set it too, or vision silently points at an unpulled model. `gemma3:1b` is text-only, so vision is unavailable on 1b by design.

**Recommendation:** on a Kaggle **CPU** session use `gemma3:4b` (3.3 GB — exactly what the repo's own working tunnel used). On a **T4 GPU** session `gemma4:12b` is genuinely viable and is the better demo. One variable at the top of Cell 1 switches it.

---

## Before you run anything

In the Kaggle notebook's right-hand panel: **Settings → Internet → On** (requires a phone-verified account). Nothing below works without it. If you want the T4, also set **Accelerator → GPU T4 x2**. Keep the browser tab open — the tunnel dies when the session stops.

---

### CELL 1 — Config + preflight

```python
# ── Gemma Monsters on Kaggle: config ───────────────────────────────────────
# CPU session  -> "gemma3:4b"  (3.3GB, what the repo's own demo CI used)
# T4 GPU sess. -> "gemma4:12b" (7.6GB, real tag, much better output)
# Fastest/tiny -> "gemma3:1b"  (815MB, text-only: no vision)
MODEL   = "gemma3:4b"

PORT       = 8501
TIMEOUT_S  = "300"          # generous: silent-stub protection, see verify cell
REPO       = "https://github.com/EdTechDL/gemma-without-borders.git"
BRANCH     = "claude/local-demo-cloudflare-sqha63"
APP_DIR    = "/kaggle/working/gemma-without-borders"
MODEL_DIR  = "/kaggle/temp/ollama"      # multi-GB blobs: keep OUT of /kaggle/working
LOG_DIR    = "/kaggle/temp"

import os, sys, socket, subprocess, shutil
os.makedirs(MODEL_DIR, exist_ok=True)

try:
    socket.create_connection(("github.com", 443), timeout=8).close()
    print("Internet: ON")
except OSError:
    raise SystemExit(
        "Internet is OFF. Right panel -> Settings -> Internet -> On "
        "(needs a phone-verified Kaggle account). Then re-run this cell."
    )

gpu = shutil.which("nvidia-smi") is not None
if gpu:
    subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total",
                    "--format=csv,noheader"])
    print("GPU session detected -> 'gemma4:12b' is a good choice here.")
else:
    print("CPU-only session. Keep MODEL small (gemma3:4b / gemma3:1b);")
    print("a 12B model on 4 CPU cores will time out and silently show placeholders.")

print(f"\nModel={MODEL}  port={PORT}  branch={BRANCH}")
```

### CELL 2 — Clone the branch

```python
!rm -rf {APP_DIR}
!git clone --depth 1 --branch {BRANCH} {REPO} {APP_DIR}
!cd {APP_DIR} && git log --oneline -1 && ls
```

### CELL 3 — Install Python deps

```python
!pip install -q --upgrade -r {APP_DIR}/requirements.txt
import streamlit, requests
print("streamlit", streamlit.__version__, "| requests", requests.__version__)
```

### CELL 4 — Install Ollama, serve it, pull the model

```python
import os, time, subprocess, requests

os.environ["OLLAMA_MODELS"] = MODEL_DIR      # blobs -> /kaggle/temp, not output quota
os.environ["OLLAMA_HOST"]   = "127.0.0.1:11434"

!curl -fsSL https://ollama.com/install.sh | sh

# Start the server in the BACKGROUND and wait until it answers.
# Ollama must be up before Streamlit starts: gemma_client caches
# gemma_available() once per process and never re-checks it.
srv_log = open(f"{LOG_DIR}/ollama.log", "wb")
subprocess.Popen(["ollama", "serve"], stdout=srv_log,
                 stderr=subprocess.STDOUT, env=os.environ.copy())

for i in range(60):
    try:
        requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        print(f"Ollama server up after {i}s"); break
    except requests.RequestException:
        time.sleep(1)
else:
    !tail -30 {LOG_DIR}/ollama.log
    raise SystemExit("Ollama server never came up.")

print(f"\nPulling {MODEL} (this is the slow part)...")
pull = subprocess.run(["ollama", "pull", MODEL], env=os.environ.copy())
if pull.returncode != 0:
    raise SystemExit(
        f"PULL FAILED for '{MODEL}'.\n"
        "Valid tags: gemma3:1b|4b|12b|27b  and  gemma4:e2b|e4b|12b|26b|31b\n"
        "NOTE: gemma4:1b and gemma4:27b in the README do NOT exist."
    )
print(f"Pull finished for {MODEL}")
```

### CELL 5 — VERIFY the model really loaded (do not skip)

```python
# This is the cell that stops you finding out on stage.
# The app NEVER crashes on a bad/slow model - it silently prints placeholder
# text. So we reproduce _ollama() exactly and assert on it.
import time, requests, textwrap

print("=== ollama list ===")
!ollama list

BASE = "http://127.0.0.1:11434"
names = [m["name"] for m in requests.get(f"{BASE}/api/tags", timeout=10).json().get("models", [])]
print("\nInstalled tags:", names or "(none)")
print(f"'{MODEL}' present in list:", MODEL in names)

def probe(label):
    t0 = time.time()
    r = requests.post(f"{BASE}/api/generate", json={
            "model": MODEL,
            "prompt": "Reply with exactly: OK",
            "stream": False,
            "options": {"temperature": 0, "num_predict": 16},
        }, timeout=int(TIMEOUT_S))
    return r, time.time() - t0

try:
    r1, t_cold = probe("cold")          # includes model load
    r2, t_warm = probe("warm")          # steady-state latency
except requests.Timeout:
    raise SystemExit(f"FAIL: generate exceeded {TIMEOUT_S}s. Model too big for this "
                     "session -> app will show PLACEHOLDER text. Use gemma3:4b or gemma3:1b.")

if r2.status_code == 200:
    print("\n" + "="*62)
    print(f"  PASS - '{MODEL}' IS LIVE. Real Gemma output, not placeholders.")
    print(f"  cold {t_cold:.1f}s | warm {t_warm:.1f}s | reply: "
          f"{r2.json()['response'].strip()[:40]!r}")
    print("="*62)
    if t_warm > 25:
        print(f"\n  WARNING: {t_warm:.0f}s for 16 tokens is slow. The app asks for up to")
        print("  600 tokens, so real calls may exceed GEMMA_TIMEOUT_S and fall back")
        print("  to placeholders mid-demo. Switch MODEL to gemma3:1b and re-run 4-5.")
else:
    print("\n" + "!"*62)
    print(f"  FAIL - HTTP {r2.status_code}: {r2.text[:200]}")
    print("  404 = model not pulled. The app will NOT crash - it will quietly")
    print("  show placeholder text instead of AI output. Fix MODEL and re-run 4-5.")
    print("!"*62)
    raise SystemExit("Model not usable - stopping so you notice now, not on stage.")
```

### CELL 6 — Launch Streamlit (after Ollama is confirmed up)

```python
import os, time, subprocess, requests

env = os.environ.copy()
env["GEMMA_MODEL"]        = MODEL
env["GEMMA_VISION_MODEL"] = MODEL      # separate var! defaults to gemma4:12b otherwise
env["GEMMA_TIMEOUT_S"]    = TIMEOUT_S
env["OLLAMA_URL"]         = "http://127.0.0.1:11434"

st_log = open(f"{LOG_DIR}/streamlit.log", "wb")
subprocess.Popen(
    ["streamlit", "run", "app.py",
     "--server.port", str(PORT), "--server.address", "127.0.0.1",
     "--server.headless", "true",
     "--server.enableCORS", "false",            # required behind the tunnel
     "--server.enableXsrfProtection", "false"],
    cwd=APP_DIR, env=env, stdout=st_log, stderr=subprocess.STDOUT)

for i in range(90):
    try:
        if requests.get(f"http://127.0.0.1:{PORT}/_stcore/health", timeout=2).ok:
            print(f"Streamlit healthy after {i}s (GEMMA_MODEL={MODEL})"); break
    except requests.RequestException:
        time.sleep(1)
else:
    !tail -40 {LOG_DIR}/streamlit.log
    raise SystemExit("Streamlit failed to start.")
```

### CELL 7 — Cloudflare quick tunnel + PRINT THE PUBLIC URL

```python
import re, time, subprocess, pathlib

CF = "/kaggle/temp/cloudflared"
!wget -q -O {CF} https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
!chmod +x {CF}

cf_log = f"{LOG_DIR}/cf.log"
open(cf_log, "w").close()
subprocess.Popen([CF, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{PORT}"],
                 stdout=open(cf_log, "wb"), stderr=subprocess.STDOUT)

url = None
for _ in range(60):
    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", pathlib.Path(cf_log).read_text())
    if m:
        url = m.group(0); break
    time.sleep(2)

if not url:
    !tail -40 {cf_log}
    raise SystemExit("No tunnel URL - quick tunnels are rate-limited; wait a minute and re-run.")

print("\n" + "="*62)
print("  PUBLIC DEMO URL:")
print(f"  {url}")
print("="*62)
print(f"  Serving GEMMA_MODEL={MODEL}")
print("  Keep this notebook RUNNING - the link dies when the session stops.")
```

### CELL 8 — Keep-alive (leave running during the demo)

```python
import time, requests
# Kaggle idles out an untouched session; this keeps it warm and re-checks
# that Gemma is still answering, so a mid-demo drop into placeholder text
# shows up here rather than on screen.
try:
    while True:
        try:
            ok = requests.post("http://127.0.0.1:11434/api/generate",
                               json={"model": MODEL, "prompt": "hi", "stream": False,
                                     "options": {"num_predict": 4}},
                               timeout=60).status_code == 200
        except requests.RequestException:
            ok = False
        print(time.strftime("%H:%M:%S"), url, "| gemma:", "OK" if ok else "DOWN -> placeholders",
              flush=True)
        time.sleep(120)
except KeyboardInterrupt:
    print("stopped")
```

---

## Constraints to tell your teammate

1. **Internet must be ON** in the notebook Settings panel (phone-verified account) — Cells 2, 3, 4 and 7 all fetch from the network.
2. **Kaggle CPU sessions are slow for Ollama.** `gemma3:4b` (3.3 GB) is the pragmatic pick and matches what the repo's own demo workflow shipped; `gemma3:1b` (815 MB) if you need speed over quality, accepting no vision.
3. **A T4 GPU session is much faster** and is the only place `gemma4:12b` makes sense. Set Accelerator → GPU T4 before starting.
4. **The app degrades, never crashes.** `ask_gemma()` catches every `RequestException` and returns `_stub()` placeholder text. That is a feature for robustness and a trap for demos — Cell 5 exists purely to convert that silence into a loud PASS/FAIL.
5. **Do not trust `README.md` lines 118-121.** `ollama pull gemma4:1b` and `gemma4:27b` will fail; those tags do not exist. `gemma4:12b` does.
6. Quick tunnels are ephemeral and rate-limited; the URL changes on every restart. Model blobs go to `/kaggle/temp` deliberately so they don't consume the 20 GB `/kaggle/working` output quota.

Files I read: `/home/user/gemma-without-borders/README.md`, `/home/user/gemma-without-borders/gemma_client.py`, `/home/user/gemma-without-borders/requirements.txt`, `/home/user/gemma-without-borders/.streamlit/config.toml`, `/home/user/gemma-without-borders/.github/workflows/demo-tunnel.yml`, `/home/user/gemma-without-borders/.github/workflows/demo-backup.yml`.

Sources for the model-tag verification: [gemma4 · Ollama](https://ollama.com/library/gemma4), [Tags · gemma4](https://ollama.com/library/gemma4/tags), [gemma4:12b](https://ollama.com/library/gemma4:12b), [gemma3 · Ollama](https://ollama.com/library/gemma3), [gemma3:1b](https://ollama.com/library/gemma3:1b)