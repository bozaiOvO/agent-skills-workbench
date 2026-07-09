# 天涯合集压缩策略审计

## 当前状态

- 原始真源：`/Volumes/素材库/抖音素材库/天涯合集`
- 本地调用语料：`assets/text-corpus`
- 本地调用语料体积：约 11M
- 原始真源体积：约 23G

## 文件类型判断

| 类型 | 数量 | 原始体积 | 处理策略 |
| --- | ---: | ---: | --- |
| `.md` / `.txt` | 18 | 约 8.5M | 直接作为本地语料层，按板块合并并切 chunk。 |
| `.docx` | 6 | 约 1.1M | 可稳定抽文本；适合转 markdown/jsonl。 |
| `.epub` | 6 | 约 36M | 可抽正文；适合转 markdown/jsonl，但需清理目录、版权页、乱码。 |
| `.pdf` | 276 | 约 9.3G | 可文本抽取的 PDF 适合压成 markdown/jsonl；扫描版或结构坏的 PDF 只保留 NAS 真源，后续需要 OCR/人工复核。 |
| `.zip` | 6 | 约 13.2G | 不直接给 skill 检索；作为 NAS 真源归档。需要时先解包、修文件名编码，再抽文本。 |
| `.chm` | 2 | 约 51M | 不作为默认调用语料；可后续专项转 HTML/text。 |
| 图片 / 音频 / PPT / mobi / azw3 / doc | 少量 | 约 25M | 不作为默认调用语料；保留 NAS 真源，需要时专项转换。 |

## 为什么本地只保留 11M

Agent 最擅长稳定读取的是纯文本：

- markdown
- txt
- jsonl chunks
- 带来源路径的 manifest

所以本地层不是保存 PDF/zip 原件，而是保存“已经提取、清洗、切块后的文本”。这能让每次 skill 调用快速检索，不被 NAS 延迟、PDF 解析失败、压缩包解码问题拖慢。

## 当前本地语料层内容

本地语料来自原 `天涯合集/提取文本`，覆盖 13 个板块：

- kk合集【无水印】
- 中医命理
- 其他
- 国际观察
- 天涯小说
- 天涯故事
- 天涯杂谈
- 情感天地
- 煮酒论史
- 经济论坛
- 股市楼市
- 莲蓬鬼话
- 资料大合集

构建结果：

- `manifest.jsonl`：13 条源文件记录
- `chunks.jsonl`：802 个检索块
- `boards/`：按板块合并后的 markdown
- `items/`：单源文件 markdown

## 后续增量建议

如果要继续提升天涯 skill 的高保真度，不建议把 23G 原包搬回本地。建议按这个顺序增量：

1. 从 NAS 真源里挑重点 PDF，用 OCR/文本抽取补充到 `assets/text-corpus/items/`
2. 对四个大 zip 做专项解包，先修复文件名编码，再抽 PDF/docx/txt
3. 对抽出来的文本做人工抽样，删掉目录页、广告页、乱码页
4. 重新跑 `scripts/build_text_corpus.py` 或增量合并到 `chunks.jsonl`

默认调用时，只读本地 `assets/text-corpus`。
