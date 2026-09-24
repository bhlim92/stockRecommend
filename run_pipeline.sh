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

# Reads KEY=value from .env (strips quotes and CR) without depending on Python
read_env() {
    grep -E "^$1=" "$PROJECT_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d "\"'\r"
}

# Sends a Telegram alert using only bash + curl, so it still works when the venv itself is broken
notify_failure() {
    local reason="$1"
    local token chat text
    token=$(read_env TELEGRAM_BOT_TOKEN)
    chat=$(read_env TELEGRAM_CHAT_ID)
    if [ -z "$token" ] || [ -z "$chat" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Telegram not configured; failure alert not sent." >> "$LOGS_DIR/scheduler.log"
        return
    fi
    text="🚨 [stockRecommend] 일일 리포트 파이프라인 실패
서버: $(hostname) / $(date '+%Y-%m-%d %H:%M:%S %Z')
원인: $reason

--- scheduler.log 마지막 15줄 ---
$(tail -n 15 "$LOGS_DIR/scheduler.log" | cut -c1-200)"
    curl -s -m 20 -X POST "https://api.telegram.org/bot${token}/sendMessage" \
        --data-urlencode "chat_id=${chat}" \
        --data-urlencode "text=${text:0:3900}" > /dev/null 2>&1 \
        || echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Failed to send Telegram alert." >> "$LOGS_DIR/scheduler.log"
}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Stock Discovery Pipeline run on Linux..." >> "$LOGS_DIR/scheduler.log"

# Check if virtual environment exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Virtual environment not found. Creating one..." >> "$LOGS_DIR/scheduler.log"
    python3 -m venv "$VENV_DIR" >> "$LOGS_DIR/scheduler.log" 2>&1
    if [ $? -ne 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to create virtual environment." >> "$LOGS_DIR/scheduler.log"
        notify_failure "가상환경(venv) 생성 실패"
        exit 1
    fi
    "$VENV_DIR/bin/pip" install --upgrade pip >> "$LOGS_DIR/scheduler.log" 2>&1
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" >> "$LOGS_DIR/scheduler.log" 2>&1
fi

VENV_PYTHON="$VENV_DIR/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Python binary not found at $VENV_PYTHON" >> "$LOGS_DIR/scheduler.log"
    notify_failure "venv 파이썬 실행 파일 없음: $VENV_PYTHON"
    exit 1
fi

# Run the orchestrator script using venv python explicitly.
# Hard 1-hour limit so a hung network/Gemini call cannot block the run forever.
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing main.py..." >> "$LOGS_DIR/scheduler.log"
timeout 3600 "$VENV_PYTHON" "$PROJECT_DIR/main.py" >> "$LOGS_DIR/scheduler.log" 2>&1

PIPELINE_STATUS=$?
if [ $PIPELINE_STATUS -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: main.py execution failed with exit code $PIPELINE_STATUS." >> "$LOGS_DIR/scheduler.log"
    if [ $PIPELINE_STATUS -eq 124 ]; then
        notify_failure "main.py 1시간 초과(timeout)로 강제 종료"
    elif [ $PIPELINE_STATUS -eq 2 ]; then
        notify_failure "리포트는 생성됐으나 DB 색인 실패 → 웹 아카이브에 표시되지 않음"
    else
        notify_failure "main.py 비정상 종료 (exit code $PIPELINE_STATUS)"
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline executed successfully." >> "$LOGS_DIR/scheduler.log"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline run finished." >> "$LOGS_DIR/scheduler.log"
echo "--------------------------------------------------" >> "$LOGS_DIR/scheduler.log"

exit $PIPELINE_STATUS
