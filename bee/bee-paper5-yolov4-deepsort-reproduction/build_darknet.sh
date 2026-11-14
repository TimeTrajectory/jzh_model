#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MAKEFILE="$ROOT/vendor/darknet/Makefile"
python3 - "$MAKEFILE" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
s=s.replace('GPU=0','GPU=1',1).replace('CUDNN=0','CUDNN=1',1)
s=s.replace('CUDNN_HALF=0','CUDNN_HALF=1',1)
s=s.replace('LIBSO=0','LIBSO=1',1)
start=s.index('ARCH= -gencode'); end=s.index('\n\nOS :=',start)
s=s[:start]+'ARCH= -gencode arch=compute_89,code=[sm_89,compute_89]'+s[end:]
s=s.replace('-I/usr/local/cudnn/include','-I/usr/include')
s=s.replace('-L/usr/local/cudnn/lib64','-L/usr/lib/x86_64-linux-gnu')
p.write_text(s)
PY
make -C "$ROOT/vendor/darknet" -j"$(nproc)"
