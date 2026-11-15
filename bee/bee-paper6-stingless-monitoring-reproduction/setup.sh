#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$ROOT"
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_assets.py
bash build_darknet.sh
.venv/bin/python configure_yolov3_tiny.py
if [[ -d ../bee-paper2-tracking-reproduction/data/yolo || -f downloads/BEE22.zip ]]; then
  .venv/bin/python prepare_data.py
  echo "Setup complete. Train with: .venv/bin/python train_yolov3.py"
else
  echo "Code and model assets are ready. BEE22 is not stored in Git."
  echo "Next: .venv/bin/python download_bee22.py && .venv/bin/python prepare_data.py"
fi

