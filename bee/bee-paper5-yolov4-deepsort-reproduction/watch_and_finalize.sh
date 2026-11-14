#!/usr/bin/env bash
# Wait for the 6,000-iteration Darknet run, then execute the fixed evaluation protocol.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
FINAL="$ROOT/runs/train/backup/yolov4-bee_final.weights"
LOG="$ROOT/results/finalization.log"

cd "$ROOT"
echo "[$(date -Is)] waiting for $FINAL" >> "$LOG"
while [[ ! -s "$FINAL" ]]; do
  if ! pgrep -f "$ROOT/vendor/darknet/darknet detector train" >/dev/null; then
    echo "[$(date -Is)] training process disappeared before final weights were written" >> "$LOG"
    exit 1
  fi
  sleep 60
done
# Darknet creates the output before all bytes are flushed. Wait for the trainer
# to exit so validation can never open a partially written weights file.
while pgrep -f "$ROOT/vendor/darknet/darknet detector train" >/dev/null; do
  sleep 5
done
size_before="$(stat -c %s "$FINAL")"
sleep 5
size_after="$(stat -c %s "$FINAL")"
if [[ "$size_before" != "$size_after" || "$size_after" -lt 200000000 ]]; then
  echo "[$(date -Is)] final weights are incomplete: $size_before -> $size_after bytes" >> "$LOG"
  exit 1
fi
echo "[$(date -Is)] final weights found; starting evaluation" >> "$LOG"
"$ROOT/.venv/bin/python" "$ROOT/finalize_experiment.py" >> "$LOG" 2>&1
echo "[$(date -Is)] all evaluation and document generation completed" >> "$LOG"
