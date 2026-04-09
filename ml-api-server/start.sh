#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh  —  Launch the GPT-OSS FastAPI server
#
# Usage:
#   ./start.sh                     # localhost, default port 8000
#   USE_NGROK=true ./start.sh      # enable ngrok tunnel
#   PORT=8001 ./start.sh           # custom port
#
# Logs:
#   logs/server_YYYY-MM-DD.log     (written by Python's rotating handler)
#   logs/stdout_YYYY-MM-DD.log     (bash-level stdout/stderr capture)
#
# Requirements:
#   - Python 3.10+
#   - Dependencies installed:  pip install -r requirements.txt
#   - .env file configured    (copy from .env.example)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Resolve script directory (works even when called from another dir) ────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Configurable defaults (can be overridden by env vars) ────────────────────
PORT="${PORT:-8000}"
USE_NGROK="${USE_NGROK:-false}"
PYTHON="${PYTHON:-python}"         # override with: PYTHON=python3 ./start.sh
LOG_DIR="$SCRIPT_DIR/logs"
PIDFILE="$SCRIPT_DIR/logs/server.pid"

# ── Create log directory ──────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"

# ── Date-stamped stdout/stderr log ───────────────────────────────────────────
TODAY="$(date -u +%Y-%m-%d)"
STDOUT_LOG="$LOG_DIR/stdout_${TODAY}.log"

# ── Sanity checks ─────────────────────────────────────────────────────────────
if ! command -v "$PYTHON" &>/dev/null; then
  echo "[ERROR] Python interpreter not found: $PYTHON" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_DIR/.env" ]; then
  echo "[WARN]  .env not found — using .env.example defaults or environment variables."
fi

# ── Check for stale PID ───────────────────────────────────────────────────────
if [ -f "$PIDFILE" ]; then
  OLD_PID="$(cat "$PIDFILE")"
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[ERROR] Server already running with PID $OLD_PID (see $PIDFILE)."
    echo "        Run: kill $OLD_PID   to stop it first."
    exit 1
  else
    echo "[INFO]  Stale PID file removed."
    rm -f "$PIDFILE"
  fi
fi

# ── Export key env vars so Python's pydantic-settings picks them up ───────────
export PORT
export USE_NGROK

# ── Launch ────────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "  GPT-OSS Embedding Server"
echo "  Port      : $PORT"
echo "  Ngrok     : $USE_NGROK"
echo "  Log dir   : $LOG_DIR"
echo "  stdout    : $STDOUT_LOG"
echo "  Started   : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "═══════════════════════════════════════════════════════════════"

# Run in background, redirect stdout+stderr to dated log, tee to terminal
"$PYTHON" main.py 2>&1 | tee -a "$STDOUT_LOG" &
SERVER_PID=$!

echo "$SERVER_PID" > "$PIDFILE"
echo ""
echo "[INFO]  Server PID: $SERVER_PID  (stored in $PIDFILE)"
echo "[INFO]  Tailing stdout log — press Ctrl+C to detach (server keeps running)."
echo ""

# ── Tail the log so the user sees live output ─────────────────────────────────
trap 'echo -e "\n[INFO]  Detached from log. Server PID $SERVER_PID still running."; exit 0' INT
wait "$SERVER_PID"
echo "[INFO]  Server process exited."
rm -f "$PIDFILE"
