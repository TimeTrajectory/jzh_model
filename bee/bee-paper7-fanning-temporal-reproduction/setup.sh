#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install -r requirements.txt
echo "Environment ready. Prepare data with: .venv/bin/python prepare_remote_dataset.py"

