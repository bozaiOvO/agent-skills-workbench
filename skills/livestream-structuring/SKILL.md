---
name: livestream-structuring
description: "把直播原始逐字稿合并整理成可读文档。用于区分连麦、问答和主播讲解，不负责下载转写。"
metadata:
  owner: jinbo
  lifecycle: production
---

# Livestream Structuring

Use this skill when the job is to make livestream transcripts readable and auditable:

`segment_*/raw_transcript.txt -> call-in consultation / ordinary QA / host-led teaching -> merged reading document`

This is the rule source for livestream decomposition. It is not a downloader, ASR tool, Feishu sync tool, or livestream conversion coach.

## When To Use

- Rebuild `02_原文与结构化内容.md` from livestream raw transcripts.
- Decide whether a section is a real call-in consultation, deep QA, ordinary QA, host-led teaching, operations chatter, or low-value noise.
- Merge the same caller across multiple segments into one complete case.
- Audit whether a generated livestream reading document is safe to sync to Feishu or Obsidian.
- Fix cases where an old `qa_verbatim.md` split one caller, produced an empty draft, or treated sales chatter as a call-in.
- Preserve call-in consultations as communication-skill learning material, especially how the host expands, challenges, reframes, calculates costs, and closes.

## Inputs

Prefer first-source files:

- `segment_*/raw_transcript.txt`
- optional segment context: previous segment tail and next segment head
- optional old `qa_verbatim.md`, only as a suspect artifact for comparison
- target output path, usually `02_原文与结构化内容.md`

## Workflow

1. Read [references/source-and-boundaries.md](references/source-and-boundaries.md).
2. Classify content using [references/content-type-rules.md](references/content-type-rules.md).
3. Render the result using [references/output-contract.md](references/output-contract.md).
4. If a document already exists, run `scripts/audit_live_doc.py` before syncing or treating it as final.
5. When old segment outputs conflict with raw transcript evidence, rebuild from raw instead of repairing the old draft.

## Output Contract

Default final document sections:

1. `整场连麦咨询`
2. `普通 QA 问答`
3. `主播主动讲解`
4. `分段核对版`

Call-in content must keep a polished but high-fidelity complete dialogue. It is a learning asset for consultation technique, not a short summary. Pure QA livestreams are also learning assets: preserve the host's answer logic, examples, boundaries, and judgment chain as deep QA notes instead of compressing each answer into a few generic bullets. Every retained QA must include `原文优化版（保留表达风格，增强可读性）` so the user can learn the host's phrasing and expansion style. Ordinary short QA and host-led teaching must be summarized structurally and must not repeat the whole livestream script.

## Exclusions

- Downloading Douyin live recordings belongs to `douyin-hot-pipeline` or AutomationCenter scripts.
- Audio/video transcription belongs to the ASR pipeline.
- Livestream positioning, conversion, offer, pacing, and CTA coaching belongs to `livestream-optimizer`.
- Deep business review and素材提炼 should run after this skill has produced stable `Lxx/Qxx/Txx` references.
- Feishu knowledge-base sync is downstream. This skill only says whether the document is safe enough to sync.

## Quality Gate

Before declaring success, check:

- raw transcript was treated as the source of truth
- same caller is not split into multiple main-reading `Lxx` cases
- `完整对话` keeps the substantive consultation process instead of a few representative lines
- the host's communication technique is preserved or explicitly extracted
- every real call-in `Lxx` includes `沟通技法拆解`; missing this is a failed document, not a soft warning
- operations chatter is not promoted into `Lxx`
- deep QA in pure-QA livestreams preserves enough answer detail for business reference
- ordinary short QA and host-led teaching are not copied as full raw transcript
- QA answers are not over-compressed into generic 2-3 bullets when the raw answer contains concrete reasoning, examples, comparisons, or risk boundaries
- every retained QA includes `原文优化版（保留表达风格，增强可读性）`
- empty or tiny reading documents are blocked
- generated documents containing Codex/runtime console logs are rejected and the last good reading document should be restored
- source locations are kept for human review

For deterministic checks:

```bash
python3 /Users/jinbo/.agents/skills/livestream-structuring/scripts/audit_live_doc.py /path/to/02_原文与结构化内容.md
```
