#!/usr/bin/env bash
set -euo pipefail

# Deploy prediction, feature, ingestion, and UI services with tmux panes
SESSION="ddi_services"

PYTHON_BIN=${PYTHON_BIN:-}
if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  elif command -v python >/dev/null; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN="python3"
  fi
fi

if ! command -v tmux >/dev/null; then
  echo "tmux is required for deploy_services.sh"
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Session $SESSION already exists. Attach via: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" -c "$(pwd)"

tmux rename-window -t "$SESSION:0" "prediction"
tmux send-keys -t "$SESSION:0" "$PYTHON_BIN scripts/manage_services.py prediction" C-m

tmux split-window -v -t "$SESSION:0"
tmux send-keys -t "$SESSION:0.1" "$PYTHON_BIN scripts/manage_services.py feature" C-m

tmux split-window -h -t "$SESSION:0"
tmux send-keys -t "$SESSION:0.2" "$PYTHON_BIN scripts/manage_services.py ui" C-m

tmux split-window -v -t "$SESSION:0.2"
tmux send-keys -t "$SESSION:0.3" "$PYTHON_BIN scripts/manage_services.py ingestion" C-m

sleep 1
tmux select-pane -t "$SESSION:0.3"
echo "Services started in tmux session $SESSION. Attach via: tmux attach -t $SESSION"
