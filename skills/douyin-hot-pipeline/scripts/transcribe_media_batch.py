#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Iterable

DEFAULT_ASR_APP_ROOT = Path('/Users/jinbo/AutomationCenter/apps/语音转文字-mac')
MEDIA_EXTENSIONS = {'.mp4', '.mov', '.avi', '.ts', '.m4a', '.mp3', '.wav'}
AUDIO_EXTENSIONS = {'.m4a', '.mp3', '.wav'}
TEMP_FILE_PREFIXES = ('._',)
TEMP_FILE_MARKERS = ('.~lock',)
TEMP_AUDIO_ROOT = Path(tempfile.gettempdir()) / 'douyin_hot_pipeline_audio'
EMPTY_TRANSCRIPT_PLACEHOLDER = '【无有效语音识别结果】'
FAILED_TRANSCRIPT_PLACEHOLDER = '【自动转写失败，已生成占位稿。请按需人工补录正文。】'
DEFAULT_ENGINE_ORDER = os.getenv('DOUYIN_ASR_ENGINES', 'faster_whisper,bcut,jianying,kuaishou,whisper')
DEFAULT_FASTER_WHISPER_MODEL = os.getenv('DOUYIN_FASTER_WHISPER_MODEL', 'small')
DEFAULT_FASTER_WHISPER_DEVICE = os.getenv('DOUYIN_FASTER_WHISPER_DEVICE', 'cpu')
DEFAULT_FASTER_WHISPER_COMPUTE_TYPE = os.getenv('DOUYIN_FASTER_WHISPER_COMPUTE_TYPE', 'int8')
DEFAULT_FASTER_WHISPER_LOCAL_ONLY = os.getenv('DOUYIN_FASTER_WHISPER_LOCAL_ONLY', '1').lower() not in {'0', 'false', 'no'}
FFMPEG_TIMEOUT_SECONDS = int(os.getenv('DOUYIN_ASR_FFMPEG_TIMEOUT_SECONDS', '900'))
ENGINE_TIMEOUT_SECONDS = int(os.getenv('DOUYIN_ASR_ENGINE_TIMEOUT_SECONDS', '900'))
AUTOMATION_ROOT = Path('/Users/jinbo/AutomationCenter')
ENV_FILES = (
    AUTOMATION_ROOT / 'config/bots/secrets.env',
    AUTOMATION_ROOT / 'config/proxy.env',
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Batch-transcribe downloaded media into sibling .txt files.')
    parser.add_argument('--asr-app-root', type=Path, default=DEFAULT_ASR_APP_ROOT)
    parser.add_argument('--folder', dest='folders', action='append', type=Path, default=[])
    parser.add_argument('--file', dest='files', action='append', type=Path, default=[])
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--retries', type=int, default=3)
    parser.add_argument('--engine-order', default=DEFAULT_ENGINE_ORDER, help='Comma-separated engines: faster_whisper,bcut,whisper')
    parser.add_argument('--engine-timeout-seconds', type=int, default=ENGINE_TIMEOUT_SECONDS)
    parser.add_argument('--ffmpeg-timeout-seconds', type=int, default=FFMPEG_TIMEOUT_SECONDS)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--placeholder-on-fail', action='store_true', help='Write a sibling placeholder .txt when all ASR engines fail.')
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


def reexec_with_asr_python(venv_python: Path) -> None:
    current = Path(sys.executable).resolve()
    target = venv_python.resolve()
    if current == target:
        return
    if os.environ.get('DOUYIN_ASR_REEXECED') == '1':
        raise SystemExit(f'ASR must run under {target}, current interpreter is {current}')
    env = os.environ.copy()
    env['DOUYIN_ASR_REEXECED'] = '1'
    os.execve(str(target), [str(target), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def load_runtime_env() -> None:
    for path in ENV_FILES:
        load_env_file(path)


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


def collect_explicit_files(paths: Iterable[Path], force: bool) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        path = path.expanduser().resolve()
        if not path.is_file() or is_temporary_file(path):
            continue
        if path.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        if not force and path.with_suffix('.txt').exists():
            continue
        files.append(path)
    return files


def dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


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


def load_whisper_class(asr_app_root: Path):
    bootstrap_asr_site_packages(asr_app_root)
    sys.path.insert(0, str(asr_app_root))
    from app.bk_asr.WhisperASR import WhisperASR

    return WhisperASR


def load_jianying_class(asr_app_root: Path):
    bootstrap_asr_site_packages(asr_app_root)
    sys.path.insert(0, str(asr_app_root))
    from app.bk_asr.JianYingASR import JianYingASR

    return JianYingASR


def load_kuaishou_class(asr_app_root: Path):
    bootstrap_asr_site_packages(asr_app_root)
    sys.path.insert(0, str(asr_app_root))
    from app.bk_asr.KuaiShouASR import KuaiShouASR

    return KuaiShouASR


def run_faster_whisper(audio_path: str, asr_app_root: Path | None = None) -> str:
    if asr_app_root is not None:
        bootstrap_asr_site_packages(asr_app_root)
    from faster_whisper import WhisperModel

    model = WhisperModel(
        DEFAULT_FASTER_WHISPER_MODEL,
        device=DEFAULT_FASTER_WHISPER_DEVICE,
        compute_type=DEFAULT_FASTER_WHISPER_COMPUTE_TYPE,
        local_files_only=DEFAULT_FASTER_WHISPER_LOCAL_ONLY,
    )
    segments, _info = model.transcribe(
        audio_path,
        language='zh',
        vad_filter=True,
        beam_size=1,
        best_of=1,
        temperature=0,
    )
    return '\n'.join(segment.text.strip() for segment in segments if segment.text.strip()).strip()


def engine_worker(engine_name: str, audio_path: str, asr_app_root: str, queue: Queue) -> None:
    try:
        load_runtime_env()
        root = Path(asr_app_root)
        if engine_name in {'faster_whisper', 'local_whisper'}:
            queue.put(('ok', run_faster_whisper(audio_path, root)))
            return
        if engine_name == 'bcut':
            engine_class = load_bcut_class(root)
        elif engine_name == 'jianying':
            engine_class = load_jianying_class(root)
        elif engine_name == 'kuaishou':
            engine_class = load_kuaishou_class(root)
        elif engine_name == 'whisper':
            engine_class = load_whisper_class(root)
        else:
            raise ValueError(f'unknown ASR engine: {engine_name}')
        result = engine_class(audio_path, use_cache=True).run()
        queue.put(('ok', result.to_txt().strip()))
    except BaseException as error:
        queue.put(('error', f'{type(error).__name__}: {error}'))


def convert_to_audio(src: Path, timeout_seconds: int) -> Path:
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
            timeout=timeout_seconds,
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            fallback_cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds,
        )
    return target


def run_engine_with_timeout(engine_name: str, audio_path: Path, timeout_seconds: int, asr_app_root: Path) -> str:
    if engine_name in {'faster_whisper', 'local_whisper'}:
        return run_faster_whisper(str(audio_path), asr_app_root)
    queue: Queue = Queue()
    process = Process(target=engine_worker, args=(engine_name, str(audio_path), str(asr_app_root), queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(5)
        if process.is_alive():
            process.kill()
            process.join(5)
        raise TimeoutError(f'{engine_name} timed out after {timeout_seconds}s')
    if process.exitcode and process.exitcode < 0:
        signame = signal.Signals(-process.exitcode).name if -process.exitcode in [sig.value for sig in signal.Signals] else process.exitcode
        raise RuntimeError(f'{engine_name} exited by signal {signame}')
    if queue.empty():
        raise RuntimeError(f'{engine_name} exited without result exit={process.exitcode}')
    status, payload = queue.get()
    if status == 'ok':
        return str(payload)
    raise RuntimeError(str(payload))


def transcribe_one(
    path: Path,
    retries: int,
    engine_order: list[str],
    asr_app_root: Path,
    engine_timeout_seconds: int,
    ffmpeg_timeout_seconds: int,
    placeholder_on_fail: bool,
) -> tuple[Path, bool, str, int]:
    audio_path: Path | None = None
    errors: list[str] = []
    for attempt in range(1, retries + 1):
        try:
            if path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_path = path
                print(f'[STEP] {path.name} attempt={attempt} audio_source=original', flush=True)
            else:
                print(f'[STEP] {path.name} attempt={attempt} ffmpeg_start timeout={ffmpeg_timeout_seconds}s', flush=True)
                audio_path = convert_to_audio(path, ffmpeg_timeout_seconds)
                print(f'[STEP] {path.name} attempt={attempt} ffmpeg_done audio={audio_path.name}', flush=True)
        except Exception as error:
            errors.append(f'ffmpeg attempt={attempt}: {type(error).__name__}: {error}')
            print(f'[STEP] {path.name} attempt={attempt} ffmpeg_error {type(error).__name__}: {error}', flush=True)
            break

        for engine_name in engine_order:
            try:
                print(f'[STEP] {path.name} attempt={attempt} engine_start={engine_name} timeout={engine_timeout_seconds}s', flush=True)
                text = run_engine_with_timeout(engine_name, audio_path, engine_timeout_seconds, asr_app_root)
                if not text:
                    text = EMPTY_TRANSCRIPT_PLACEHOLDER
                path.with_suffix('.txt').write_text(text, encoding='utf-8')
                if audio_path != path and audio_path and audio_path.exists():
                    audio_path.unlink(missing_ok=True)
                return path, True, engine_name, len(text)
            except Exception as error:
                errors.append(f'{engine_name} attempt={attempt}: {type(error).__name__}: {error}')
                print(f'[STEP] {path.name} attempt={attempt} engine_error={engine_name} {type(error).__name__}: {error}', flush=True)
        time.sleep(min(10, attempt * 2))
    if audio_path != path and audio_path and audio_path.exists():
        audio_path.unlink(missing_ok=True)
    if placeholder_on_fail:
        detail = ' | '.join(errors[-8:])
        text = f'{FAILED_TRANSCRIPT_PLACEHOLDER}\n\n失败原因：{detail}\n'
        path.with_suffix('.txt').write_text(text, encoding='utf-8')
        return path, True, f'placeholder_after_failed_asr: {detail}', len(text)
    return path, False, ' | '.join(errors[-8:]), 0


def main() -> int:
    args = parse_args()
    load_runtime_env()
    venv_python = ensure_dependencies(args.asr_app_root)
    reexec_with_asr_python(venv_python)
    engine_order = [engine.strip().lower() for engine in args.engine_order.split(',') if engine.strip()]
    if not engine_order:
        raise SystemExit('No ASR engines configured')
    unknown = [engine for engine in engine_order if engine not in {'faster_whisper', 'local_whisper', 'bcut', 'jianying', 'kuaishou', 'whisper'}]
    if unknown:
        raise SystemExit(f'Unsupported ASR engines: {", ".join(unknown)}')
    folders = [folder.expanduser().resolve() for folder in args.folders]
    files = dedupe_paths([*collect_media_files(folders, args.force), *collect_explicit_files(args.files, args.force)])
    total = len(files)
    print(f'TODO {total} engines={",".join(engine_order)} engine_timeout={args.engine_timeout_seconds}s ffmpeg_timeout={args.ffmpeg_timeout_seconds}s', flush=True)
    if not files:
        return 0

    success = 0
    placeholders = 0
    failed = 0
    failures: list[tuple[Path, str]] = []
    placeholder_failures: list[tuple[Path, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {
            executor.submit(
                transcribe_one,
                path,
                args.retries,
                engine_order,
                args.asr_app_root,
                args.engine_timeout_seconds,
                args.ffmpeg_timeout_seconds,
                args.placeholder_on_fail,
            ): path
            for path in files
        }
        for index, future in enumerate(as_completed(future_map), start=1):
            path, ok, detail, text_len = future.result()
            if ok:
                if detail.startswith('placeholder_after_failed_asr:'):
                    placeholders += 1
                    placeholder_failures.append((path, detail))
                    print(f'[PLACEHOLDER {index}/{total}] {path.name} -> {path.with_suffix(".txt").name} ({text_len} chars)', flush=True)
                else:
                    success += 1
                    print(f'[OK {index}/{total}] {path.name} -> {path.with_suffix(".txt").name} ({text_len} chars, engine={detail})', flush=True)
            else:
                failed += 1
                failures.append((path, detail))
                print(f'[FAIL {index}/{total}] {path.name} :: {detail}', flush=True)
    print(f'SUMMARY ok={success} placeholder={placeholders} fail={failed} total={total}', flush=True)
    if placeholder_failures:
        print('PLACEHOLDER_LIST_START', flush=True)
        for path, error in placeholder_failures:
            print(path, flush=True)
            print(error, flush=True)
        print('PLACEHOLDER_LIST_END', flush=True)
    if failures:
        print('FAILED_LIST_START', flush=True)
        for path, error in failures:
            print(path, flush=True)
            print(error, flush=True)
        print('FAILED_LIST_END', flush=True)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
