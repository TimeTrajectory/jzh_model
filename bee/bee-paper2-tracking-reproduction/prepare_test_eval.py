"""Create read-only evaluation labels from BEE22 test MOT ground truth."""
from pathlib import Path
import csv
import configparser

root = Path(__file__).resolve().parent
base = root / 'data/BEE22/test'
image_list = []
for sequence in sorted(base.glob('BEE22-*')):
    info = configparser.ConfigParser()
    info.read(sequence / 'seqinfo.ini')
    width = int(info['Sequence']['imWidth'])
    height = int(info['Sequence']['imHeight'])
    labels = {}
    with (sequence / 'gt/gt.txt').open() as file:
        for row in csv.reader(file):
            frame = int(row[0]); x,y,w,h=map(float,row[2:6])
            labels.setdefault(frame, []).append(f'0 {(x+w/2)/width:.8f} {(y+h/2)/height:.8f} {w/width:.8f} {h/height:.8f}')
    image_dir = root / 'data/yolo/images/test' / sequence.name
    label_dir = root / 'data/yolo/labels/test' / sequence.name
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    for image in sorted((sequence / 'img1').glob('*.jpg')):
        frame = int(image.stem)
        dest = image_dir / image.name
        if not dest.exists(): dest.symlink_to(image)
        (label_dir / f'{image.stem}.txt').write_text('\n'.join(labels.get(frame, [])) + '\n')
        image_list.append(str(dest))
(root / 'test.txt').write_text('\n'.join(image_list) + '\n')
(root / 'bee22_test.yaml').write_text(f'path: {root}\ntrain: {root / "train.txt"}\nval: {root / "test.txt"}\nnc: 1\nnames: [bee]\n')
print(f'Prepared {len(image_list)} held-out test frames')
