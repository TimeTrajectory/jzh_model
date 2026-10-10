#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python - <<'PY'
try:
    import torch
except ImportError as exc:
    raise SystemExit('Install PyTorch for your CPU/CUDA platform first: https://pytorch.org/get-started/locally/') from exc
print('torch:', torch.__version__, 'CUDA available:', torch.cuda.is_available())
PY
python -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python - <<'PY'
import torch, ultralytics, cv2, PIL
print('torch:', torch.__version__, 'ultralytics:', ultralytics.__version__, 'opencv:', cv2.__version__, 'Pillow:', PIL.__version__)
PY
