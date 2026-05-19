#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from organize_transcripts_by_year import collect_items, filter_name, render_output

DEFAULT_VOLUME_ROOT = Path('/Users/bo/Desktop/TikTokDownloader-master/Volume')
DEFAULT_RANKED_ROOT = DEFAULT_VOLUME_ROOT / '整理输出_按年份热度'
SPECIAL_RULES = {
    'UID1822310415739536_老宋聊就业_发布作品': {
        'blogger_name': '老宋聊就业',
        'targets': [
            Path('/Users/bo/Documents/2026/老宋系统/我的脚本/已发布'),
            Path('/Users/bo/Documents/2026/老宋Claude/我的脚本/已发布'),
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sync special blogger outputs to published folders.')
    parser.add_argument('--volume-root', type=Path, default=DEFAULT_VOLUME_ROOT)
    parser.add_argument('--ranked-root', type=Path, default=DEFAULT_RANKED_ROOT)
    parser.add_argument('--stem', dest='stems', action='append', default=[])
    return parser.parse_args()


def reset_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.name.startswith('.'):
            continue
        if child.is_dir():
            shutil.rmtree(child)
        elif child.is_file():
            child.unlink()


def copy_annual_outputs(source_root: Path, target_root: Path) -> int:
    reset_directory(target_root)
    if not source_root.is_dir():
        return 0
    copied = 0
    for source_year in sorted(path for path in source_root.iterdir() if path.is_dir()):
        target_year = target_root / source_year.name
        shutil.copytree(source_year, target_year, dirs_exist_ok=True)
        copied += sum(1 for path in source_year.iterdir() if path.is_file() and path.suffix.lower() == '.txt')
    return copied


def build_time_sorted_items(volume_root: Path, stem: str) -> tuple[list[dict[str, object]], dict[str, int]]:
    workbook_path = volume_root / 'Data' / f'{stem}.xlsx'
    blogger_folder = volume_root / stem
    if not workbook_path.is_file():
        raise SystemExit(f'Workbook not found for special sync: {workbook_path}')
    if not blogger_folder.is_dir():
        raise SystemExit(f'Folder not found for special sync: {blogger_folder}')
    _, grouped, stats = collect_items(workbook_path, blogger_folder)
    items = [item for group in grouped.values() for item in group]
    items.sort(key=lambda item: (str(item['publish_sort']), str(item['stem'])))
    return items, stats


def write_time_sorted_outputs(items: list[dict[str, object]], target_root: Path) -> int:
    reset_directory(target_root)
    written = 0
    for item in items:
        filename = filter_name(str(item['stem']), default=str(item['work_id']))
        (target_root / f'{filename}.txt').write_text(render_output(item), encoding='utf-8')
        written += 1
    return written


def sync_special_stem(volume_root: Path, ranked_root: Path, stem: str) -> None:
    rule = SPECIAL_RULES.get(stem)
    if rule is None:
        print(f'SKIP no-special-sync {stem}')
        return
    blogger_name = str(rule['blogger_name'])
    annual_source = ranked_root / filter_name(blogger_name, blogger_name)
    items, stats = build_time_sorted_items(volume_root, stem)
    for target in rule['targets']:
        annual_target = target / '年度top排序'
        time_target = target / '时间排序'
        annual_count = copy_annual_outputs(annual_source, annual_target)
        time_count = write_time_sorted_outputs(items, time_target)
        print(
            f'OK special-sync target={target} annual={annual_count} '
            f'time={time_count} matched={stats["matched"]} unmatched={stats["unmatched"]}'
        )


def main() -> int:
    args = parse_args()
    volume_root = args.volume_root.expanduser().resolve()
    ranked_root = args.ranked_root.expanduser().resolve()
    stems = args.stems or []
    if not stems:
        print('SKIP no-stems-for-special-sync')
        return 0
    for stem in stems:
        sync_special_stem(volume_root, ranked_root, stem)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
