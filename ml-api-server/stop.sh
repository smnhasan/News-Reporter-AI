#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# stop.sh  —  Gracefully stop the running GPT-OSS server
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/logs/server.pid"

if [ ! -f "$PIDFILE" ]; then
  echo "[INFO]  No PID file found at $PIDFILE — server may not be running."
  exit 0
fi

PID="$(cat "$PIDFILE")"

if ! kill -0 "$PID" 2>/dev/null; then
  echo "[INFO]  PID $PID is not running. Removing stale PID file."
  rm -f "$PIDFILE"
  exit 0
fi

echo "[INFO]  Sending SIGTERM to PID $PID..."
kill -TERM "$PID"

# Wait up to 10 seconds for graceful shutdown
for i in $(seq 1 10); do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "[INFO]  Server stopped cleanly."
    rm -f "$PIDFILE"
    exit 0
  fi
  sleep 1
done

echo "[WARN]  Process did not stop within 10 s — sending SIGKILL..."
kill -KILL "$PID" 2>/dev/null || true
rm -f "$PIDFILE"
echo "[INFO]  Server force-killed."
