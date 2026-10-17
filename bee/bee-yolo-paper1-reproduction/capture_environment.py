"""Record the software and GPU versions used for an experiment."""
import sqlite3  # load conda ICU before Torch in this environment
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
import torch
from download_assets import ASSETS, sha256

ROOT = Path(__file__).resolve().parent
packages = ['torch', 'torchvision', 'ultralytics', 'opencv-python', 'numpy', 'Pillow',
            'polars', 'pandas', 'matplotlib', 'Flask', 'PyYAML', 'setuptools']
versions = {}
for name in packages:
    try:
        versions[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        versions[name] = None
try:
    gpu_info = subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
                                        '--format=csv,noheader'], text=True).strip()
except (FileNotFoundError, subprocess.CalledProcessError):
    gpu_info = None
result = {
    'platform': platform.platform(),
    'python': platform.python_version(),
    'cuda_runtime': torch.version.cuda,
    'cuda_available': torch.cuda.is_available(),
    'gpu': gpu_info,
    'packages': versions,
    'assets': {name: {'path': str(path), 'sha256': sha256(path)} for name, (_, path, _) in ASSETS.items() if path.is_file()},
}
(ROOT / 'environment.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(ROOT / 'environment.json')
