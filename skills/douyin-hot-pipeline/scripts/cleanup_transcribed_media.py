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

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.ts'}
TEMP_FILE_PREFIXES = ('._',)
TEMP_FILE_MARKERS = ('.~lock',)
RESERVED_VOLUME_DIRS = {'Data', 'Log', 'Cache', 'Temp', '整理输出_按年份热度'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Delete source video files that already have sibling transcript .txt files.')
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


def main() -> int:
    parse_args()
    print(
        'ERROR unsafe cleanup disabled; use scripts/archive_douyin_blogger_outputs.py '
        '--stem <UID..._发布作品> --delete-local-media after NAS verification',
        file=sys.stderr,
    )
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
