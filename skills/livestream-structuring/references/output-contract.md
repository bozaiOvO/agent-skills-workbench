# Output Contract

The final reading document should be useful for human reading, business review, and later knowledge-base sync.

## Required Sections

```markdown
# 结构化阅读稿

## 录制信息

## 阅读说明

## 整场连麦咨询

## 普通 QA 问答

## 主播主动讲解

## 分段核对版
```

Existing AutomationCenter files may use `整场连麦咨询（跨分段合并版）`; that is acceptable.

## Call-In Format

```markdown
### L01. 主题（跨N个分段合并）

**来源定位：** 分段 02 中段 -> 分段 03 前段
**连麦状态：** 已结束 / 未明确结束 / 延续到下一分段 / 可能未完整截取
**案例价值：** 高 / 中 / 低

**连麦人基本情况（AI提取，非原话）：**
- 学历：
- 专业/方向：
- 届别/年龄：
- 当前状态：
- 经历/项目：
- 目标方向：
- 关键限制：

**连麦大致内容（AI概括，非原话）：**
自然说明这个人是什么情况、问了什么、主播怎么判断、最后落到什么结论。

**核心建议（AI提取，非原话）：**
1.
2.
3.

**完整对话（已润色，按真实顺序融合）：**

**连麦人：** ...

**主播：** ...

**沟通技法拆解（AI提取，非原话）：**
1.
2.
3.
```

Rules:

- one caller, one `Lxx`
- background summary appears once
- main explanation appears once
- complete dialogue follows real order
- segment labels only appear in source location or final check section
- polished dialogue may remove filler and fix ASR errors, but cannot invent facts
- `完整对话` is not a summary. Preserve the substantive back-and-forth, including the caller's background, host follow-up questions, constraint checks, objections, decision reasoning, and final advice.
- For a normal real call-in, keep roughly 70%-90% of meaningful speaker turns. Remove only filler, repeated口癖, obvious ASR garbage, and unrelated room operations.
- Do not compress a multi-minute consultation into 4-8 representative lines. If the case needs only a few lines, it is usually ordinary QA, not `Lxx`.
- Host explanations addressed to the caller must stay inside the dialogue, even if they are long. Only room-facing sales chatter such as福袋、扣6、资料领取、灯牌 can be omitted or summarized.
- If a call spans multiple segments, merge it in chronological order and keep the full substantive dialogue across all segments; do not keep only the conclusion.
- The document is also a communication-skill learning asset. Preserve how the host asks, interrupts, jokes, challenges assumptions, calculates costs, compares options, applies pressure, and closes the consultation.
- Add `沟通技法拆解` after the dialogue. Extract the host's actual consultation technique, such as opening diagnosis, follow-up chain, reframing, cost/time calculation, pressure test, risk warning, offer/course boundary, and closing move.
- Treat missing `沟通技法拆解` as a hard quality failure for any real call-in `Lxx`.
- Reject outputs that contain Codex/runtime console logs, command output, session ids, or prompt templates instead of the final reading document.

## QA Format

```markdown
### Q01. 主题

**来源定位：** 分段 01 中段

**问题：**

**原文优化版（保留表达风格，增强可读性）：**
基于主播原回答整理成可阅读文本。保留主播的说法、语气、判断顺序、反问、例子和边界；修正 ASR 错字、技术名词和断句；删除空转口癖、重复废话和无关运营话术；不要编造新事实，不要改成鸡汤，也不要压成要点。短 QA 可 1 段，深度 QA 通常 2-5 段。

**回答结论：**

**回答要点：**
1.
2.
3.

**回答展开（适用于深度 QA，AI整理，非原话）：**
保留主播的判断链路、例子、对比、边界条件、风险提醒和下一步建议。短 QA 可删除本字段。

**适用场景：**

**回答策略（AI提取，非原话）：**
```

Rules:

- independent comment question only
- no long transcript paste
- no duplicated call-in follow-up questions
- omit low-value repeated questions
- every retained `Qxx` must include `原文优化版（保留表达风格，增强可读性）` before the structured conclusion
- `原文优化版` is polished source-like prose, not raw transcript and not a summary; it should preserve the host's voice, sequence, examples, questions, and boundaries while removing filler and ASR noise
- in pure-QA livestreams, `Qxx` is the main reading asset; preserve substantial answers as deep QA, not thin 2-3 bullet summaries
- for deep QA, keep the conclusion, reasoning, example/comparison, risk boundary, and suggested next action when the raw answer contains them
- do not split one substantial answer into a fake `Qxx` plus `Txx`; if the host's teaching is caused by that question, keep it inside that `Qxx`
- short independent QA can stay compact, but substantial career/IT/training answers should remain useful for later业务复盘

## Host-Led Teaching Format

```markdown
### T01. 主题

**来源定位：** 分段 01 后段

**核心观点：**

**展开内容：**
1.
2.
3.

**业务价值：**
```

Rules:

- only keep standalone teaching with reuse value
- no full-script rendering
- no fake QA formatting

## Final Check Section

`分段核对版` is for audit only.

It may say:

```markdown
- 分段 01：真实连麦 / 普通 QA / 主动讲解 / 运营互动 / 无沉淀价值
- 分段 02：...
```

This section must not become the main reading structure.
