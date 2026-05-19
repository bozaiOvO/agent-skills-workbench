#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.ts'}
TEMP_FILE_PREFIXES = ('._',)
TEMP_FILE_MARKERS = ('.~lock',)
RESERVED_VOLUME_DIRS = {'Data', 'Log', 'Cache', 'Temp', '整理输出_按年份热度'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Delete source video files that already have sibling transcript .txt files.')
    parser.add_argument(
        '--volume-root',
        type=Path,
        default=Path('/Users/bo/Desktop/TikTokDownloader-master/Volume'),
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


def cleanup_folder(folder: Path) -> tuple[int, int]:
    deleted = 0
    kept = 0
    for path in sorted(folder.iterdir()):
        if not path.is_file() or is_temporary_file(path):
            continue
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        transcript = path.with_suffix('.txt')
        if transcript.is_file() and transcript.stat().st_size > 0:
            path.unlink(missing_ok=True)
            deleted += 1
            print(f'[DEL] {path}')
        else:
            kept += 1
    return deleted, kept


def main() -> int:
    args = parse_args()
    volume_root = args.volume_root.expanduser().resolve()
    folders = iter_target_folders(volume_root, args.folders)
    total_deleted = 0
    total_kept = 0
    for folder in folders:
        deleted, kept = cleanup_folder(folder)
        total_deleted += deleted
        total_kept += kept
    print(f'SUMMARY deleted={total_deleted} kept_without_txt={total_kept} folders={len(folders)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
