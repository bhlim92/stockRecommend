#!/bin/bash
# ==============================================================================
# Stock Discovery & Portfolio Rebalancing Scheduler Execution Script (Linux)
# ==============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/venv"
LOGS_DIR="$PROJECT_DIR/logs"

cd "$PROJECT_DIR"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Stock Discovery Pipeline run on Linux..." >> "$LOGS_DIR/scheduler.log"

# Check if virtual environment exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Virtual environment not found. Creating one..." >> "$LOGS_DIR/scheduler.log"
    python3 -m venv "$VENV_DIR" >> "$LOGS_DIR/scheduler.log" 2>&1
    if [ $? -ne 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to create virtual environment." >> "$LOGS_DIR/scheduler.log"
        exit 1
    fi
    "$VENV_DIR/bin/pip" install --upgrade pip >> "$LOGS_DIR/scheduler.log" 2>&1
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" >> "$LOGS_DIR/scheduler.log" 2>&1
fi

VENV_PYTHON="$VENV_DIR/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Python binary not found at $VENV_PYTHON" >> "$LOGS_DIR/scheduler.log"
    exit 1
fi

# Run the orchestrator script using venv python explicitly
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing main.py..." >> "$LOGS_DIR/scheduler.log"
"$VENV_PYTHON" "$PROJECT_DIR/main.py" >> "$LOGS_DIR/scheduler.log" 2>&1

PIPELINE_STATUS=$?
if [ $PIPELINE_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: main.py execution failed with exit code $PIPELINE_STATUS." >> "$LOGS_DIR/scheduler.log"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline executed successfully." >> "$LOGS_DIR/scheduler.log"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline run finished." >> "$LOGS_DIR/scheduler.log"
echo "--------------------------------------------------" >> "$LOGS_DIR/scheduler.log"

exit $PIPELINE_STATUS
