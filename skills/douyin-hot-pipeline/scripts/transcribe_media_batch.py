#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

DEFAULT_ASR_APP_ROOT = Path('/Users/bo/Documents/语音转文字-mac')
MEDIA_EXTENSIONS = {'.mp4', '.mov', '.avi', '.ts', '.m4a', '.mp3', '.wav'}
AUDIO_EXTENSIONS = {'.m4a', '.mp3', '.wav'}
TEMP_FILE_PREFIXES = ('._',)
TEMP_FILE_MARKERS = ('.~lock',)
TEMP_AUDIO_ROOT = Path(tempfile.gettempdir()) / 'douyin_hot_pipeline_audio'
EMPTY_TRANSCRIPT_PLACEHOLDER = '【无有效语音识别结果】'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Batch-transcribe downloaded media into sibling .txt files.')
    parser.add_argument('--asr-app-root', type=Path, default=DEFAULT_ASR_APP_ROOT)
    parser.add_argument('--folder', dest='folders', action='append', type=Path, default=[])
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--retries', type=int, default=3)
    parser.add_argument('--force', action='store_true')
    return parser.parse_args()


def is_temporary_file(path: Path) -> bool:
    return path.name.startswith(TEMP_FILE_PREFIXES) or any(marker in path.name for marker in TEMP_FILE_MARKERS)


def ensure_dependencies(asr_app_root: Path):
    if not asr_app_root.is_dir():
        raise SystemExit(f'ASR app root not found: {asr_app_root}')
    venv_python = asr_app_root / '.venv/bin/python'
    if not venv_python.is_file():
        raise SystemExit(f'ASR virtualenv python not found: {venv_python}')
    if not shutil_which('ffmpeg'):
        raise SystemExit('ffmpeg not found in PATH')
    return venv_python


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)


def collect_media_files(folders: Iterable[Path], force: bool) -> list[Path]:
    files: list[Path] = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            if not path.is_file() or is_temporary_file(path):
                continue
            if path.suffix.lower() not in MEDIA_EXTENSIONS:
                continue
            if not force and path.with_suffix('.txt').exists():
                continue
            files.append(path)
    return files


def bootstrap_asr_site_packages(asr_app_root: Path) -> None:
    lib_root = asr_app_root / '.venv/lib'
    if not lib_root.is_dir():
        return
    for site_packages in sorted(lib_root.glob('python*/site-packages')):
        if site_packages.is_dir() and str(site_packages) not in sys.path:
            sys.path.insert(0, str(site_packages))


def load_bcut_class(asr_app_root: Path):
    bootstrap_asr_site_packages(asr_app_root)
    sys.path.insert(0, str(asr_app_root))
    from app.bk_asr.BcutASR import BcutASR

    return BcutASR


def convert_to_audio(src: Path) -> Path:
    TEMP_AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(str(src).encode('utf-8')).hexdigest()[:20]
    target = TEMP_AUDIO_ROOT / f'{key}.mp3'
    fast_cmd = [
        'ffmpeg',
        '-y',
        '-i',
        str(src),
        '-vn',
        '-ac',
        '1',
        '-ar',
        '16000',
        '-acodec',
        'libmp3lame',
        '-b:a',
        '32k',
        str(target),
    ]
    fallback_cmd = ['ffmpeg', '-y', '-i', str(src), '-vn', '-acodec', 'libmp3lame', '-q:a', '4', str(target)]
    try:
        subprocess.run(
            fast_cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            fallback_cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return target


def transcribe_one(path: Path, retries: int, bcut_class) -> tuple[Path, bool, str, int]:
    audio_path: Path | None = None
    last_error = ''
    for attempt in range(1, retries + 1):
        try:
            if path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_path = path
            else:
                audio_path = convert_to_audio(path)
            result = bcut_class(str(audio_path), use_cache=True).run()
            text = result.to_txt().strip()
            if not text:
                text = EMPTY_TRANSCRIPT_PLACEHOLDER
            path.with_suffix('.txt').write_text(text, encoding='utf-8')
            if audio_path != path and audio_path and audio_path.exists():
                audio_path.unlink(missing_ok=True)
            return path, True, '', len(text)
        except Exception as error:
            last_error = f'{type(error).__name__}: {error}'
            time.sleep(min(10, attempt * 2))
    if audio_path != path and audio_path and audio_path.exists():
        audio_path.unlink(missing_ok=True)
    return path, False, last_error, 0


def main() -> int:
    args = parse_args()
    ensure_dependencies(args.asr_app_root)
    bcut_class = load_bcut_class(args.asr_app_root)
    folders = [folder.expanduser().resolve() for folder in args.folders]
    files = collect_media_files(folders, args.force)
    total = len(files)
    print(f'TODO {total}', flush=True)
    if not files:
        return 0

    success = 0
    failed = 0
    failures: list[tuple[Path, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {executor.submit(transcribe_one, path, args.retries, bcut_class): path for path in files}
        for index, future in enumerate(as_completed(future_map), start=1):
            path, ok, error, text_len = future.result()
            if ok:
                success += 1
                print(f'[OK {index}/{total}] {path.name} -> {path.with_suffix(".txt").name} ({text_len} chars)', flush=True)
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
