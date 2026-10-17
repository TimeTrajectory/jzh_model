"""Validate and convert the public COCO ZIP into a one-class YOLO dataset."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import re
from pathlib import Path
import shutil
import zipfile
from PIL import Image
from download_assets import sha256, ASSETS

ROOT = Path(__file__).resolve().parent
EXPECTED = {'train': (6721, 9370), 'valid': (1914, 2661), 'test': (996, 1343)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, default=ASSETS['dataset'][1])
    parser.add_argument('--output', type=Path, default=ROOT / 'dataset')
    args = parser.parse_args()
    archive, output = args.archive.resolve(), args.output.resolve()
    digest = sha256(archive)
    if digest != ASSETS['dataset'][2]:
        raise ValueError(f'Unexpected dataset SHA256: {digest}')
    if output.exists():
        raise FileExistsError(f'{output} exists; inspect it before deleting or rerunning')
    output.mkdir(parents=True)
    audit = {'archive': str(archive), 'sha256': digest, 'splits': {}}
    try:
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
            if any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):
                raise ValueError('Unsafe ZIP path')
            for split, expected in EXPECTED.items():
                ann_name = f'{split}/_annotations.coco.json'
                coco = json.loads(z.read(ann_name))
                images = coco['images']
                annotations = coco['annotations']
                if (len(images), len(annotations)) != expected:
                    raise ValueError(f'{split} counts differ from expected: {len(images)}, {len(annotations)}')
                ids = {im['id'] for im in images}
                files = [im['file_name'] for im in images]
                if len(ids) != len(images) or len(set(files)) != len(files):
                    raise ValueError(f'{split}: duplicate image ID or filename')
                zip_images = {n for n in names if n.startswith(split + '/') and n.lower().endswith(('.jpg', '.jpeg', '.png'))}
                expected_images = {f'{split}/{f}' for f in files}
                if zip_images != expected_images:
                    raise ValueError(f'{split}: COCO images do not match ZIP entries')
                ann_by_image = defaultdict(list)
                categories = Counter()
                for ann in annotations:
                    if ann['image_id'] not in ids:
                        raise ValueError(f'{split}: unknown image ID')
                    if ann['category_id'] != 1:
                        raise ValueError(f'{split}: unexpected category {ann["category_id"]}')
                    ann_by_image[ann['image_id']].append(ann)
                    categories[ann['category_id']] += 1
                image_dir = output / 'images' / split
                label_dir = output / 'labels' / split
                image_dir.mkdir(parents=True)
                label_dir.mkdir(parents=True)
                negatives = 0
                for image in images:
                    name = image['file_name']
                    if Path(name).name != name:
                        raise ValueError(f'Unsafe image filename: {name}')
                    source = f'{split}/{name}'
                    target = image_dir / name
                    with z.open(source) as inp, target.open('wb') as out:
                        shutil.copyfileobj(inp, out)
                    with Image.open(target) as pil:
                        width, height = pil.size
                        pil.verify()
                    if (width, height) != (image['width'], image['height']):
                        raise ValueError(f'{source}: image dimensions differ from COCO')
                    lines = []
                    for ann in ann_by_image[image['id']]:
                        x, y, w, h = map(float, ann['bbox'])
                        tol = 1e-6
                        if w <= 0 or h <= 0 or x < -tol or y < -tol or x + w > width + tol or y + h > height + tol:
                            raise ValueError(f'{source}: invalid bbox {ann["bbox"]}')
                        xc, yc = (x + w / 2) / width, (y + h / 2) / height
                        nw, nh = w / width, h / height
                        if any(v < 0 or v > 1 for v in (xc, yc, nw, nh)):
                            raise ValueError(f'{source}: normalized bbox out of range')
                        lines.append(f'0 {xc:.10f} {yc:.10f} {nw:.10f} {nh:.10f}')
                    if not lines:
                        negatives += 1
                    (label_dir / (Path(name).stem + '.txt')).write_text('\n'.join(lines) + ('\n' if lines else ''))
                audit['splits'][split] = {'images': len(images), 'boxes': len(annotations), 'negative_images': negatives, 'category_ids': dict(categories)}
        seen_hashes = {}
        duplicate_pairs = []
        for split in EXPECTED:
            for path in (output / 'images' / split).iterdir():
                digest = sha256(path)
                previous = seen_hashes.setdefault(digest, (split, path.name))
                if previous[0] != split:
                    duplicate_pairs.append([previous, [split, path.name]])
        audit['cross_split_exact_duplicate_pairs'] = len(duplicate_pairs)
        audit['cross_split_exact_duplicates'] = duplicate_pairs
        prefix_splits = defaultdict(set)
        unmatched_filenames = 0
        for split in EXPECTED:
            for path in (output / 'images' / split).iterdir():
                match = re.match(r'(.+?)_(?:mp4|mov)-\d+_jpg', path.name)
                if match:
                    prefix_splits[match.group(1)].add(split)
                else:
                    unmatched_filenames += 1
        audit['filename_prefix_groups_crossing_splits'] = sum(len(splits) > 1 for splits in prefix_splits.values())
        audit['filename_prefix_unmatched_images'] = unmatched_filenames
        yaml_text = f'path: {output}\ntrain: images/train\nval: images/valid\ntest: images/test\nnc: 1\nnames: [bee]\n'
        (ROOT / 'dataset.yaml').write_text(yaml_text)
        (ROOT / 'dataset_audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
        print(json.dumps(audit, indent=2, ensure_ascii=False))
    except Exception:
        shutil.rmtree(output)
        raise


if __name__ == '__main__':
    main()
