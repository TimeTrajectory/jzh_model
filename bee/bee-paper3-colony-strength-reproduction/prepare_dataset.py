"""Extract LabelMe annotations and create a deterministic YOLO 60/20/20 split."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
from collections import Counter
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from PIL import Image


ROOT = Path(__file__).resolve().parent
CLASS_NAMES = ["WB no pollen", "WB pollen", "Drone bee"]


def normalized_label(value: str) -> int:
    label = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
    if "drone" in label:
        return 2
    if "pollen" in label and not any(token in label for token in ("no pollen", "without pollen", "non pollen", "nonpollen")):
        return 1
    if "worker" in label or label.startswith("wb") or "bee" in label:
        return 0
    raise ValueError(f"Unknown class label: {value!r}")


def safe_extract(archive: Path, destination: Path) -> None:
    marker = destination / ".extracted"
    if marker.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as zipped:
        for info in zipped.infolist():
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Unsafe archive member: {info.filename}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Symlink archive member: {info.filename}")
        zipped.extractall(destination)
    marker.write_text("ok\n")


def extract_nested_archives(root: Path) -> None:
    """Expand ZIP files bundled inside the official supplement."""
    processed: set[Path] = set()
    while True:
        pending = [path for path in root.rglob("*.zip") if path not in processed]
        if not pending:
            return
        for archive in pending:
            processed.add(archive)
            destination = archive.parent / f"{archive.stem}_extracted"
            safe_extract(archive, destination)


def find_image(annotation: Path, payload: dict) -> Path:
    candidates = []
    image_path = payload.get("imagePath")
    if image_path:
        candidates.append(annotation.parent / Path(str(image_path)).name)
    candidates.extend(annotation.with_suffix(suffix) for suffix in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    matches = [p for p in annotation.parent.iterdir() if p.is_file() and p.stem == annotation.stem and p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"No unique image for {annotation}")


def convert(annotation: Path, payload: dict, width: int, height: int) -> tuple[list[str], Counter[int]]:
    rows: list[str] = []
    counts: Counter[int] = Counter()
    for shape in payload.get("shapes", []):
        points = shape.get("points") or []
        if len(points) < 2:
            continue
        class_id = normalized_label(str(shape.get("label", "")))
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        x1, x2 = max(0.0, min(xs)), min(float(width), max(xs))
        y1, y2 = max(0.0, min(ys)), min(float(height), max(ys))
        if x2 <= x1 or y2 <= y1:
            continue
        cx = (x1 + x2) / (2 * width)
        cy = (y1 + y2) / (2 * height)
        bw = (x2 - x1) / width
        bh = (y2 - y1) / height
        rows.append(f"{class_id} {cx:.8f} {cy:.8f} {bw:.8f} {bh:.8f}")
        counts[class_id] += 1
    return rows, counts


def stable_name(annotation: Path, raw: Path, image: Path) -> str:
    relative = annotation.relative_to(raw).as_posix()
    digest = hashlib.sha1(relative.encode()).hexdigest()[:10]
    return f"{annotation.stem}_{digest}{image.suffix.lower()}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=ROOT / "downloads/supplement.zip")
    parser.add_argument("--seed", type=int, default=50)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    raw = ROOT / "data/raw"
    output = ROOT / "data/yolo"
    safe_extract(args.archive.resolve(), raw)
    extract_nested_archives(raw)
    annotations = sorted(path for path in raw.rglob("*.json") if path.name.lower() not in {"metadata.json", "dataset_manifest.json"})
    labelme: list[tuple[Path, dict, Path]] = []
    skipped = []
    for annotation in annotations:
        try:
            payload = json.loads(annotation.read_text(encoding="utf-8-sig"))
            if not isinstance(payload.get("shapes"), list):
                continue
            image = find_image(annotation, payload)
            labelme.append((annotation, payload, image))
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError) as error:
            skipped.append({"annotation": str(annotation), "reason": str(error)})
    if not labelme:
        raise RuntimeError(f"No LabelMe image/annotation pairs found below {raw}")

    rng = random.Random(args.seed)
    rng.shuffle(labelme)
    count = len(labelme)
    train_end = int(count * 0.60)
    val_end = train_end + int(count * 0.20)
    assignments = (["train"] * train_end + ["val"] * (val_end - train_end) + ["test"] * (count - val_end))

    if output.exists() and args.force:
        shutil.rmtree(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output exists; use --force to rebuild: {output}")

    statistics = {split: {"images": 0, "boxes": Counter()} for split in ("train", "val", "test")}
    records = []
    for (annotation, payload, image), split in zip(labelme, assignments):
        width = int(payload.get("imageWidth") or 0)
        height = int(payload.get("imageHeight") or 0)
        if width <= 0 or height <= 0:
            with Image.open(image) as opened:
                width, height = opened.size
        rows, counts = convert(annotation, payload, width, height)
        name = stable_name(annotation, raw, image)
        image_target = output / "images" / split / name
        label_target = output / "labels" / split / f"{Path(name).stem}.txt"
        image_target.parent.mkdir(parents=True, exist_ok=True)
        label_target.parent.mkdir(parents=True, exist_ok=True)
        image_target.symlink_to(image.resolve())
        label_target.write_text("\n".join(rows) + ("\n" if rows else ""))
        statistics[split]["images"] += 1
        statistics[split]["boxes"].update(counts)
        records.append({"source": str(annotation.relative_to(raw)), "image": str(image.relative_to(raw)), "split": split, "output": name, "boxes": sum(counts.values())})

    yaml = ROOT / "dataset.yaml"
    yaml.write_text(
        f"path: {output}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: WB no pollen\n  1: WB pollen\n  2: Drone bee\n"
    )
    serial_stats = {
        split: {"images": values["images"], "boxes": {CLASS_NAMES[key]: value for key, value in sorted(values["boxes"].items())}}
        for split, values in statistics.items()
    }
    manifest = {
        "paper_protocol": "random frame split 60/20/20",
        "seed_not_reported_by_paper": args.seed,
        "classes": CLASS_NAMES,
        "total_pairs": count,
        "statistics": serial_stats,
        "skipped": skipped,
        "records": records,
    }
    (ROOT / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in manifest.items() if key != "records"}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

