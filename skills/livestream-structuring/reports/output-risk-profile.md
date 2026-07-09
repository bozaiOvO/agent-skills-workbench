# Output Risk Profile

## Main Risks

1. The model reads old `qa_verbatim.md` instead of raw transcripts and repeats old mistakes.
2. One caller is split into multiple `Lxx` cases because the video was cut into segments.
3. Sales, payment,资料领取, or room operations are mislabeled as call-in consultations.
4. Ordinary QA and host-led teaching become a second full transcript.
5. A tiny or empty document is synced to Feishu because the pipeline treated generation as successful.

## Required Guards

- Prefer `segment_*/raw_transcript.txt`.
- Mark uncertain call endings as `未明确结束` or `可能未完整截取`.
- Keep full dialogue only for real call-ins.
- Run `scripts/audit_live_doc.py` before sync or manual approval.
- Rebuild from raw when the audit blocks.

## Missing Evidence

- `missing evidence`: no formal fixture set yet for 2026-06-08 K哥 L05/L06.
- `missing evidence`: no formal fixture set yet for 2026-06-09 empty draft.
- `missing evidence`: no automatic semantic duplicate detector for same-caller merge.
