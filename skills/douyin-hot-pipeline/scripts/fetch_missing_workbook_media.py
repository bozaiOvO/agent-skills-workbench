#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib import error, request


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT_DIR = Path(__file__).resolve().parent
ORGANIZE = load_module('organize_script', SCRIPT_DIR / 'organize_transcripts_by_year.py')
DEFAULT_SETTINGS = Path('/Users/bo/Desktop/TikTokDownloader-master/Volume/settings.json')
DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/135.0.0.0 Safari/537.36'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Download missing workbook-mapped Douyin videos directly from 下载地址.')
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--settings', type=Path, default=DEFAULT_SETTINGS)
    parser.add_argument('--earliest', default='')
    parser.add_argument('--latest', default='')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--retries', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--force', action='store_true')
    return parser.parse_args()


def load_cookie_header(settings_path: Path) -> str:
    if not settings_path.is_file():
        return ''
    try:
        payload = json.loads(settings_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return ''
    cookie = payload.get('cookie')
    if isinstance(cookie, str):
        return cookie.strip()
    if isinstance(cookie, dict):
        parts = []
        for key, value in cookie.items():
            key_text = str(key or '').strip()
            value_text = str(value or '').strip()
            if not key_text or not value_text:
                continue
            parts.append(f'{key_text}={value_text}')
        return '; '.join(parts)
    return ''


def existing_video_map(folder: Path) -> dict[str, Path]:
    return {
        path.stem: path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == '.mp4' and not ORGANIZE.is_temporary_file(path)
    }


def resolve_existing(stem: str, prefix: str, mp4_map: dict[str, Path]) -> Path | None:
    existing = mp4_map.get(stem)
    if existing is not None:
        return existing
    candidates = [path for key, path in mp4_map.items() if prefix and key.startswith(prefix)]
    if len(candidates) == 1:
        return candidates[0]
    return None


def select_jobs(
    workbook: Path,
    folder: Path,
    earliest: str,
    latest: str,
    force: bool,
    limit: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    earliest_dt = ORGANIZE.parse_datetime_value(earliest) if earliest else None
    latest_dt = ORGANIZE.parse_datetime_value(latest) if latest else None
    header, rows = ORGANIZE.workbook_rows(workbook)
    mp4_map = existing_video_map(folder)
    txt_map = {
        path.stem: path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == '.txt' and not ORGANIZE.is_temporary_file(path)
    }
    selected: list[dict[str, Any]] = []
    issues: list[str] = []
    seen_keys: set[str] = set()
    for row in rows:
        row_data = ORGANIZE.row_to_dict(header, row)
        if str(row_data.get('作品类型') or '').strip() != '视频':
            continue
        publish_dt = ORGANIZE.parse_datetime_value(row_data.get('发布时间'))
        if earliest_dt is not None and (publish_dt is None or publish_dt < earliest_dt):
            continue
        if latest_dt is not None and (publish_dt is None or publish_dt > latest_dt):
            continue
        stem = ORGANIZE.expected_transcript_stem(row_data)
        prefix = ORGANIZE.transcript_prefix(row_data)
        work_id = str(row_data.get('作品ID') or '').strip()
        unique_key = work_id or stem
        if unique_key in seen_keys:
            continue
        seen_keys.add(unique_key)
        existing_txt = txt_map.get(stem)
        if existing_txt is None:
            txt_candidates = [path for key, path in txt_map.items() if prefix and key.startswith(prefix)]
            if len(txt_candidates) == 1:
                existing_txt = txt_candidates[0]
        if existing_txt is not None and existing_txt.is_file() and existing_txt.stat().st_size > 0 and not force:
            continue
        existing = resolve_existing(stem, prefix, mp4_map)
        if existing is not None and existing.is_file() and existing.stat().st_size > 0 and not force:
            continue
        url = str(row_data.get('下载地址') or '').strip()
        if not url.startswith('http'):
            issues.append(f'NO_URL {unique_key} {stem}')
            continue
        destination = folder / f'{stem}.mp4'
        selected.append(
            {
                'destination': destination,
                'stem': stem,
                'prefix': prefix,
                'url': url,
                'work_id': work_id,
                'publish_time': ORGANIZE.normalize_datetime_text(row_data.get('发布时间')),
            }
        )
        if limit > 0 and len(selected) >= limit:
            break
    return selected, issues


def make_headers(cookie_header: str) -> dict[str, str]:
    headers = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    if cookie_header:
        headers['Cookie'] = cookie_header
    return headers


def download_one(job: dict[str, Any], cookie_header: str, timeout: int, retries: int) -> tuple[Path, bool, str, int]:
    destination = Path(job['destination'])
    temp_path = destination.with_suffix(destination.suffix + '.part')
    headers = make_headers(cookie_header)
    ssl_context = ssl._create_unverified_context()
    for attempt in range(1, retries + 1):
        try:
            temp_path.unlink(missing_ok=True)
            req = request.Request(str(job['url']), headers=headers)
            with request.urlopen(req, timeout=timeout, context=ssl_context) as response:
                content_type = response.headers.get_content_type()
                with temp_path.open('wb') as file_obj:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        file_obj.write(chunk)
            size = temp_path.stat().st_size if temp_path.exists() else 0
            if size <= 0:
                raise ValueError('empty file')
            if content_type.startswith('text/'):
                raise ValueError(f'unexpected content-type {content_type}')
            temp_path.replace(destination)
            return destination, True, '', size
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            if attempt >= retries:
                return destination, False, f'{type(exc).__name__}: {exc}', 0
            time.sleep(min(2 ** (attempt - 1), 8))
    return destination, False, 'unknown error', 0


def main() -> int:
    args = parse_args()
    workbook = args.workbook.expanduser().resolve()
    folder = args.folder.expanduser().resolve()
    settings = args.settings.expanduser().resolve()
    if not workbook.is_file():
        raise SystemExit(f'Workbook not found: {workbook}')
    if not folder.is_dir():
        raise SystemExit(f'Folder not found: {folder}')
    jobs, issues = select_jobs(workbook, folder, args.earliest, args.latest, args.force, args.limit)
    print(f'TODO {len(jobs)} earliest={args.earliest or "-"} latest={args.latest or "-"}', flush=True)
    if issues:
        print(f'ISSUES {len(issues)}', flush=True)
        for issue in issues[:20]:
            print(issue, flush=True)
    if not jobs:
        print('SUMMARY ok=0 fail=0 total=0', flush=True)
        return 0

    cookie_header = load_cookie_header(settings)
    success = 0
    failed = 0
    failures: list[tuple[Path, str]] = []
    total = len(jobs)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(download_one, job, cookie_header, args.timeout, args.retries): job
            for job in jobs
        }
        for index, future in enumerate(as_completed(future_map), start=1):
            path, ok, error_text, size = future.result()
            if ok:
                success += 1
                print(f'[OK {index}/{total}] {path.name} bytes={size}', flush=True)
            else:
                failed += 1
                failures.append((path, error_text))
                print(f'[FAIL {index}/{total}] {path.name} :: {error_text}', flush=True)
    print(f'SUMMARY ok={success} fail={failed} total={total}', flush=True)
    if failures:
        print('FAILED_LIST_START', flush=True)
        for path, error_text in failures:
            print(path, flush=True)
            print(error_text, flush=True)
        print('FAILED_LIST_END', flush=True)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
