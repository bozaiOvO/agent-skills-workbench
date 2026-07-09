#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_DOWNLOADER_ROOT = Path('/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master')
DEFAULT_ASR_APP_ROOT = Path('/Users/jinbo/AutomationCenter/apps/语音转文字-mac')
DEFAULT_OUTPUT_ROOT = DEFAULT_DOWNLOADER_ROOT / 'Volume/整理输出_按年份热度'
TEMP_FILE_PREFIXES = ('._',)
TEMP_FILE_MARKERS = ('.~lock',)
LOGIN_COOKIE_KEYS = ('sessionid_ss', 'sessionid', 'sid_tt')
LOGGED_OUT_MARKERS = (
    '配置文件 cookie 参数未登录，数据获取已提前结束',
)
COOKIE_REFRESH_FAILED_MARKERS = (
    '读取 Cookie 失败',
    'Cookie 数据为空',
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the full Douyin blogger pipeline: download, transcribe, and rank.')
    parser.add_argument('urls', nargs='*', help='Douyin blogger home URLs')
    parser.add_argument('--repo-root', type=Path, default=DEFAULT_DOWNLOADER_ROOT)
    parser.add_argument('--asr-app-root', type=Path, default=DEFAULT_ASR_APP_ROOT)
    parser.add_argument('--output-root', type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument('--browser-choice', default='9', help='Downloader browser menu choice for Douyin cookie, default is Firefox=9')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--earliest', default='', help='Download posts on/after this date, e.g. 2024/1/1')
    parser.add_argument('--latest', default='', help='Download posts on/before this date')
    parser.add_argument('--skip-download', action='store_true')
    parser.add_argument('--skip-transcribe', action='store_true')
    parser.add_argument('--skip-organize', action='store_true')
    parser.add_argument('--force-transcribe', action='store_true')
    parser.add_argument('--refresh-cookie', action='store_true', help='Refresh Douyin cookie from browser before downloading')
    parser.add_argument('--allow-logged-out-partial', action='store_true', help='Allow downloader output even when Douyin reports logged-out partial data')
    parser.add_argument('--keep-media', action='store_true', help='Keep source video files after successful transcription and organize')
    parser.add_argument('--stem', dest='stems', action='append', default=[], help='Workbook/folder stem to process when skipping download')
    return parser.parse_args()


def is_temporary_file(path: Path) -> bool:
    return path.name.startswith(TEMP_FILE_PREFIXES) or any(marker in path.name for marker in TEMP_FILE_MARKERS)


def find_target_workbooks(data_root: Path, stems: list[str] | None = None, modified_after: float | None = None) -> list[Path]:
    selected = set(stems or [])
    workbooks: list[Path] = []
    for path in sorted(data_root.glob('UID*.xlsx')):
        if not path.is_file() or is_temporary_file(path):
            continue
        if selected and path.stem not in selected:
            continue
        if modified_after is not None and path.stat().st_mtime < modified_after:
            continue
        workbooks.append(path)
    return workbooks


def build_accounts_urls(urls: list[str], earliest: str, latest: str) -> list[dict[str, object]]:
    return [
        {
            'mark': '',
            'url': url,
            'tab': 'post',
            'earliest': earliest,
            'latest': latest,
            'enable': True,
        }
        for url in urls
    ]


def has_login_cookie(settings: dict) -> bool:
    cookie = settings.get('cookie') or {}
    if isinstance(cookie, dict):
        return any(cookie.get(key) for key in LOGIN_COOKIE_KEYS)
    if isinstance(cookie, str):
        return any(f'{key}=' in cookie for key in LOGIN_COOKIE_KEYS)
    return False


def restore_settings(settings_path: Path, original: dict) -> None:
    settings_path.write_text(json.dumps(original, ensure_ascii=False, indent=4), encoding='utf-8')


def settings_with_refreshed_cookie(settings_path: Path, original: dict) -> dict:
    try:
        current = json.loads(settings_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return original
    if not has_login_cookie(current):
        return original
    restored = dict(original)
    restored['cookie'] = current.get('cookie')
    return restored


def ensure_download_record_enabled(repo_root: Path) -> None:
    db_path = repo_root / 'Volume/DouK-Downloader.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS config_data (
            NAME TEXT PRIMARY KEY,
            VALUE TEXT NOT NULL
            );"""
        )
        conn.execute(
            "INSERT OR IGNORE INTO config_data (NAME, VALUE) VALUES ('Record', '1')"
        )
        conn.execute(
            "UPDATE config_data SET VALUE = '1' WHERE NAME = 'Record'"
        )
        conn.commit()


def run_downloader(
    repo_root: Path,
    urls: list[str],
    browser_choice: str,
    earliest: str,
    latest: str,
    refresh_cookie: bool,
    allow_logged_out_partial: bool,
) -> list[Path]:
    if not urls:
        raise SystemExit('No URLs provided for download step')
    python_path = repo_root / 'venv/bin/python'
    settings_path = repo_root / 'Volume/settings.json'
    data_root = repo_root / 'Volume/Data'
    if not python_path.is_file():
        raise SystemExit(f'Downloader python not found: {python_path}')
    if not settings_path.is_file():
        raise SystemExit(f'Downloader settings not found: {settings_path}')

    original_settings = json.loads(settings_path.read_text(encoding='utf-8'))
    patched_settings = dict(original_settings)
    patched_settings['accounts_urls'] = build_accounts_urls(urls, earliest, latest)
    patched_settings['run_command'] = ''
    patched_settings['download'] = True
    start_time = time.time() - 2
    settings_path.write_text(json.dumps(patched_settings, ensure_ascii=False, indent=4), encoding='utf-8')

    lines = []
    if refresh_cookie or not has_login_cookie(original_settings):
        lines.extend(['2', str(browser_choice)])
    lines.extend(['5', '1', '1', 'Q'])

    env = os.environ.copy()
    env.setdefault('PYTHONIOENCODING', 'utf-8')
    try:
        result = subprocess.run(
            [str(python_path), 'main.py'],
            cwd=repo_root,
            input='\n'.join(lines) + '\n',
            text=True,
            check=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = result.stdout or ''
        print(output, end='' if output.endswith('\n') else '\n')
        if not allow_logged_out_partial and any(marker in output for marker in LOGGED_OUT_MARKERS):
            raise SystemExit(
                'Douyin downloader reported logged-out partial data; refresh the browser cookie before treating this run as complete.'
            )
        if refresh_cookie and any(marker in output for marker in COOKIE_REFRESH_FAILED_MARKERS):
            raise SystemExit(
                f'Douyin cookie refresh failed for browser choice {browser_choice}; choose the browser where Douyin is actually logged in.'
            )
    finally:
        restore_settings(
            settings_path,
            settings_with_refreshed_cookie(settings_path, original_settings) if refresh_cookie else original_settings,
        )

    workbooks = find_target_workbooks(data_root, modified_after=start_time)
    if not workbooks:
        raise SystemExit('Download completed but no updated Data workbook was detected')
    return workbooks


def repo_python(repo_root: Path) -> str:
    python_path = repo_root / 'venv/bin/python'
    return str(python_path) if python_path.is_file() else sys.executable


def run_transcribe(skill_dir: Path, asr_app_root: Path, folders: list[Path], workers: int, force: bool) -> None:
    if not folders:
        print('SKIP no-folders-for-transcribe')
        return
    cmd = [
        sys.executable,
        str(skill_dir / 'scripts/transcribe_media_batch.py'),
        '--asr-app-root',
        str(asr_app_root),
        '--workers',
        str(workers),
        '--placeholder-on-fail',
    ]
    if force:
        cmd.append('--force')
    for folder in folders:
        cmd.extend(['--folder', str(folder)])
    subprocess.run(cmd, check=True)


def run_organize(
    skill_dir: Path,
    python_executable: str,
    volume_root: Path,
    output_root: Path,
    workbooks: list[Path],
    earliest: str,
    latest: str,
) -> None:
    if not workbooks:
        print('SKIP no-workbooks-for-organize')
        return
    cmd = [
        python_executable,
        str(skill_dir / 'scripts/organize_transcripts_by_year.py'),
        '--volume-root',
        str(volume_root),
        '--output-root',
        str(output_root),
    ]
    if earliest:
        cmd.extend(['--earliest', earliest])
    if latest:
        cmd.extend(['--latest', latest])
    for workbook in workbooks:
        cmd.extend(['--stem', workbook.stem])
    subprocess.run(cmd, check=True)


def run_normalize_empty_transcripts(skill_dir: Path, python_executable: str, volume_root: Path, folders: list[Path]) -> None:
    if not folders:
        print('SKIP no-folders-for-normalize')
        return
    cmd = [
        python_executable,
        str(skill_dir / 'scripts/normalize_empty_transcripts.py'),
        '--volume-root',
        str(volume_root),
    ]
    for folder in folders:
        cmd.extend(['--folder', str(folder)])
    subprocess.run(cmd, check=True)


def run_export_time_sorted_transcripts(skill_dir: Path, python_executable: str, volume_root: Path, workbooks: list[Path]) -> None:
    if not workbooks:
        print('SKIP no-workbooks-for-time-sorted-export')
        return
    for workbook in workbooks:
        transcript_dir = volume_root / workbook.stem
        if not transcript_dir.is_dir():
            print(f'SKIP no-transcript-dir-for-time-sorted-export {workbook.stem}')
            continue
        cmd = [
            python_executable,
            str(skill_dir / 'scripts/export_time_sorted_transcripts.py'),
            '--volume-root',
            str(volume_root),
            '--transcript-dir',
            str(transcript_dir),
            '--stem',
            workbook.stem,
        ]
        subprocess.run(cmd, check=True)


def run_cleanup(skill_dir: Path, python_executable: str, volume_root: Path, folders: list[Path]) -> None:
    if not folders:
        print('SKIP no-folders-for-cleanup')
        return
    cmd = [
        python_executable,
        str(skill_dir / 'scripts/cleanup_transcribed_media.py'),
        '--volume-root',
        str(volume_root),
    ]
    for folder in folders:
        cmd.extend(['--folder', str(folder)])
    subprocess.run(cmd, check=True)


def run_special_sync(skill_dir: Path, python_executable: str, volume_root: Path, output_root: Path, workbooks: list[Path]) -> None:
    if not workbooks:
        print('SKIP no-workbooks-for-special-sync')
        return
    cmd = [
        python_executable,
        str(skill_dir / 'scripts/sync_special_blogger_outputs.py'),
        '--volume-root',
        str(volume_root),
        '--ranked-root',
        str(output_root),
    ]
    for workbook in workbooks:
        cmd.extend(['--stem', workbook.stem])
    subprocess.run(cmd, check=True)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    volume_root = repo_root / 'Volume'
    data_root = volume_root / 'Data'
    skill_dir = Path(__file__).resolve().parent.parent
    python_executable = repo_python(repo_root)

    if args.skip_download:
        workbooks = find_target_workbooks(data_root, stems=args.stems or None)
        if not workbooks:
            raise SystemExit('No matching workbooks found while skip-download is enabled')
    else:
        ensure_download_record_enabled(repo_root)
        workbooks = run_downloader(
            repo_root,
            args.urls,
            args.browser_choice,
            args.earliest,
            args.latest,
            args.refresh_cookie,
            args.allow_logged_out_partial,
        )

    folders = [volume_root / workbook.stem for workbook in workbooks if (volume_root / workbook.stem).is_dir()]

    if not args.skip_transcribe:
        run_transcribe(skill_dir, args.asr_app_root.expanduser().resolve(), folders, args.workers, args.force_transcribe)

    run_normalize_empty_transcripts(skill_dir, python_executable, volume_root, folders)

    if not args.skip_organize:
        run_organize(
            skill_dir,
            python_executable,
            volume_root,
            args.output_root.expanduser().resolve(),
            workbooks,
            args.earliest,
            args.latest,
        )

    run_export_time_sorted_transcripts(skill_dir, python_executable, volume_root, workbooks)

    if not args.keep_media:
        run_cleanup(skill_dir, python_executable, volume_root, folders)

    run_special_sync(skill_dir, python_executable, volume_root, args.output_root.expanduser().resolve(), workbooks)

    stems = ', '.join(workbook.stem for workbook in workbooks)
    print(f'SUMMARY stems=[{stems}] output={args.output_root.expanduser().resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
