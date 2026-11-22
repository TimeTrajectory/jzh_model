#!/usr/bin/env python3
"""Range-read the official 17.3 GB Zenodo ZIP and store 1024x576 frames.

The complete ZIP is never stored locally. Entries are downloaded in contiguous batches,
decoded, resized to the paper's model input geometry, and written as JPEG files.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import hashlib
import io
import json
import struct
import time
import zipfile
import zlib
from pathlib import Path

import cv2
import numpy as np
import requests

ROOT = Path(__file__).resolve().parent
URL = "https://zenodo.org/api/records/15622033/files/dataset-rgb.zip/content"
REMOTE_SIZE = 17_336_965_310
REMOTE_MD5 = "d955adbbf48f4369b178090a42b9966e"
PREFIX = "dataset-rgb"


class RemoteRange(io.RawIOBase):
    def __init__(self, url=URL, size=REMOTE_SIZE):
        self.url, self.size, self.pos = url, size, 0
        self.session = requests.Session()

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos

    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        if n <= 0: return b""
        end = min(self.size - 1, self.pos + n - 1)
        response = self.session.get(
            self.url, headers={"Range": f"bytes={self.pos}-{end}"}, timeout=(30, 180)
        )
        response.raise_for_status()
        if response.status_code != 206:
            raise RuntimeError(f"server ignored Range: {response.status_code}")
        data = response.content
        self.pos += len(data)
        return data


def sequence_of(filename: str) -> str:
    return Path(filename).stem.rsplit("_", 1)[0]


def choose(infos, maximum):
    if not maximum: return infos
    groups = collections.defaultdict(list)
    for info in infos: groups[sequence_of(info.filename)].append(info)
    selected = []
    for sequence in sorted(groups):
        values = groups[sequence]
        if len(values) <= maximum: selected.extend(values); continue
        # A contiguous central clip preserves the n-1/n/n+1 relation.
        start = (len(values) - maximum) // 2
        selected.extend(values[start:start + maximum])
    return sorted(selected, key=lambda x: x.header_offset)


def request_span(session, start, end, attempts=5):
    for attempt in range(attempts):
        try:
            response = session.get(URL, headers={"Range": f"bytes={start}-{end}"}, timeout=(30, 300))
            response.raise_for_status()
            expected = end - start + 1
            if response.status_code != 206 or len(response.content) != expected:
                raise RuntimeError(f"bad range response {response.status_code}: {len(response.content)}/{expected}")
            return response.content
        except Exception:
            if attempt + 1 == attempts: raise
            time.sleep(2 ** attempt)


def decode_entry(block, block_start, info):
    at = info.header_offset - block_start
    header = struct.unpack_from("<IHHHHHIIIHH", block, at)
    if header[0] != 0x04034B50: raise ValueError(f"bad local header: {info.filename}")
    name_length, extra_length = header[-2:]
    data_at = at + 30 + name_length + extra_length
    packed = block[data_at:data_at + info.compress_size]
    if len(packed) != info.compress_size: raise ValueError(f"short entry: {info.filename}")
    if info.compress_type == zipfile.ZIP_STORED: raw = packed
    elif info.compress_type == zipfile.ZIP_DEFLATED: raw = zlib.decompress(packed, -15)
    else: raise ValueError(f"unsupported ZIP method {info.compress_type}: {info.filename}")
    if len(raw) != info.file_size: raise ValueError(f"size mismatch: {info.filename}")
    return raw


def batches(infos, count):
    # Keep gaps small. A new filename prefix starts a new contiguous video clip.
    group = []
    for info in infos:
        if group and (len(group) >= count or info.header_offset - group[-1].header_offset > 5_000_000):
            yield group; group = []
        group.append(info)
    if group: yield group


def fetch_entries(infos, callback, batch_size, parallel):
    session = requests.Session(); done = 0; total = len(infos)
    groups = iter(batches(infos, batch_size))

    def download(group):
        start = group[0].header_offset
        last = group[-1]
        end = last.header_offset + 30 + len(last.filename.encode()) + len(last.extra) + last.compress_size + 4095
        end = min(REMOTE_SIZE - 1, end)
        return start, request_span(requests.Session(), start, end)

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        pending = {}
        for _ in range(parallel):
            try:
                group = next(groups); pending[pool.submit(download, group)] = group
            except StopIteration: break
        while pending:
            future = next(concurrent.futures.as_completed(pending))
            group = pending.pop(future); start, block = future.result()
            for info in group:
                callback(info, decode_entry(block, start, info)); done += 1
            if done % 256 < len(group): print(f"processed {done}/{total}", flush=True)
            try:
                group = next(groups); pending[pool.submit(download, group)] = group
            except StopIteration: pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-per-sequence", type=int, default=0, help="0 keeps all 18,000 frames")
    parser.add_argument("--batch-entries", type=int, default=48)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--jpeg-quality", type=int, default=78)
    args = parser.parse_args()
    data_root = ROOT / "data/rgb"
    remote = RemoteRange()
    with zipfile.ZipFile(remote) as archive:
        all_infos = archive.infolist()
    by_name = {x.filename: x for x in all_infos}
    image_infos = [x for x in all_infos if "/images/" in x.filename and x.filename.endswith(".jpg")]
    image_infos = choose(image_infos, args.max_per_sequence)
    selected = {Path(x.filename).stem for x in image_infos}
    image_infos = [x for x in image_infos if not (data_root / Path(x.filename).parts[1] / "images" / Path(x.filename).name).exists()]

    def save_image(info, raw):
        parts = Path(info.filename).parts; split = parts[1]
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if image is None: raise ValueError(f"cannot decode {info.filename}")
        image = cv2.resize(image, (1024, 576), interpolation=cv2.INTER_AREA)
        out = data_root / split / "images" / Path(info.filename).name
        out.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(out), image, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality]):
            raise OSError(out)

    fetch_entries(image_infos, save_image, args.batch_entries, args.parallel)
    label_infos = [x for x in all_infos if "/labels/" in x.filename and x.filename.endswith(".txt") and Path(x.filename).stem in selected and not (data_root / Path(x.filename).parts[1] / "labels" / Path(x.filename).name).exists()]
    labels_found = set()

    def save_label(info, raw):
        parts = Path(info.filename).parts; split = parts[1]; labels_found.add((split, Path(info.filename).stem))
        out = data_root / split / "labels" / Path(info.filename).name
        out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(raw)

    fetch_entries(label_infos, save_label, max(args.batch_entries, 256), args.parallel)
    rows = []; counts = {}
    for split in ("train", "val"):
        images = sorted((data_root / split / "images").glob("*.jpg"))
        boxes = 0; negatives = 0
        labels_dir = data_root / split / "labels"; labels_dir.mkdir(parents=True, exist_ok=True)
        for image in images:
            label = labels_dir / f"{image.stem}.txt"
            if not label.exists(): label.write_text("")
            n = sum(bool(x.strip()) for x in label.read_text().splitlines())
            boxes += n; negatives += n == 0; rows.append((split, image.name, n))
        counts[split] = {"images": len(images), "boxes": boxes, "negative_images": negatives,
                         "sequences": dict(collections.Counter(sequence_of(x.name) for x in images))}
    yaml = f"path: {data_root.resolve()}\ntrain: train/images\nval: val/images\nnames:\n  0: fanning_bee\n"
    (ROOT / "dataset_rgb.yaml").write_text(yaml)
    audit = {"source_url": URL, "source_record": "10.5281/zenodo.15622033",
             "remote_bytes": REMOTE_SIZE, "remote_md5": REMOTE_MD5,
             "processing": f"resize 1920x1080 to 1024x576, JPEG quality {args.jpeg_quality}",
             "max_per_sequence": args.max_per_sequence, "counts": counts}
    digest = hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()
    audit["selected_manifest_sha256"] = digest
    (ROOT / "data/dataset_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__": main()

