#!/usr/bin/env python3
"""Download the public BEE22 archive with resume and integrity checks."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib
import requests
import time
import zipfile

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "downloads/BEE22.zip"
PARTIAL = TARGET.with_suffix(".zip.part")
PARTS = ROOT / "downloads/parts"
URL = "https://drive.usercontent.google.com/download?id=1jSlhbEItF9nOVlnNchSS3KE8HxMFYQYl&export=download&confirm=t"
EXPECTED_BYTES = 354_790_457
EXPECTED_SHA256 = "099549bef8b60f8bc35c1158354616a5b384e8308185cb84a11e8b3de8378dd7"
CHUNK = 4 * 1024 * 1024


def fetch(segment):
    start, end = segment
    path = PARTS / f"{start:012d}-{end:012d}.part"
    if path.is_file() and path.stat().st_size == end - start + 1:
        return start, path
    for attempt in range(4):
        try:
            with requests.get(
                URL,
                headers={"Range": f"bytes={start}-{end}"},
                stream=True,
                timeout=(20, 120),
            ) as response:
                response.raise_for_status()
                expected = f"bytes {start}-{end}/{EXPECTED_BYTES}"
                if response.status_code != 206 or response.headers.get("Content-Range") != expected:
                    raise RuntimeError(
                        f"unexpected range response: {response.status_code} "
                        f"{response.headers.get('Content-Range')}"
                    )
                temp = path.with_suffix(".tmp")
                with temp.open("wb") as output:
                    for block in response.iter_content(1024 * 1024):
                        if block:
                            output.write(block)
                if temp.stat().st_size != end - start + 1:
                    raise RuntimeError(f"incomplete range {start}-{end}")
                temp.replace(path)
            return start, path
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if not (TARGET.is_file() and TARGET.stat().st_size == EXPECTED_BYTES):
        PARTS.mkdir(exist_ok=True)
        segments = [
            (start, min(EXPECTED_BYTES - 1, start + CHUNK - 1))
            for start in range(0, EXPECTED_BYTES, CHUNK)
        ]
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(fetch, segment) for segment in segments]
            for completed, future in enumerate(as_completed(futures), 1):
                future.result()
                if completed % 8 == 0 or completed == len(futures):
                    print(f"downloaded ranges {completed}/{len(futures)}", flush=True)
        with PARTIAL.open("wb") as output:
            for start, end in segments:
                part = PARTS / f"{start:012d}-{end:012d}.part"
                with part.open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        output.write(block)
                part.unlink()
        if PARTIAL.stat().st_size != EXPECTED_BYTES:
            raise RuntimeError(f"incomplete download: {PARTIAL.stat().st_size}/{EXPECTED_BYTES}")
        PARTIAL.replace(TARGET)

    digest = hashlib.sha256()
    with TARGET.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"archive SHA256 mismatch: {actual} != {EXPECTED_SHA256}")
    with zipfile.ZipFile(TARGET) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"corrupt archive member: {bad}")
    print(f"complete: {TARGET} ({EXPECTED_BYTES} bytes, SHA256 {actual})")


if __name__ == "__main__":
    main()
