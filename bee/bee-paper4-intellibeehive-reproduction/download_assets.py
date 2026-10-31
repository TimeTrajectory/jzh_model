#!/usr/bin/env python3
"""Download pinned third-party sources and the official YOLOv7-tiny weights.

The IntelliBeeHive authors did not publish their training images or project code.
This reproduction therefore uses the public Caltech Honeybee entrance dataset as
an explicitly documented substitute. Raw data and vendored code stay ignored by
this repository; this script makes them reproducible.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YOLOV7_URL = "https://github.com/WongKinYiu/yolov7.git"
YOLOV7_COMMIT = "a207844b1ce82d204ab36d87d496728d3d2348e7"
CALTECH_URL = "https://github.com/yibingwei-1/Caltech-Honeybee.git"
CALTECH_COMMIT = "0a06fabcf23bbc75f03af4b028f8070bda8a2649"
WEIGHTS_URL = "https://github.com/WongKinYiu/yolov7/releases/download/v0.1/yolov7-tiny.pt"
WEIGHTS_SHA256 = "0fa1423606133c06362ec716029dade1169d5631e83195b75d8efa66d2ee0b77"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, check=True)


def clone_pinned(url: str, destination: Path, commit: str) -> None:
    if not (destination / ".git").exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", url, str(destination))
    current = subprocess.check_output(
        ["git", "-C", str(destination), "rev-parse", "HEAD"], text=True
    ).strip()
    if current != commit:
        run("git", "-C", str(destination), "fetch", "origin", commit)
        run("git", "-C", str(destination), "checkout", "--detach", commit)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_weights(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and sha256(path) == WEIGHTS_SHA256:
        print(f"Weights already verified: {path}")
        return
    print(f"Downloading {WEIGHTS_URL}")
    urllib.request.urlretrieve(WEIGHTS_URL, path)
    actual = sha256(path)
    if actual != WEIGHTS_SHA256:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"Weight checksum mismatch: {actual}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-dataset", action="store_true")
    args = parser.parse_args()
    clone_pinned(YOLOV7_URL, ROOT / "vendor/yolov7", YOLOV7_COMMIT)
    if not args.skip_dataset:
        clone_pinned(CALTECH_URL, ROOT / "downloads/Caltech-Honeybee", CALTECH_COMMIT)
    download_weights(ROOT / "weights/yolov7-tiny.pt")


if __name__ == "__main__":
    main()

