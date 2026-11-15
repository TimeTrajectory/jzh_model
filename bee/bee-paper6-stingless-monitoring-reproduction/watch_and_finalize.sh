#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; FINAL="$ROOT/runs/train/backup/yolov3-tiny-bee_final.weights"; LOG="$ROOT/results/finalization.log"
echo "[$(date -Is)] waiting for final weights" >> "$LOG"
while [[ ! -s "$FINAL" ]]; do
  if ! pgrep -f "$ROOT/vendor/darknet/darknet detector train" >/dev/null; then echo "training disappeared before final weights" >> "$LOG"; exit 1; fi
  sleep 30
done
while pgrep -f "$ROOT/vendor/darknet/darknet detector train" >/dev/null; do sleep 3; done
before="$(stat -c %s "$FINAL")"; sleep 3; after="$(stat -c %s "$FINAL")"
[[ "$before" = "$after" && "$after" -gt 10000000 ]] || { echo "incomplete final weights" >> "$LOG"; exit 1; }
"$ROOT/.venv/bin/python" "$ROOT/finalize_experiment.py" >> "$LOG" 2>&1
echo "[$(date -Is)] complete" >> "$LOG"
