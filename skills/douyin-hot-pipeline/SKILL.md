---
name: douyin-hot-pipeline
description: "批量下载抖音博主视频，转写、校正、排序并归档。用于完整抖音内容采集流程。"

---

# Douyin Hot Pipeline

## Overview

Use this skill to run the full local Douyin workflow on this Mac:

- download one or more blogger home URLs
- refresh or reuse browser cookies
- transcribe media into sibling `.txt`
- rewrite sibling `.txt` with the same metadata header used by ranked outputs
- rank yearly hot posts into `topNNN_*.txt`

Jinbo's production skill root is `/Users/jinbo/AutomationCenter/config/skills/douyin-hot-pipeline`. The weekly launchd flow must resolve to this tracked path and `/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master`; reject workbench, Documents, `.agents`, or legacy `/Users/bo` roots as production runtime. Prefer configured paths from `/Users/jinbo/AutomationCenter/config/settings.json`.

The workbench copy at `/Users/jinbo/Documents/agent-workbench/agent-skills-workbench/skills/douyin-hot-pipeline` is a development/source mirror only.

## Production Identity And AI Contract

- `UID` is the permanent blogger identity and only account join key. Nickname changes update canonical display name/aliases; they do not create a new logical blogger.
- `作品ID` is the permanent work identity. Scan all included work metadata every run, but download/transcribe media only for new or explicitly missing作品ID. A nickname change must not trigger historical media redownload.
- Archive every nickname era under stable NAS root `bloggers/UID<uid>/`. Merge legacy nickname roots non-destructively and record aliases in identity metadata.
- ASR empty output, placeholder-only output, or failure after retries is failure. Do not count it as processed, archive-complete, or eligible for local media deletion.
- Reject known ASR-only artifacts such as a standalone subtitle credit or repeated `Zither Harp`; never sign a completion marker for them. Failed runs write a media-SHA-bound `.asr-failure.json` receipt with every engine outcome.
- `verified_no_speech` is allowed only with a SHA-bound terminal receipt and one of these proofs: the complete track is at or below `-80 dB`; or media is at most 60 seconds and both Bcut and local Faster-Whisper return no valid speech twice; or a legacy at-most-30.5-second item has two local Whisper empty results. A failed provider call is not no-speech evidence.
- Full/default-favorites pipelines always retain local media. The only deletion path is `scripts/archive_douyin_blogger_outputs.py --delete-local-media`, after NAS size, SHA-256, ffprobe, and transcript validity all pass.
- Mandatory L1 applies to all enabled watchlist bloggers: the original 17 enabled bloggers and every later enabled addition. Correct clear ASR errors, punctuation, and paragraphing; only fully mechanical repetition with no information gain may be lightly merged when it clearly harms reading. Preserve normal口头禅、语气词、口语、原意、顺序、态度、数字、争议表达、狠话、粗口和有意义的强调。不审查、不和谐化、不书面化、不新增观点、不改成摘要。
- Weekly production must never use `--no-ai`. Obsidian sync is allowed only after the L1 gate reports `pending=0`, `invalid_source=0`, and enabled outputs have `ai_corrected: true`.
- Separate L2/enhanced-reading and `AI轻校正版` trees are retired. All enabled bloggers use the same faithful L1; TOP is rebuilt from that canonical corpus.

## Preflight

Before running any command, decide 4 things:

1. **Mode**
   - full pipeline
   - transcribe only
   - ranking only
   - backfill missing workbook media
2. **Target**
   - one or more Douyin home URLs
   - one or more known `--stem`
   - one or more downloaded folders
3. **Range**
   - all dates
   - or `--earliest` / `--latest`
4. **Media retention**
   - source media is always kept during download, ASR, organize, and L1
   - delete only through the verified NAS archive command

## Command Routing

Use the smallest command that matches the user's intent:

| User request | Command |
|---|---|
| 给 URL，想从下载到排序一条龙跑完 | `scripts/run_douyin_pipeline.py` |
| 已经下载完，只想转文字 | `scripts/transcribe_media_batch.py` |
| 已经有 transcript / workbook，只想重排年度 top | `scripts/organize_transcripts_by_year.py` |
| workbook 有作品但本地缺媒体，要补拉 | `scripts/fetch_missing_workbook_media.py` |
| 老宋聊就业要同步额外发布目录 | `scripts/sync_special_blogger_outputs.py` |
| 单条抖音分享链接只要“转文字/发文本文件” | `scripts/download_douyin_detail_links.py` + `scripts/transcribe_media_batch.py` |

### Single video link → transcript file

When Jinbo sends a Douyin short/detail video URL and only asks for a transcript file, do **not** run the full blogger/ranking pipeline. Use the direct-link path:

```bash
cd /Users/jinbo/AutomationCenter
OUT_DIR="/Users/jinbo/AutomationCenter/tmp/douyin_single_transcript_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"
/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master/.venv/bin/python \
  scripts/download_douyin_detail_links.py --out-dir "$OUT_DIR" 'https://v.douyin.com/xxxx/'
python3 scripts/transcribe_media_batch.py --folder "$OUT_DIR" --workers 1 --retries 2
```

