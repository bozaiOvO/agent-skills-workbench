#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import fcntl
import json
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

AUTOMATION_ROOT = Path(os.environ.get('AUTOMATION_CENTER_ROOT', '/Users/jinbo/AutomationCenter'))
AUTOMATION_SCRIPTS = AUTOMATION_ROOT / 'scripts'
if str(AUTOMATION_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_SCRIPTS))

from storage_paths import load_storage_paths

STORAGE = load_storage_paths()
DEFAULT_DOWNLOADER_ROOT = STORAGE.downloader_root
DEFAULT_VOLUME_ROOT = STORAGE.douyin_downloads_root
DEFAULT_ASR_APP_ROOT = Path('/Users/jinbo/AutomationCenter/apps/语音转文字-mac')
DEFAULT_OUTPUT_ROOT = STORAGE.douyin_ranked_root
DEFAULT_TRANSCRIBE_SCRIPT = Path('/Users/jinbo/AutomationCenter/scripts/transcribe_media_batch.py')
DOWNLOADER_SETTINGS_LOCK_NAME = '.douyin-downloader-settings.lock'
EX_TEMPFAIL = getattr(os, 'EX_TEMPFAIL', 75)
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


class DownloaderSettingsLockBusy(RuntimeError):
    pass


def downloader_settings_lock_path(settings_path: Path) -> Path:
    return settings_path.parent / DOWNLOADER_SETTINGS_LOCK_NAME


@contextmanager
def downloader_settings_lock(settings_path: Path):
    lock_path = downloader_settings_lock_path(settings_path)
    with lock_path.open('a+', encoding='utf-8') as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            raise DownloaderSettingsLockBusy(f'Downloader settings lock busy: {lock_path}') from exc
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextmanager
def termination_signals_as_exit():
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    previous_handlers: dict[int, object] = {}

    def handle_termination(signum, _frame) -> None:
        raise SystemExit(128 + signum)

    try:
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, handle_termination)
        yield
    finally:
        for signum, previous_handler in previous_handlers.items():
            signal.signal(signum, previous_handler)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the full Douyin blogger pipeline: download, transcribe, and rank.')
    parser.add_argument('urls', nargs='*', help='Douyin blogger home URLs')
    parser.add_argument('--repo-root', type=Path, default=DEFAULT_DOWNLOADER_ROOT)
    parser.add_argument('--volume-root', type=Path, default=None)
    parser.add_argument('--asr-app-root', type=Path, default=DEFAULT_ASR_APP_ROOT)
    parser.add_argument('--output-root', type=Path, default=None)
    parser.add_argument('--browser-choice', default='9', help='Downloader browser menu choice for Douyin cookie, default is Firefox=9')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--asr-engine-order', default=os.getenv('DOUYIN_ASR_ENGINES', ''))
    parser.add_argument('--transcribe-script', type=Path, default=DEFAULT_TRANSCRIBE_SCRIPT)
    parser.add_argument('--earliest', default='', help='Download posts on/after this date, e.g. 2024/1/1')
    parser.add_argument('--latest', default='', help='Download posts on/before this date')
    parser.add_argument('--skip-download', action='store_true')
    parser.add_argument('--skip-transcribe', action='store_true')
    parser.add_argument('--skip-organize', action='store_true')
    parser.add_argument('--force-transcribe', action='store_true')
    parser.add_argument('--refresh-cookie', action='store_true', help='Refresh Douyin cookie from browser before downloading')
    parser.add_argument('--allow-logged-out-partial', action='store_true', help='Allow downloader output even when Douyin reports logged-out partial data')
    parser.add_argument('--keep-media', action='store_true', help='Compatibility flag. Source media is always retained until verified NAS archival.')
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


