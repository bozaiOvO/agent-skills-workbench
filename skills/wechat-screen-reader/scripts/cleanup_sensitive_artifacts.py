#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path


DEFAULT_PATTERNS = [
    "raw*",
    "crops",
    "image_crops",
    "image_opened",
    "image_segments",
    "downloads",
    "files",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.webp",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete sensitive temporary screenshot/image/file artifacts while keeping reports by default.")
    parser.add_argument("work_dir", help="Task output directory to clean")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-ocr-json", action="store_true", help="Also delete OCR JSON files")
    args = parser.parse_args()

    root = Path(args.work_dir)
    patterns = list(DEFAULT_PATTERNS)
    if args.include_ocr_json:
        patterns.extend(["*.json", "ocr*"])

    targets = []
    for pattern in patterns:
        targets.extend(root.glob(pattern))

    for target in sorted(set(targets)):
        if not target.exists():
            continue
        print(target)
        if args.dry_run:
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


if __name__ == "__main__":
    main()
