---
name: ipdna拆解
description: Analyze a local folder of Chinese short-video scripts/transcripts to extract a creator's IP DNA, generate a human-readable voice DNA brief plus structured criteria JSON, then produce + QA migrated scripts for persona-led content businesses such as education, consulting, services, career planning, AI/AIGC/tech training, and similar knowledge/commercial IPs. Use when the user asks to 深度分析竞品脚本目录、提炼内容基因、克隆爆款结构、做 IP DNA 判据、自动生成新脚本，尤其适用于真人 IP，不适用于剧情号、搬运号、纯整活号。
---

# IPDNA拆解

这个 skill 现在不是“某个赛道专用外挂”，
而是 **真人 IP 内容迁移底座**。

它适合的核心对象是：

- 卖课程
- 卖咨询
- 卖服务
- 卖判断
- 卖职业结果
- 卖知识型信任

典型场景包括：

- 就业培训
- 职业教育
- 转行培训
- 职业规划 / 就业咨询
- AI / AIGC / Agent / 云计算 / 编程 / 数字技能课程
- 家长决策型内容
- 个人品牌型直播 / 短视频获客业务

它默认服务的是 **真人 IP**，
不是剧情号、搬运号、纯靠剪辑表演的账号。

这个 skill 不负责把输出写成“某人本人附体”。

它负责 4 件事：

1. 提炼竞品的 **内容能力**
2. 提炼竞品的 **文风 DNA / voice DNA**
3. 转成 **可执行判据**
4. 迁移成 **适合当前业务** 的新脚本

如果当前仓库里有品牌文件（如 `Claude_codex.md` / `Claude.md`），那是 **品牌覆写层**；
如果没有，就按通用知识型 / 教育型 / 咨询型 IP 业务执行。

## 何时触发

用户出现这些需求时使用：

- “分析这个目录下的几百篇脚本”
- “提炼某个博主的 IP DNA / 爆款基因”
- “把这个博主的方法迁移到我的新赛道”
- “自动生成 criteria json / 判据文件 / 质检标准”
- “结合我的业务自动写脚本”
- “这个账号为什么像他自己”
- “帮我把风格拆出来，避免 AI 味”

## 默认输出物

除非用户明确指定别的文件名，否则默认保存：

- `style_report_codex.md`
- `voice_dna_codex.md`
- `IP_Criteria_codex.json`
- `draft_script_codex.md`
- `final_script_codex.md`

## 使用时的四层结构

### 第一层：竞品能力层

从语料中提取：

- 钩子
- 结构
- 节奏
- 判断方式
- 情绪推进
- 转化承接

### 第二层：文风 DNA 层

这层不是写论文，
而是回答 6 个实际问题：

1. 这个 IP 怎么定义“真实”
2. 这个 IP 靠什么让人信
3. 这个 IP 站在什么位置说话
4. 这个 IP 怎么组织句子和节奏
5. 这个 IP 的情绪强度和权力姿态是什么
6. 这个 IP 哪些地方最容易被 AI 写塌

当第一次分析一个新 IP，
或者生成结果总是“像正确材料，不像真人”，
必须补这一层。

### 第三层：业务适配层

判断这个方法能不能迁移到当前业务：

- 能不能吸引目标客户
- 会不会伤转化
- 会不会让人听不懂
- 会不会不符合行业常识
- 会不会和品牌边界冲突

### 第四层：品牌覆写层

如果当前项目有品牌文件，读取后再覆写：

- 受众是谁
- 决策者是谁
- 哪些方向能卖
- 哪些话不能说
- 要偏流量、认知、信任还是转化

## 快速工作流

1. **确认输入**
   - 语料目录
   - 新产品 / 新赛道
   - 目标受众
   - 是否直接出脚本
2. **跑语料扫描**
   - 运行 `scripts/scan_corpus_codex.py`
3. **读本地业务上下文**
   - 优先尝试：
     - `Claude_codex.md`
     - `Claude.md`
     - 品牌 / 项目说明文件
   - 如果没有，就按通用知识型 IP 业务执行