def ensure_download_record_enabled(repo_root: Path, volume_root: Path | None = None) -> None:
    volume_root = volume_root or repo_root / 'Volume'
    db_path = volume_root / 'DouK-Downloader.db'
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
    volume_root: Path | None = None,
) -> list[Path]:
    if not urls:
        raise SystemExit('No URLs provided for download step')
    python_path = repo_root / 'venv/bin/python'
    volume_root = volume_root or repo_root / 'Volume'
    settings_path = volume_root / 'settings.json'
    data_root = volume_root / 'Data'
    if not python_path.is_file():
        raise SystemExit(f'Downloader python not found: {python_path}')
    if not settings_path.is_file():
        raise SystemExit(f'Downloader settings not found: {settings_path}')

    lines = []
    env = os.environ.copy()
    env.setdefault('PYTHONIOENCODING', 'utf-8')
    with downloader_settings_lock(settings_path):
        original_settings = json.loads(settings_path.read_text(encoding='utf-8'))
        patched_settings = dict(original_settings)
        patched_settings['accounts_urls'] = build_accounts_urls(urls, earliest, latest)
        patched_settings['run_command'] = ''
        patched_settings['download'] = True
        start_time = time.time() - 2

        if refresh_cookie or not has_login_cookie(original_settings):
            lines.extend(['2', str(browser_choice)])
        lines.extend(['5', '1', '1', 'Q'])

        with termination_signals_as_exit():
            try:
                settings_path.write_text(json.dumps(patched_settings, ensure_ascii=False, indent=4), encoding='utf-8')
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


def run_transcribe(
    transcribe_script: Path,
    asr_app_root: Path,
    folders: list[Path],
    workers: int,
    force: bool,
    engine_order: str,
) -> None:
    if not folders:
        print('SKIP no-folders-for-transcribe')
        return
    cmd = [
        sys.executable,
        str(transcribe_script),
        '--asr-app-root',
        str(asr_app_root),
        '--workers',
        str(workers),
    ]
    if engine_order:
        cmd.extend(['--engine-order', engine_order])
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
    default_repo = DEFAULT_DOWNLOADER_ROOT.expanduser().resolve()
    volume_root = (
        args.volume_root.expanduser().resolve()
        if args.volume_root
        else (DEFAULT_VOLUME_ROOT if repo_root == default_repo else repo_root / 'Volume').expanduser().resolve()
    )
    output_root = (
        args.output_root.expanduser().resolve()
        if args.output_root
        else (DEFAULT_OUTPUT_ROOT if volume_root == DEFAULT_VOLUME_ROOT else volume_root / '整理输出_按年份热度').expanduser().resolve()
    )
    data_root = volume_root / 'Data'
    skill_dir = Path(__file__).resolve().parent.parent
    python_executable = repo_python(repo_root)

    if args.skip_download:
        workbooks = find_target_workbooks(data_root, stems=args.stems or None)
        if not workbooks:
            raise SystemExit('No matching workbooks found while skip-download is enabled')
    else:
        ensure_download_record_enabled(repo_root, volume_root)
        try:
            workbooks = run_downloader(
                repo_root,
                args.urls,
                args.browser_choice,
                args.earliest,
                args.latest,
                args.refresh_cookie,
                args.allow_logged_out_partial,
                volume_root,
            )
        except DownloaderSettingsLockBusy as exc:
            print(f'ERROR {exc}', file=sys.stderr)
            return EX_TEMPFAIL

    folders = [volume_root / workbook.stem for workbook in workbooks if (volume_root / workbook.stem).is_dir()]

    if not args.skip_transcribe:
        transcribe_script = args.transcribe_script.expanduser().resolve()
        if not transcribe_script.is_file():
            raise SystemExit(f'Transcribe script not found: {transcribe_script}')
        run_transcribe(
            transcribe_script,
            args.asr_app_root.expanduser().resolve(),
            folders,
            args.workers,
            args.force_transcribe,
            args.asr_engine_order,
        )

    run_normalize_empty_transcripts(skill_dir, python_executable, volume_root, folders)

    if not args.skip_organize:
        run_organize(
            skill_dir,
            python_executable,
            volume_root,
            output_root,
            workbooks,
            args.earliest,
            args.latest,
        )

    run_export_time_sorted_transcripts(skill_dir, python_executable, volume_root, workbooks)

    run_special_sync(skill_dir, python_executable, volume_root, output_root, workbooks)

    stems = ', '.join(workbook.stem for workbook in workbooks)
    print(f'SUMMARY stems=[{stems}] output={output_root}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
