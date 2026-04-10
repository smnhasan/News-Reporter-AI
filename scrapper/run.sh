#!/bin/bash
set -euo pipefail

LOGFILE="/var/log/run_scrapper.log"
exec > >(tee -a "$LOGFILE") 2>&1

echo "=== Starting Scrapper Script ==="
echo "Timestamp: $(date)"
echo "--------------------------------"

# Load conda
CONDA_BASE="$HOME/anaconda3"
if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    echo "[INFO] Sourcing conda.sh"
    source "$CONDA_BASE/etc/profile.d/conda.sh"
else
    echo "[ERROR] conda.sh not found at $CONDA_BASE/etc/profile.d/conda.sh" >&2
    exit 1
fi

# Activate conda environment
echo "[INFO] Activating conda environment: scrapper-env"
if conda activate scrapper; then
    echo "[OK] Conda environment activated"
else
    echo "[ERROR] Failed to activate conda environment: scrapper-env" >&2
    exit 1
fi

# Ensure Redis dump directory exists
REDIS_DIR="./redis"
mkdir -p "$REDIS_DIR"

# Check if Redis server is running, start if not
REDIS_PORT=6376
REDIS_PID_FILE="/var/run/redis_$REDIS_PORT.pid"
if [ -f "$REDIS_PID_FILE" ] && ps -p "$(cat $REDIS_PID_FILE)" > /dev/null; then
    echo "[INFO] Redis server already running on port $REDIS_PORT"
else
    echo "[INFO] Starting Redis server on port $REDIS_PORT"
    redis-server --port $REDIS_PORT --dbfilename dump.rdb --dir "$REDIS_DIR" --daemonize yes --pidfile $REDIS_PID_FILE
    if [ $? -eq 0 ]; then
        echo "[OK] Redis server started"
    else
        echo "[ERROR] Failed to start Redis server" >&2
        exit 1
    fi
fi

# Run Python script
echo "[INFO] Running Python scrapper"
if python -m src.main; then
    echo "[OK] Python scrapper finished successfully"
else
    echo "[ERROR] Python scrapper failed" >&2
    exit 1
fi

echo "--------------------------------"
echo "=== Scrapper Script Completed ==="

# Cronjob setup instructions (not part of the script execution)
# To schedule this script to run every day at 2 AM, add the following line to your crontab:
# 0 2 * * * /bin/bash /path/to/scrapper_cron.sh
# Use 'crontab -e' to edit the crontab and add the line above, replacing '/path/to/scrapper_cron.sh' with the actual path to this script.