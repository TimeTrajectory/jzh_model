#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_assets.py
./build_darknet.sh
.venv/bin/python prepare_data.py
.venv/bin/python configure_yolov4.py
echo "Setup complete. Run: .venv/bin/python train_yolov4.py"
