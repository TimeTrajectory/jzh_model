"""Inspect the official supplement without extracting untrusted paths."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", nargs="?", type=Path, default=ROOT / "downloads/supplement.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "archive_manifest.json")
    args = parser.parse_args()

    archive = args.archive.resolve()
    suffixes: Counter[str] = Counter()
    roots: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    total_uncompressed = 0
    with ZipFile(archive) as zipped:
        for info in zipped.infolist():
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Unsafe archive member: {info.filename}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"Symlink archive member: {info.filename}")
            if info.is_dir():
                continue
            suffix = member.suffix.lower() or "<none>"
            suffixes[suffix] += 1
            roots[member.parts[0] if member.parts else "<root>"] += 1
            examples.setdefault(suffix, [])
            if len(examples[suffix]) < 8:
                examples[suffix].append(info.filename)
            total_uncompressed += info.file_size

    manifest = {
        "archive": str(archive),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": file_sha256(archive),
        "uncompressed_bytes": total_uncompressed,
        "files_by_suffix": dict(suffixes.most_common()),
        "files_by_top_level": dict(roots.most_common()),
        "examples": examples,
    }
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

