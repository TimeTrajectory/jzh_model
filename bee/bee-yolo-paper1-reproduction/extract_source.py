"""Safely extract the verified YOLOv5 v7.0 source archive."""
from pathlib import Path
import shutil
import zipfile
from download_assets import ASSETS, sha256

ROOT = Path(__file__).resolve().parent
archive = ASSETS['yolov5'][1]
if sha256(archive) != ASSETS['yolov5'][2]:
    raise ValueError('YOLOv5 archive SHA256 mismatch')
target = ROOT / 'vendor/yolov5'
if target.exists():
    if not (target / 'val.py').is_file():
        raise ValueError('Incomplete existing vendor/yolov5 directory')
    print('YOLOv5 source directory already exists')
else:
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            name = Path(member.filename)
            if name.is_absolute() or '..' in name.parts or name.parts[0] != 'yolov5-7.0':
                raise ValueError(f'unsafe ZIP path: {member.filename}')
            dst = target.joinpath(*name.parts[1:])
            if member.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as source, dst.open('wb') as out:
                    shutil.copyfileobj(source, out)
    print(f'Extracted {target}')