Then verify the sibling `.txt` exists and is non-empty; on Telegram, deliver the text file directly with `MEDIA:/absolute/path/to/file` and keep the reply short. See `references/single-video-transcription.md` for the dependency/bootstrap notes from the 2026-07 direct-link run.

### Favorites distinction

Douyin default favorites and categorized favorite folders are different downloader modes:

- default favorites / 默认收藏 / 收藏作品: use `批量下载收藏作品(抖音)`, configured by `owner_url`, output stem `UID..._收藏作品`
- categorized favorites / 分类收藏夹 / 收藏夹作品: use `批量下载收藏夹作品(抖音)`, output stems `CID..._收藏夹作品`

Do not treat categorized `CID..._收藏夹作品` folders as proof that default favorites were downloaded. If the user asks broadly for 收藏内容, verify both `UID..._收藏作品` and `CID..._收藏夹作品` outputs.

On AutomationCenter, use `/Users/jinbo/AutomationCenter/scripts/run_douyin_default_favorites.py` for the default favorites pipeline. It temporarily runs DouK-Downloader with `run_command=5 9 Q Q`, then transcribes, normalizes, organizes, and rewrites time-sorted headers. Keep media until NAS archive is verified; only delete through the verified archive cleanup path.

如果用户同时给了 URL 和 `--stem`，优先确认是“增量补跑”还是“全量重跑”。

## Local Defaults

- The only configured download base is `paths.downloads_root` in `/Users/jinbo/AutomationCenter/config/settings.json`.
- Resolve derived paths through `/Users/jinbo/AutomationCenter/scripts/storage_paths.py`; do not hard-code or rebuild `Volume` paths.
- Production skill root: `/Users/jinbo/AutomationCenter/config/skills/douyin-hot-pipeline`
- Downloader repo: `/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master`
- ASR app: `/Users/jinbo/AutomationCenter/apps/语音转文字-mac`
- Canonical download root: `/Users/jinbo/AutomationCenter/downloads/douyin/bloggers`
- Ranked output root: `/Users/jinbo/AutomationCenter/downloads/douyin/bloggers/整理输出_按年份热度`
- Compatibility-only third-party path: `/Users/jinbo/AutomationCenter/workspace/TikTokDownloader-master/Volume`
- Default browser cookie choice: Firefox menu option `9`

## Recommended Commands

### 1. Full pipeline

Use this when the user gives one or more Douyin blogger URLs and wants the whole workflow completed.

```bash
python3 /Users/jinbo/AutomationCenter/config/skills/douyin-hot-pipeline/scripts/run_douyin_pipeline.py \
  --refresh-cookie \
  --keep-media \
  'https://www.douyin.com/user/xxx' \
  'https://www.douyin.com/user/yyy'
```

Common useful flags:

- `--earliest 2024/1/1`
- `--latest 2024/12/31`
- `--keep-media` (compatibility flag; retention is always on)
- `--skip-download`
- `--skip-transcribe`
- `--skip-organize`
- `--force-transcribe`

### 2. Transcribe only

Use this when downloads already exist and the user only wants `.txt` generation.

```bash
python3 /Users/jinbo/AutomationCenter/scripts/transcribe_media_batch.py \
  --folder '/Users/jinbo/AutomationCenter/downloads/douyin/bloggers/UID91977772972589_AI 人才圈-丁班长_发布作品' \
  --folder '/Users/jinbo/AutomationCenter/downloads/douyin/bloggers/UID1813521332186576_温迪老师大数据云计算高薪就业_发布作品'
```

Behavior:

- uses the local speech-to-text app at `/Users/jinbo/AutomationCenter/apps/语音转文字-mac`
- uses the verified `BcutASR` path on this machine
- converts media through `ffmpeg` when needed
- writes a sibling `.txt` next to each source media file
- after workbook matching, rewrites matching sibling `.txt` files with metadata headers above `=======下为正文============`, even if top ranking is skipped
- skips files that already have `.txt` unless `--force` is set

### 3. Ranking only

Use this when transcripts already exist and the user only wants yearly hotness outputs.

```bash
python3 /Users/jinbo/AutomationCenter/config/skills/douyin-hot-pipeline/scripts/organize_transcripts_by_year.py \
  --stem 'UID91977772972589_AI 人才圈-丁班长_发布作品' \
  --stem 'UID1813521332186576_温迪老师大数据云计算高薪就业_发布作品'
```

Useful filters:

- `--earliest 2024/1/1`
- `--latest 2024/12/31`

### 4. Rerank without redownloading

Use this when the user wants to skip download/transcribe and only refresh rankings from known stems.

```bash
python3 /Users/jinbo/AutomationCenter/config/skills/douyin-hot-pipeline/scripts/run_douyin_pipeline.py \
  --skip-download \
  --skip-transcribe \
  --stem 'UID91977772972589_AI 人才圈-丁班长_发布作品'
```

## Workflow

