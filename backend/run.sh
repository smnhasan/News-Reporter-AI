#!/bin/bash

# ===============================
# Run RAG Chatbot Backend
# ===============================

# --- Conda Environment Activation ---
CONDA_BASE="$HOME/anaconda3"
if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    echo "Sourcing conda.sh"
    source "$CONDA_BASE/etc/profile.d/conda.sh"
else
    echo "ERROR: conda.sh not found at $CONDA_BASE/etc/profile.d/conda.sh" >&2
    exit 1
fi

echo "Activating conda environment: backend-env"
if conda activate news-verifyp-env; then
    echo "Conda environment activated successfully."
else
    echo "ERROR: Failed to activate conda environment: backend-env" >&2
    exit 1
fi

# --- Application Configuration ---
APP_MODULE="main:app"
HOST="0.0.0.0"
PORT="8000"
WORKERS=1
LOG_DIR="./logs"
ACCESS_LOG="$LOG_DIR/access.log"
ERROR_LOG="$LOG_DIR/error.log"
INFO_LOG="$LOG_DIR/info.log"

# Create log directory if not exists
mkdir -p $LOG_DIR

echo "Starting RAG Chatbot backend..."
echo "Logs: Access=$ACCESS_LOG, Error=$ERROR_LOG, Info=$INFO_LOG"

# Run Gunicorn with Uvicorn workers
exec gunicorn $APP_MODULE \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind $HOST:$PORT \
    --access-logfile "$ACCESS_LOG" \
    --error-logfile "$ERROR_LOG" \
    --log-file "$INFO_LOG" \
    --capture-output \
    --log-level info
    