#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

python -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_assets.py
.venv/bin/python prepare_dataset.py

cat <<'EOF'

Setup finished.
Activate the environment with:
  source .venv/bin/activate

Train the two paper-aligned experiments with:
  python run_experiments.py --task all --epochs 100
EOF