1. Identify the smallest matching command.
2. Confirm URLs, stems, and date range. Media retention is mandatory.
3. If the task includes downloading, decide whether to pass `--refresh-cookie`.
4. Run the command with only the needed targets.
5. Verify outputs:
   - downloaded media exists when download was requested
   - sibling `.txt` exists, contains real non-placeholder ASR text, and includes metadata headers above正文 when transcription was requested
   - ranked `topNNN_*.txt` exists when organize was requested
6. For weekly blogger archive runs, complete mandatory L1 and then refresh Obsidian:
   - run `/Users/jinbo/AutomationCenter/scripts/run_douyin_ai_until_complete.sh`
   - require L1 dry-run `pending=0` and `invalid_source=0`; do not bypass this with `--no-ai`
   - run `/Users/jinbo/AutomationCenter/scripts/sync_douyin_obsidian_vault.sh` to copy the validated Markdown view into the vault
   - verify `自动化中枢/01_博主/抖音脚本库/时间排序/<博主名>/` contains Markdown for newly created `.txt` transcripts
7. Report what succeeded, what failed, where outputs were written, and the Obsidian sync result.

## Failure Handling

- If `DouK-Downloader` stops on first-run language or disclaimer prompts, stop and tell the user to initialize it once manually, then rerun.
- If browser login is expired or cookie import fails, rerun with `--refresh-cookie` and explicitly mention browser choice `9`.
- If `/Users/jinbo/AutomationCenter/apps/语音转文字-mac` is missing, stop and report the exact missing path.
- If `ffmpeg` is missing, stop and explain that transcription cannot continue until media conversion is available.
- If ASR returns empty or placeholder-only text after retries, mark the item and blogger run failed. Do not archive it as complete or delete its source media.
- Weekly recovery may run the strict no-speech classifier after ASR failure. If any invalid source remains, the blogger run still fails and follows the normal hourly retry policy.
- Local media deletion accepts only a valid transcript completion marker or a trusted terminal receipt whose source path, bad-source backup SHA, evidence, and media SHA all verify. `non_transcribable_work` requires a non-video workbook type; unknown receipts keep media.
- If the user asks for ranking only, do not redownload or retranscribe by default.
- If the user asks for specific bloggers or stems, keep every command scoped to those targets only.

## Ranking Rules

When running yearly hotness ranking:

- group by `博主 / 年份`
- if a workbook contains multiple rows for the same `作品ID`, always use the row with the latest `采集时间` for metrics, title, tags, duration, publish time, and score; if `采集时间` is unavailable, use the later workbook row
- existing videos should not be re-downloaded just to refresh metrics, but both TOP outputs and sibling time-sorted `.txt` headers must be rewritten from the latest workbook metrics after each scan
- compute `综合分 = 评论×4 + 收藏×3 + 分享×2 + 点赞×1`
- sort by 综合分 descending, then comment/favorite/share/like counts
- use `作品话题` as tags first; if empty, derive tags from `作品描述` hashtags
- use `作品描述` as the title source; if hashtags exist, keep the text before the first `#` as `标题`
- write each result as `topNNN_*.txt`
- keep fixed headers in this order: `评论 / 收藏 / 分享 / 点赞 / 视频时长 / 发布时间 / 综合分 / 标题 / 标签`
- insert `=======下为正文============` before正文
- read transcript text with fallback encodings `utf-8`, `utf-8-sig`, `gb18030`
- sibling time-sorted `.txt` outputs must use the same header/body format as ranked `topNNN_*.txt`, so downstream analysis can consume either format
- when verifying a weekly scan, sample at least one repeated `作品ID` when available and confirm the `.txt` header matches the latest `采集时间` row in `downloads/douyin/bloggers/Data/<stem>.xlsx`

## Output Contract

Default report structure:

1. `执行模式`
   - full pipeline / transcribe only / ranking only / backfill
2. `处理目标`
   - URLs, stems, or folders actually used
3. `执行结果`
   - which scripts ran successfully
   - which step failed, if any
4. `输出位置`
   - ranked output root
   - any special synced folders
5. `后续建议`
   - whether to rerun with `--refresh-cookie`
   - whether to keep media next time
   - whether a missing dependency needs manual fixing

## Notes

- Treat `downloads/douyin/bloggers/Data/UID*.xlsx` as the source of truth for metrics and tags.
- Treat the latest `采集时间` row per `作品ID` as the source of truth inside that workbook.
- Match each workbook row back to the downloader-generated filename pattern before reading sibling transcript text.
- NAS archive and local `.txt` refresh are not enough for Obsidian visibility. After a weekly archive, finish all-enabled L1 with `run_douyin_ai_until_complete.sh`, pass the L1 completeness gate, then run `sync_douyin_obsidian_vault.sh`.
- Expect image posts to be unmatched because they do not produce transcribed `.txt` 正文.
- For direct-link 补下载, `scripts/fetch_missing_workbook_media.py` must treat existing `.txt` as already processed, even if the original `.mp4` was deleted.
- Special case: when the processed stem is `UID1822310415739536_老宋聊就业_发布作品`, also run the special output sync into `/Users/jinbo/Documents/2026/老宋系统/我的脚本/已发布` and `/Users/jinbo/Documents/2026/老宋Claude/我的脚本/已发布`.
