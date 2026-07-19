#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

AUTOMATION_ROOT = Path(os.environ.get('AUTOMATION_CENTER_ROOT', '/Users/jinbo/AutomationCenter'))
if str(AUTOMATION_ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(AUTOMATION_ROOT / 'scripts'))

from storage_paths import load_storage_paths

PLACEHOLDER = '【无有效语音识别结果】'
TEMP_FILE_PREFIXES = ('._',)
TEMP_FILE_MARKERS = ('.~lock',)
RESERVED_VOLUME_DIRS = {'Data', 'Log', 'Cache', 'Temp', '整理输出_按年份热度'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Replace zero-byte transcript files with a placeholder marker.')
    parser.add_argument(
        '--volume-root',
        type=Path,
        default=load_storage_paths().douyin_downloads_root,
    )
    parser.add_argument('--folder', dest='folders', action='append', type=Path, default=[])
    return parser.parse_args()


def is_temporary_file(path: Path) -> bool:
    return path.name.startswith(TEMP_FILE_PREFIXES) or any(marker in path.name for marker in TEMP_FILE_MARKERS)


def iter_target_folders(volume_root: Path, folders: list[Path]) -> list[Path]:
    if folders:
        return [folder.expanduser().resolve() for folder in folders if folder.expanduser().resolve().is_dir()]
    result: list[Path] = []
    for path in sorted(volume_root.expanduser().resolve().iterdir()):
        if not path.is_dir() or path.name in RESERVED_VOLUME_DIRS or is_temporary_file(path):
            continue
        result.append(path)
    return result


def normalize_folder(folder: Path) -> int:
    updated = 0
    for path in sorted(folder.iterdir()):
        if not path.is_file() or is_temporary_file(path):
            continue
        if path.suffix.lower() != '.txt':
            continue
        if path.stat().st_size != 0:
            continue
        path.write_text(PLACEHOLDER, encoding='utf-8')
        updated += 1
        print(f'[FIX] {path}')
    return updated


def main() -> int:
    args = parse_args()
    volume_root = args.volume_root.expanduser().resolve()
    folders = iter_target_folders(volume_root, args.folders)
    total_updated = 0
    for folder in folders:
        total_updated += normalize_folder(folder)
    print(f'SUMMARY updated={total_updated} folders={len(folders)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