4. **深读代表样本**
   - 覆盖多个年份
   - 高热样本为主
   - 补充少量中低热样本对照
5. **先做文风 DNA 压缩**
   - 输出 `style_report_codex.md`
   - 输出 `voice_dna_codex.md`
   - 读取 `references/style-dna-framework_codex.md`
6. **生成 `IP_Criteria`**
   - 读取 `references/criteria-schema_codex.md`
7. **生成初稿**
8. **执行 QA 闭环**
   - 读取 `references/qa-rubric_codex.md`
9. **输出终稿**

## 通用知识型 IP 业务默认假设

当没有品牌说明文件时，默认这样理解业务：

- 业务本质：卖结果、卖判断、卖信任，不只是卖知识
- 用户常见关切：
  - 值不值得信
  - 适不适合自己 / 孩子
  - 有没有出路
  - 花时间花钱值不值
- 常见决策者：
  - 学生本人
  - 家长
  - 转行成年人
  - 咨询采购者

## 输出前必须先判断这 6 件事

### 1. 这条内容打谁

- 家长
- 在校生
- 应届生
- 往届待业
- 转行人群
- 企业主 / 咨询客户

### 2. 这条内容做什么

- 流量
- 认知
- 信任
- 转化

### 3. 竞品最值钱的能力是什么

不是“像不像”。

而是：

- 开头能力
- 结构能力
- 判断能力
- 反转能力
- 权力姿态
- 转化承接能力

### 4. 这个 IP 靠什么让人信

必须说清：

- 靠经历
- 靠结果
- 靠判断
- 靠身份
- 靠故事
- 还是靠直播间临场压迫感

### 5. 哪些能借，哪些不能借

必须拆分：

- `can_borrow`
- `cannot_borrow`
- `must_rewrite`

### 6. 这条是否安全

必须检查：

- 有无过度承诺
- 有无自伤
- 有无脱离当前业务实际
- 有无目标受众听不懂的地方
- 有无为了像竞品而把品牌边界写穿

## 关于文风 DNA 的使用原则

不要把那套大而全的哲学框架原样塞进生成 prompt。

正确做法是：

1. 先用深分析看透
2. 再压缩成 `voice_dna_codex.md`
3. 再结构化进 `IP_Criteria_codex.json`
4. 最后拿压缩后的判据去生成

也就是说：

`深分析是上游研究层，不是下游废话层。`

## 质检闭环

至少做这 9 测：

- 结构吻合度
- 钩子有效性
- IP 味儿浓度
- 权力姿态一致性
- 世界观一致性
- 反 AI 味测试
- 去重测试
- 受众适配测试
- 业务安全测试

如果当前业务是课程 / 培训 / 咨询类，再额外做：

- **转化承接测试**
  - 最后 CTA 是否自然
  - 是否会让人觉得硬广

## 关于“自动循环”

默认执行闭环重写，
直到通过。

但不要假装无限。

如果连续 2 轮没有结构性提升，
就停止伪重复，
报告卡点：

- 是源语料本身不够清晰
- 还是迁移目标太模糊
- 还是品牌约束和竞品结构冲突
- 还是 voice DNA 压缩得不够准

## 何时读取参考文件

- `references/style-dna-framework_codex.md`
  - 当你第一次分析一个新 IP
  - 或者生成结果 AI 味太重
  - 或者用户明确要“文风 DNA / 风格拆解”
- `references/criteria-schema_codex.md`
  - 当你要写 `IP_Criteria*.json`
- `references/qa-rubric_codex.md`
  - 当你开始闭环质检

## 何时用子代理

只有用户明确允许 delegation / subagent / parallel work 时再用。

否则默认本地完成。

## 产出标准

合格的结果必须满足：

- 像竞品的“内容能力”，不像竞品的“外壳”
- 像竞品的“权力姿态”，不像竞品的“口头禅堆砌”
- 像当前业务在说话，不像硬缝合
- 有可复用判据，不是一次性灵感
- 有研究层、判据层、初稿层、终稿层，不是只给一版文案
