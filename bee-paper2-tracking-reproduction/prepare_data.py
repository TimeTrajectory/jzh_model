"""Safely unpack BEE22 and make YOLOv5 detection labels and sequence-held-out split."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "downloads/BEE22.zip"
DATA = ROOT / "data/BEE22"
VAL_SEQUENCE = "BEE22-15"


def main() -> None:
    with ZipFile(ARCHIVE) as archive:
        for entry in archive.infolist():
            path = Path(entry.filename)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "BEE22":
                raise ValueError(f"Unsafe archive member: {entry.filename}")
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Symlink in archive: {entry.filename}")
        archive.extractall(ROOT / "data")

    train_images: list[str] = []
    val_images: list[str] = []
    statistics: dict[str, dict[str, int]] = {}
    for sequence in sorted((DATA / "train").glob("BEE22-*")):
        images = sorted((sequence / "img1").glob("*.jpg"))
        if not images:
            raise ValueError(f"Empty sequence: {sequence}")
        target = val_images if sequence.name == VAL_SEQUENCE else train_images
        split = "val" if sequence.name == VAL_SEQUENCE else "train"
        labels_dir = ROOT / "data/yolo/labels" / split / sequence.name
        images_dir = ROOT / "data/yolo/images" / split / sequence.name
        labels_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        identities: set[int] = set()
        boxes = 0
        for image in images:
            source = sequence / "labels_with_ids" / f"{image.stem}.txt"
            if not source.exists():
                raise FileNotFoundError(source)
            converted = []
            for row in source.read_text().splitlines():
                cols = row.split()
                if len(cols) != 6 or cols[0] != "0":
                    raise ValueError(f"Unexpected label: {source}: {row}")
                identity = int(cols[1])
                coords = [float(v) for v in cols[2:]]
                if identity < 1 or any(not 0 <= v <= 1 for v in coords):
                    raise ValueError(f"Invalid label: {source}: {row}")
                identities.add(identity)
                boxes += 1
                converted.append("0 " + " ".join(f"{v:.8f}" for v in coords))
            (labels_dir / f"{image.stem}.txt").write_text("\n".join(converted) + ("\n" if converted else ""))
            linked_image = images_dir / image.name
            if not linked_image.exists():
                linked_image.symlink_to(image)
            target.append(str(linked_image))
        statistics[sequence.name] = {"frames": len(images), "boxes": boxes, "identities": len(identities)}

    for name, images in (("train", train_images), ("val", val_images)):
        (ROOT / f"{name}.txt").write_text("\n".join(images) + "\n")
    (ROOT / "bee22.yaml").write_text(
        f"train: {ROOT / 'train.txt'}\nval: {ROOT / 'val.txt'}\nnc: 1\nnames: ['bee']\n"
    )
    test = {p.name: len(list((p / "img1").glob("*.jpg"))) for p in sorted((DATA / "test").glob("BEE22-*"))}
    manifest = {
        "source_archive": str(ARCHIVE),
        "validation_sequence": VAL_SEQUENCE,
        "train_frames": len(train_images),
        "validation_frames": len(val_images),
        "train_sequences": statistics,
        "test_sequences": test,
        "label_conversion": "Drop identity column from [class,id,cx,cy,w,h]; keep normalized boxes",
    }
    (ROOT / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
