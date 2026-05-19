#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_DIR = Path(__file__).resolve().parent
ORGANIZE = load_module('organize_script', SCRIPT_DIR / 'organize_transcripts_by_year.py')
TRANSCRIBE = load_module('transcribe_script', SCRIPT_DIR / 'transcribe_media_batch.py')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Transcribe only missing video transcripts for a workbook date range.')
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--asr-app-root', type=Path, default=Path('/Users/bo/Documents/语音转文字-mac'))
    parser.add_argument('--earliest', default='')
    parser.add_argument('--latest', default='')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--retries', type=int, default=3)
    return parser.parse_args()


def select_media_files(workbook: Path, folder: Path, earliest: str, latest: str) -> tuple[list[Path], list[str]]:
    earliest_dt = ORGANIZE.parse_datetime_value(earliest) if earliest else None
    latest_dt = ORGANIZE.parse_datetime_value(latest) if latest else None
    header, rows = ORGANIZE.workbook_rows(workbook)
    mp4_map = {
        path.stem: path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == '.mp4' and not ORGANIZE.is_temporary_file(path)
    }
    txt_map = {
        path.stem: path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == '.txt' and not ORGANIZE.is_temporary_file(path)
    }
    selected: dict[str, Path] = {}
    missing_media: list[str] = []
    for row in rows:
        row_data = ORGANIZE.row_to_dict(header, row)
        publish_dt = ORGANIZE.parse_datetime_value(row_data.get('发布时间'))
        if earliest_dt is not None and (publish_dt is None or publish_dt < earliest_dt):
            continue
        if latest_dt is not None and (publish_dt is None or publish_dt > latest_dt):
            continue
        if str(row_data.get('作品类型') or '').strip() != '视频':
            continue
        stem = ORGANIZE.expected_transcript_stem(row_data)
        prefix = ORGANIZE.transcript_prefix(row_data)
        if stem in txt_map:
            continue
        txt_candidates = [path for key, path in txt_map.items() if prefix and key.startswith(prefix)]
        if len(txt_candidates) == 1:
            continue
        media = mp4_map.get(stem)
        if media is None:
            media_candidates = [path for key, path in mp4_map.items() if prefix and key.startswith(prefix)]
            if len(media_candidates) == 1:
                media = media_candidates[0]
        if media is None:
            missing_media.append(stem)
            continue
        selected[str(media)] = media
    return sorted(selected.values()), missing_media


def main() -> int:
    args = parse_args()
    workbook = args.workbook.expanduser().resolve()
    folder = args.folder.expanduser().resolve()
    asr_app_root = args.asr_app_root.expanduser().resolve()
    files, missing_media = select_media_files(workbook, folder, args.earliest, args.latest)
    print(f'TODO {len(files)} earliest={args.earliest or "-"} latest={args.latest or "-"}', flush=True)
    if missing_media:
        print(f'MISSING_MEDIA {len(missing_media)}', flush=True)
        for stem in missing_media[:20]:
            print(stem, flush=True)
    if not files:
        print('SUMMARY ok=0 fail=0 total=0', flush=True)
        return 0

    TRANSCRIBE.ensure_dependencies(asr_app_root)
    bcut_class = TRANSCRIBE.load_bcut_class(asr_app_root)
    success = 0
    failed = 0
    failures: list[tuple[Path, str]] = []
    total = len(files)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {executor.submit(TRANSCRIBE.transcribe_one, path, args.retries, bcut_class): path for path in files}
        for index, future in enumerate(as_completed(future_map), start=1):
            path, ok, error, text_len = future.result()
            if ok:
                success += 1
                if index % 10 == 0 or index == total:
                    print(f'[OK {index}/{total}] {path.name} chars={text_len}', flush=True)
            else:
                failed += 1
                failures.append((path, error))
                print(f'[FAIL {index}/{total}] {path.name} :: {error}', flush=True)
    print(f'SUMMARY ok={success} fail={failed} total={total}', flush=True)
    if failures:
        print('FAILED_LIST_START', flush=True)
        for path, error in failures:
            print(path, flush=True)
            print(error, flush=True)
        print('FAILED_LIST_END', flush=True)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
