"""Download and verify the public assets used by the reproduction."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import requests


ROOT = Path(__file__).resolve().parent
ASSETS = {
    "dataset": (
        "https://www.kaggle.com/api/v1/datasets/download/birdy654/bee-detection-in-the-wild",
        ROOT / "downloads/bee-detection-in-the-wild.zip",
        "0567b37cc0cecccbbe1a0186173a05e9f1a7897be00c3c107a2f7b6345c3fdca",
    ),
    "author": (
        "https://raw.githubusercontent.com/AjayJohnAlex/Bee_Detection/main/models/custom_yolov5m.pt",
        ROOT / "weights/author_custom_yolov5m.pt",
        "27637d1a36f0deb0169baf11143b9d73d12052fb96a6b50c65508160b78f30eb",
    ),
    "yolov5_pretrained": (
        "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt",
        ROOT / "weights/yolov5m.pt",
        "61d933360ba5a7733a36764996c800287d973889d875227f5beedd2473a97a56",
    ),
    "yolo26_pretrained": (
        "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26m.pt",
        ROOT / "weights/yolo26m.pt",
        "401cea9ab23ad19246ff7744859816bc599f350e93c9dd30367b6f0a0745d0b7",
    ),
    "yolov5": (
        "https://github.com/ultralytics/yolov5/archive/refs/tags/v7.0.zip",
        ROOT / "downloads/yolov5-v7.0.zip",
        "a40568a7979c4b27195d198987e49610de86b038b044f2521f5515455571f852",
    ),
    "author_example_video": (
        "https://raw.githubusercontent.com/AjayJohnAlex/Bee_Detection/main/upload_data/honey_bee_video1.mp4",
        ROOT / "downloads/author_example_video.mp4",
        "c33d84b028dc075308168e344cd0258004ae2514aec70e5cc85172e4ee73ef55",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str) -> None:
    url, target, expected = ASSETS[name]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and sha256(target) == expected:
        print(f"{name}: verified existing {target}", flush=True)
        return
    partial = target.with_suffix(target.suffix + ".part")
    with requests.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        with partial.open("wb") as file:
            size = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
                    size += len(chunk)
                    if size // (50 * 1024 * 1024) != (size - len(chunk)) // (50 * 1024 * 1024):
                        print(f"{name}: {size // (1024 * 1024)} MiB", flush=True)
    actual = sha256(partial)
    if actual != expected:
        partial.unlink()
        raise ValueError(f"{name} SHA256 mismatch: {actual} != {expected}")
    partial.replace(target)
    print(f"{name}: verified {target} ({target.stat().st_size} bytes)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", nargs="*")
    args = parser.parse_args()
    for item in args.assets or ASSETS:
        if item not in ASSETS:
            parser.error(f"unknown asset: {item}")
        download(item)
