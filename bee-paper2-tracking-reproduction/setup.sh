#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python - <<'PY'
try:
    import torch
except ImportError as exc:
    raise SystemExit(
        "请先根据本机 CPU/CUDA 环境安装 PyTorch：https://pytorch.org/get-started/locally/"
    ) from exc
print("torch:", torch.__version__, "CUDA available:", torch.cuda.is_available())
PY

python -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
# Some managed Python images expose a partial shared Pandas install. Keep a complete
# wheel inside this project environment so YOLOv5 imports are reproducible.
python -m pip install --no-deps --force-reinstall pandas==2.3.3
python download_assets.py
