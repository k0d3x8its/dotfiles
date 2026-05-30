#!/usr/bin/env bash
# HITL (Human-In-The-Loop) feedback loop template
# Use when the bug cannot be reproduced without manual interaction.
# Fill in SETUP, TRIGGER_INSTRUCTIONS, and CAPTURE_CMD, then run.
# Output is written to hitl-output.log for agent analysis.

set -euo pipefail

LOG_FILE="hitl-output.log"
ITERATION=0

# --- CONFIGURE THESE ---

SETUP() {
  # Run once before the loop starts. Examples:
  #   python app.py &                          # start a dev server in background
  #   sqlite3 dev.db < fixtures/seed.sql       # seed a database
  #   truncate -s 0 app.log                    # clear the log before capturing
  #   systemctl --user restart myservice       # restart a service
  :  # remove this line when you add real commands
}

CAPTURE_CMD() {
  # Capture observable state after each manual trigger. Examples:
  #   tail -n 50 app.log                       # last 50 lines of app log
  #   sqlite3 dev.db "SELECT * FROM events ORDER BY id DESC LIMIT 20"
  #   journalctl --user -u myservice -n 30 --no-pager
  #   cat /tmp/debug-output.txt
  #   curl -s http://localhost:8080/debug/state | python3 -m json.tool
  :  # remove this line when you add real commands
}

TRIGGER_INSTRUCTIONS="
Replace this with step-by-step instructions for the human to follow.
Be specific: which button, which URL, which input value, in what order.
"

# --- END CONFIGURATION ---

SETUP

echo "" > "$LOG_FILE"
echo "[HITL] Loop started. Log: $LOG_FILE"
echo "[HITL] Press ENTER after each manual trigger. Type 'done' to exit."
echo ""
echo "=== TRIGGER INSTRUCTIONS ==="
echo "$TRIGGER_INSTRUCTIONS"
echo "============================="
echo ""

while true; do
  read -rp "[HITL] Ready for iteration $((ITERATION + 1))? (ENTER to capture / 'done' to stop): " input
  [[ "$input" == "done" ]] && break

  ITERATION=$((ITERATION + 1))
  echo "" >> "$LOG_FILE"
  echo "=== ITERATION $ITERATION — $(date -Iseconds) ===" >> "$LOG_FILE"
  CAPTURE_CMD >> "$LOG_FILE" 2>&1
  echo "[HITL] Captured. Running total: $ITERATION iteration(s)."
done

echo ""
echo "[HITL] Loop complete. $ITERATION iteration(s) captured."
echo "[HITL] Feed $LOG_FILE back to the agent for analysis."
