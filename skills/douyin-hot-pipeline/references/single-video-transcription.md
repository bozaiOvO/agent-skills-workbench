# Single Douyin Video Link → Transcript Notes

Session source: 2026-07-05 Telegram request to transcribe a single Douyin short link from `计算机/AI就业-大风哥`.

## Working path on Jinbo's AutomationCenter

1. Read AutomationCenter entry/settings first, then use configured paths:
   - downloader root: `/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master`
   - ASR app root: `/Users/jinbo/AutomationCenter/apps/语音转文字-mac`
2. For a single video URL, use the lightweight detail-link downloader, not the full blogger pipeline:

```bash
cd /Users/jinbo/AutomationCenter
OUT_DIR="/Users/jinbo/AutomationCenter/tmp/douyin_single_transcript_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"
/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master/.venv/bin/python \
  scripts/download_douyin_detail_links.py --out-dir "$OUT_DIR" 'https://v.douyin.com/xxxx/'
python3 scripts/transcribe_media_batch.py --folder "$OUT_DIR" --workers 1 --retries 2
```

3. Verify exactly one `.txt` sibling was created and has content; send it with `MEDIA:/absolute/path.txt` if the user asked for the file.

## Dependency/bootstrap pitfall

`python3 scripts/download_douyin_detail_links.py ...` may fail under system Python with missing modules such as `httpx` or `gmssl`.

If `/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master/.venv/bin/python` is missing or lacks dependencies, bootstrap it with the ASR Python that already exists:

```bash
DOWNLOADER=/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master
PY312=/Users/jinbo/AutomationCenter/apps/语音转文字-mac/.venv/bin/python
if [ ! -x "$DOWNLOADER/.venv/bin/python" ]; then
  "$PY312" -m venv "$DOWNLOADER/.venv"
fi
"$DOWNLOADER/.venv/bin/python" -m pip install --upgrade pip
"$DOWNLOADER/.venv/bin/python" -m pip install -r "$DOWNLOADER/requirements.txt"
```

This fixed the `ModuleNotFoundError: httpx` and then `ModuleNotFoundError: gmssl` sequence.

## ASR pitfall

`transcribe_media_batch.py` may first try `faster_whisper` and fail with:

```text
LocalEntryNotFoundError: Cannot find an appropriate cached snapshot folder ... outgoing traffic has been disabled
```

This is not fatal if the engine order continues to `bcut`; in the 2026-07 run, BcutASR produced the transcript successfully. Only report failure if all engines fail and no `.txt` is produced.

## Delivery style

For Telegram requests like “把这个视频转文字，把文本文件发过来”, do not send a long process report. Send the resulting `.txt` as media and one short sentence if needed.