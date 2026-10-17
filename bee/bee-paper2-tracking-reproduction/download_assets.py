"""Download and verify the fixed YOLOv5 source and pretrained detector weights."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path
from zipfile import ZipFile

import requests

ROOT = Path(__file__).resolve().parent
ASSETS = {
    "yolov5_source": (
        "https://github.com/ultralytics/yolov5/archive/refs/tags/v7.0.zip",
        ROOT / "downloads/yolov5-v7.0.zip",
        "a40568a7979c4b27195d198987e49610de86b038b044f2521f5515455571f852",
    ),
    "yolov5s_weights": (
        "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt",
        ROOT / "weights/yolov5s-v7.0.pt",
        "8b3b748c1e592ddd8868022e8732fde20025197328490623cc16c6f24d0782ee",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(name: str) -> Path:
    url, target, expected = ASSETS[name]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha256(target) == expected:
        print(f"{name}: verified existing {target}")
        return target
    partial = target.with_suffix(target.suffix + ".part")
    with requests.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        with partial.open("wb") as output:
            for block in response.iter_content(1024 * 1024):
                if block:
                    output.write(block)
    actual = sha256(partial)
    if actual != expected:
        partial.unlink()
        raise ValueError(f"{name} SHA256 mismatch: {actual} != {expected}")
    partial.replace(target)
    print(f"{name}: verified {target}")
    return target


def extract_yolov5(archive: Path) -> None:
    target = ROOT / "vendor/yolov5"
    if (target / "train.py").is_file():
        print(f"YOLOv5 source already exists: {target}")
        return
    with ZipFile(archive) as zip_file:
        for member in zip_file.infolist():
            source = Path(member.filename)
            if source.is_absolute() or ".." in source.parts or source.parts[0] != "yolov5-7.0":
                raise ValueError(f"unsafe ZIP path: {member.filename}")
            destination = target.joinpath(*source.parts[1:])
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zip_file.open(member) as input_file, destination.open("wb") as output_file:
                    shutil.copyfileobj(input_file, output_file)
    print(f"Extracted {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    archive = download("yolov5_source")
    extract_yolov5(archive)
    if not args.source_only:
        download("yolov5s_weights")


if __name__ == "__main__":
    main()
