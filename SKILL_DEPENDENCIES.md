# Skill Dependencies

This file answers two questions for every dependency-sensitive skill:

1. Is the corpus/data included in GitHub?
2. If not, what local path or runtime state should point to it?

## Path Rule

Use repo-relative paths whenever the corpus is bundled:

- `<repo>/skills/<skill-name>/assets/...`
- `<repo>/skills/<skill-name>/references/...`
- `<repo>/skills/<skill-name>/scripts/...`

For data that should not be committed, prefer a machine-local data source:

```bash
mkdir -p ~/.agents/data
```

Then point scripts to it with environment variables instead of hardcoding one Mac's directory layout.

## Dependency Matrix

| Skill | In GitHub? | External path or runtime | Mac mini action |
|---|---:|---|---|
| `kge-perspective` | Yes. `assets/corpus/` has 1213 transcript `.txt` files; `references/research/` is also bundled. | Optional override: `KGE_CORPUS_DIRS` or `KGE_CORPUS_DIR`. Legacy fallback: `~/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/程序员K哥`. | No extra corpus needed for normal use after clone. Use env var only if replacing/updating corpus. |
| `shuiqiupao-perspective` | Yes. `assets/corpus/` has 697 水球泡 files and `assets/paopaoshuo/` has 546 泡泡说 files. | Optional override: `SHUIQIUPAO_CORPUS_DIRS` or `SHUIQIUPAO_CORPUS_DIR`, colon-separated for multiple dirs. Legacy fallbacks under `~/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/`. | No extra corpus needed for normal use after clone. |
| `tianya-perspective` | Yes for the working research layer. `references/research/boards/` has 26 board analysis/source Markdown files. | Raw Tianya dump is not required for normal answers and is not treated as the synced source. | No extra path needed unless rebuilding the research files from raw board exports. |
| `don-ge-skill` | Partly. Distilled references plus `corpus-map.md` and `corpus-manifest.json` are bundled; raw source transcripts are not bundled. | Refresh source: `DON_GE_CORPUS_DIR`. Legacy fallback: `/Users/bo/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/dontbesilent 聊赚钱`. | Normal use works from bundled references. To refresh or verify raw source, copy/sync corpus locally and set `DON_GE_CORPUS_DIR`. |
| `fengge-perspective` | Partly. Distilled references and search helper are bundled; raw `Zhoulifeng-Streaming-Dataset` is not bundled. | Required for search mode: `FENGGE_DATASET_ROOT` or `ZHOUFENG_DATASET_ROOT`. Legacy fallback: `/Users/bo/Desktop/TikTokDownloader-master/Volume/Zhoulifeng-Streaming-Dataset`. | Without the dataset, use the bundled references only and do not claim fresh corpus search. |
| `程序员luck视角` | Partly. Distilled references and search helper are bundled; raw 111-file corpus is not bundled. | Required for search mode: `LUCK_CORPUS_DIRS`, `LUCK_CORPUS_DIR`, or `PROGRAMMER_LUCK_CORPUS_DIR`. Legacy fallback: `~/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/程序员luck`. | Without the corpus, use the bundled references only and label answers as framework inference when needed. |
| `livestream-optimizer` | Partly. Rubric, syllabus, concept index, and methodology are bundled; the 21 transcript course folder is not bundled. | Required for transcript search: `LIVESTREAM_COURSE_DIR`. Legacy fallback: `/Users/bo/Documents/2026/陈晶直播课程`. | Normal review works from bundled methodology plus user transcript. Course evidence search needs local course folder. |
| `qieman-weekly-links` | Script is bundled. A generated Markdown snapshot is bundled at `assets/且曼周刊推荐内容链接汇总.md`. Feishu login state, weeklies input JSON, and raw extraction JSON are not bundled. | Requires logged-in Feishu Chrome CDP session for fresh extraction. Inputs/outputs can be set with `QIEMAN_WEEKLIES_PATH`, `QIEMAN_OUTPUT_JSON`, `QIEMAN_OUTPUT_MD`, `CDP_PORT`, `FEISHU_DOMAIN`. | Sync the skill normally. The bundled Markdown can be read immediately after clone; fresh reruns need local Feishu login/CDP and a weeklies JSON. Do not expect `/private/tmp` files to sync. |
| `wechat-daily` | Script is bundled. WeChat databases, database keys, config, and generated reports are not bundled. | Requires local WeChat Mac 4.x data under `~/Library/Containers/...`, plus `~/.config/wechat-daily.json` and `~/.config/wechat-keys.json`. | Configure on each Mac separately. Never commit keys or private WeChat databases. |
| `wx-cli` | Skill instructions are bundled. The `wx` binary, WeChat app, local WeChat databases, memory-scanned keys, daemon cache, and `~/.wx-cli/config.json` are not bundled. | Requires installing `@jackwener/wx-cli` or the upstream install script, then per-machine `wx init`. On macOS, setup may re-sign WeChat, reset TCC privacy records, restart WeChat, and require `sudo`. | Sync the skill normally, but install/init the CLI separately on each Mac with explicit user confirmation. |
| `agent-browser` | Skill instructions are bundled. Browser sessions and login state are runtime state. | Requires local Chrome/Chromium/CDP availability depending on task. | Sync the skill normally. Install/init the `agent-browser` CLI on each Mac when needed; browser sessions and auth remain per machine. |

Most other synced skills are instruction-only or include their needed references/assets in the repository. If a skill later adds corpus, update this file and the top of that skill's `SKILL.md` in the same commit.

## Recommended External Data Layout

For external corpora on a second Mac, use one local data root:

```bash
mkdir -p ~/.agents/data

export FENGGE_DATASET_ROOT="$HOME/.agents/data/fengge-perspective/Zhoulifeng-Streaming-Dataset"
export LUCK_CORPUS_DIR="$HOME/.agents/data/programmer-luck/程序员luck"
export DON_GE_CORPUS_DIR="$HOME/.agents/data/don-ge-skill/dontbesilent-聊赚钱"
export LIVESTREAM_COURSE_DIR="$HOME/.agents/data/livestream-optimizer/陈晶直播课程"
```

If an agent host does not inherit shell environment variables, use the explicit script flag when available, such as `--corpus-dir`, or create a local symlink from the legacy fallback path to the data root.

## Verification

Run:

```bash
bash scripts/check-skill-dependencies.sh
```

This reports bundled corpus counts and which external/runtime dependencies are missing on the current Mac.
