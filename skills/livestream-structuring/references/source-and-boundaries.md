# Source And Boundaries

## First Source Principle

`raw_transcript.txt` is the source of truth.

Old `qa_verbatim.md`, old Obsidian documents, and previous AI summaries are only secondary references. If they conflict with raw transcripts, trust raw transcripts and rebuild.

Use old drafts only to identify what likely went wrong:

- empty output
- one caller split across segments
- sales or operations chatter mislabeled as call-in
- call-in questions duplicated into ordinary QA
- host teaching copied as a full transcript
- pure-QA livestreams where every answer was compressed into thin 2-3 point summaries

## Pipeline Boundary

This skill owns only livestream structure:

```text
raw transcript -> classify -> merge -> structured reading document -> quality gate
```

It does not own:

- download
- ASR transcription
- NAS archive
- Feishu upload
- business analysis
- article writing
- short-video素材提炼

Those stages can consume the stable `Lxx/Qxx/Txx` output after this skill finishes.

## Main Reading Principle

The main reading document is not a second full transcript.

Keep complete polished dialogue only for real call-in consultations, because the consultation case itself is the asset.

For pure-QA livestreams, QA answers are the main asset. Output structured deep QA notes that preserve the host's useful reasoning:

- conclusion
- reasoning chain
- examples or comparisons
- constraints and risk boundaries
- suggested next action
- reusable answer strategy

Do not reduce a substantial host answer to a few generic bullets. The user should still be able to learn how the host answered, persuaded, compared options, and handled edge cases.

For ordinary short QA and host-led teaching, output structured reading notes:

- question and answer points
- core viewpoint
- applicable scenario
- business value

Do not paste long raw blocks just because they are available. The target is "high-fidelity structured notes", not full raw transcript and not thin summary.

## Bad Draft Fallback

Rebuild from raw when any of these appear:

- final document is empty or suspiciously short
- a known call-in session disappeared
- one caller appears as multiple main-reading `Lxx` blocks
- large sections are labeled `主播主动讲解` only because the segment prompt failed
- document says no real call-ins while raw transcript contains clear caller background and multi-turn diagnosis

AutomationCenter fallback command pattern:

```bash
python3 /Users/jinbo/AutomationCenter/scripts/rebuild_live_obsidian_june.py \
  --month YYYY-MM \
  --owner 主播名 \
  --date YYYY-MM-DD \
  --label HH-MM-SS \
  --regenerate-session-from-raw
```
