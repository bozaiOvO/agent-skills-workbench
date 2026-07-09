# Tianya Text Corpus

本目录是 `tianya-perspective` 的本地轻量语料层，用于 Agent/Skill 每次调用时快速检索。

- 本地语料层：`assets/text-corpus/`
- 原始真源归档：`/Volumes/素材库/抖音素材库/天涯合集`
- 构建来源：原 `天涯合集/提取文本`
- 构建脚本：`scripts/build_text_corpus.py`

## 目录说明

- `boards/`：按板块合并后的 markdown，适合人工阅读和快速检索。
- `items/`：每个源文件抽取后的 markdown。
- `chunks.jsonl`：面向 Agent 的分块语料。
- `manifest.jsonl`：每个源文件的来源、板块、状态和输出路径。
- `build-report.json`：本次构建摘要。

## 原则

PDF、zip、chm、图片、音频等原始文件不放在本地语料层里。它们保存在 NAS 真源归档中。

Skill 调用时应优先读取本目录；只有需要复核原件、重新抽取或补充 OCR 时，才访问 NAS 真源。
