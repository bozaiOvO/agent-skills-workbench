# 语料总览

## 路径

- 数据集根目录：`/Users/bo/Desktop/TikTokDownloader-master/Volume/Zhoulifeng-Streaming-Dataset`

## 当前可见结构

### 1. 原始直播文本

- `orginal_text/`
- 约 `769` 份 `.txt`
- 覆盖 `2022-2025`
- 年份分布大致为：
  - `2022`: 173
  - `2023`: 196
  - `2024`: 160
  - `2025`: 239

这是风格复刻和原始判断的主语料层。

### 2. 标点恢复文本

- `refine_data_process/01_punc_transcripts/`
- 约 `98` 份 `.txt`

适合在原始稿过于口水、断句差时做辅助阅读，但不能完全替代原始稿。

### 3. 清洗后的 SFT 数据

- `refine_data_process/10_feng_sft_train.json`
- 当前本地可读样本数：`9297`

这层非常适合做：

- 问答模板
- 稳定立场提炼
- 更短、更干净的输出骨架

### 4. 长逻辑 CoT 数据

- `11_long_cot_filtered_9486_150-300.jsonl`
- `11_long_cot_filtered_12330_100-250.jsonl`

注意：当前本地看到的至少一个文件是 **Git LFS 指针**，不是实际 JSONL 内容。

因此当前 skill 默认：

- 不把它当已读完的真实语料
- 只把它视为“项目曾经产出过长逻辑层”的信号

## 标题层面的粗分类

粗看标题，核心簇大致是：

- `解答世间万物`：约 `445`
- `be` 系：约 `109`
- 其余为旅行、地区、直播日常、财经、历史、登山等专题

直观结论：

- `解答世间万物` 是主干母体
- `be` 系是偏夜聊、状态流、延伸表达的分支
- 2024-2025 的专题化程度明显增加

## README 可吸收的关键结论

这个数据集 README 的价值不在宣传，而在“数据漏斗”。

可直接吸收的操作性结论：

1. 原始 ASR 不能直接当高质量知识库，先要清噪
2. 文本去重、PPL 过滤、聚类降噪、规则过滤是必要步骤
3. 语义去重和重写后得到的 SFT 底库，最适合提炼稳定观点
4. 长逻辑 CoT 是额外层，不是主底库

所以当前默认策略是：

- **像峰哥说话**：先读 `orginal_text`
- **提炼稳定问答**：再看 `10_feng_sft_train.json`
- **想找长逻辑**：先确认 CoT 文件不是 LFS 指针

## 当前使用建议

如果是用户对话型任务，默认顺序：

1. `scripts/search_corpus.py`
2. `references/domain-router.md`
3. `references/mental-models.md`
4. `references/voice-dna.md`
5. 需要年份变化时再看 `references/evolution-timeline.md`
