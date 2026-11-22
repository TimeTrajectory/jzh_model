#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$ROOT"
mkdir -p results
while [[ ! -f data/dataset_audit.json ]]; do sleep 30; done
python3 - <<'PY'
import json
d=json.load(open('data/dataset_audit.json'))
assert d['counts']['train']['images']==14400,d
assert d['counts']['val']['images']==3600,d
boxes=d['counts']['train']['boxes']+d['counts']['val']['boxes']
assert boxes==57598,d
print('FULL_DATASET_OK',d['counts'],'archive_box_count',boxes,'paper_text_box_count',57597)
PY
for encoding in rgb tsg tem; do
  run_dir="runs/train/fast_yolo11n_${encoding}"
  if [[ ! -f "$run_dir/weights/best.pt" ]]; then
    .venv/bin/python train.py "$encoding" --model weights/yolo11n.pt --epochs 50 --batch 32 --workers 8 --patience 15 --name "fast_yolo11n_${encoding}" 2>&1 | tee "results/train_${encoding}.log"
  else
    echo "TRAINING_CHECKPOINT_EXISTS $encoding; skip retraining" | tee -a "results/train_${encoding}.log"
  fi
  .venv/bin/python evaluate.py "$encoding" --weights "$run_dir/weights/best.pt" --batch 32 --workers 0 2>&1 | tee "results/eval_${encoding}.log"
done
.venv/bin/python update_results.py
if [[ -f generate_documents.py ]]; then .venv/bin/python generate_documents.py; fi
echo "PAPER7_PIPELINE_COMPLETE $(date --iso-8601=seconds)" | tee results/completion.txt

