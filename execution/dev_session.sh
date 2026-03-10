#!/usr/bin/env bash
# Start (or attach to) a tmux dev session with API + frontend panes.
# Usage: bash execution/dev_session.sh
set -euo pipefail

SESSION="product-pulse-ui"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Attaching to existing session '$SESSION'..."
  exec tmux attach -t "$SESSION"
fi

# Create session with first window named "dev"
tmux new-session -d -s "$SESSION" -n "dev" -x 220 -y 50

# Left pane: API
tmux send-keys -t "$SESSION:dev.0" "bash '$REPO_ROOT/execution/run_api.sh'" Enter

# Split vertically (right pane): Frontend
tmux split-window -h -t "$SESSION:dev"
tmux send-keys -t "$SESSION:dev.1" "bash '$REPO_ROOT/execution/run_frontend.sh'" Enter

# Even out pane widths
tmux select-layout -t "$SESSION:dev" even-horizontal

# Focus left pane
tmux select-pane -t "$SESSION:dev.0"

exec tmux attach -t "$SESSION"
