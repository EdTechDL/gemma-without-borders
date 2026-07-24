#!/usr/bin/env bash
# One command to put GEMMA Monsters on a public URL for phone testing:
#   ./share.sh
# Starts the app plus a Cloudflare quick tunnel (no account needed) and prints
# the https://....trycloudflare.com link to hand to testers. Ctrl-C stops both.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8501}"

command -v streamlit >/dev/null 2>&1 || pip install -r requirements.txt

# find cloudflared, or fetch a private copy next to the repo on first run
CF="$(command -v cloudflared || true)"
if [ -z "$CF" ]; then
  CF="./.cloudflared-bin"
  if [ ! -x "$CF" ]; then
    echo "downloading cloudflared (first run only)..."
    OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
    ARCH="$(uname -m)"
    case "$ARCH" in x86_64) ARCH=amd64 ;; aarch64 | arm64) ARCH=arm64 ;; esac
    if [ "$OS" = "darwin" ]; then
      # macOS releases ship as a tarball, not a bare binary
      curl -sSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-${ARCH}.tgz" |
        tar -xz && mv cloudflared "$CF"
    else
      curl -sSL -o "$CF" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-${OS}-${ARCH}"
    fi
    chmod +x "$CF"
  fi
fi

cleanup() { kill $(jobs -p) 2>/dev/null || true; }
trap cleanup EXIT INT TERM

APP_LOG="${TMPDIR:-/tmp}/gwb-streamlit.log"
TUN_LOG="${TMPDIR:-/tmp}/gwb-tunnel.log"

streamlit run app.py --server.headless true --server.port "$PORT" >"$APP_LOG" 2>&1 &
"$CF" tunnel --url "http://localhost:$PORT" >"$TUN_LOG" 2>&1 &

echo "waiting for the tunnel..."
URL=""
for _ in $(seq 1 30); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUN_LOG" | head -1 || true)"
  [ -n "$URL" ] && break
  sleep 1
done

if [ -z "$URL" ]; then
  echo "Tunnel did not come up; see $TUN_LOG" >&2
  exit 1
fi

echo
echo "=================================================="
echo "  Share this link with the team:"
echo "  $URL"
echo "=================================================="
echo "App log: $APP_LOG   Tunnel log: $TUN_LOG"
echo "Keep this terminal open; Ctrl-C stops app + tunnel."
wait
