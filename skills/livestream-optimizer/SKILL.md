---
name: livestream-optimizer
description: Use when the user wants to turn livestream course transcripts and their own livestream transcripts into a repeatable coaching workflow. Diagnose positioning, persona, offer, structure, pacing, interaction, and CTA; then give transcript-based rewrites and next-session adjustments for personal-IP, knowledge, lead-gen, and conversion-oriented livestreams.
---

# Livestream Optimizer

Use this skill for Chinese livestream coaching, especially personal-IP, knowledge, lead-gen, and conversion-oriented rooms. The reference transcript library lives at `/Users/bo/Documents/2026/陈晶直播课程`; do not read the whole folder by default. Start with [references/course-map.md](references/course-map.md), then search or open only the 1-3 most relevant files.

If the user wants to turn livestream `raw_transcript.txt` files into `Lxx/Qxx/Txx` structured reading documents, route to `$livestream-structuring` instead. This skill can consume that structured output later for coaching, but it should not own call-in merging, QA classification, first-source rebuild, or pre-sync quality gates.

## When To Use

- Review a past livestream transcript.
- Diagnose why a livestream feels weak, messy, or low-converting.
- Rewrite opening, self-intro, transitions, offer, or closing CTA.
- Turn course transcripts into a reusable livestream playbook.
- Connect short-video topics, persona material, and livestream content.

## Do Not Use For

- Rebuilding `02_原文与结构化内容.md` from `segment_*/raw_transcript.txt`.
- Deciding whether content is a real call-in consultation, ordinary QA, or host-led teaching.
- Merging one caller across livestream segments.
- Checking whether a structured livestream document is safe to sync to Feishu.

Use `$livestream-structuring` for those jobs first, then return here only if the next task is livestream coaching or conversion improvement.

## Inputs

Ask for whatever is available, then proceed with explicit assumptions:

- livestream transcript or a representative excerpt
- business, product, and price
- target audience
- stream goal: follow, add contact, book call, order, or conversion
- performance data if available: duration, viewers, retention, comments, inquiries, orders

If upstream context is missing, still review the transcript, but say where the diagnosis is tentative.

## Workflow

1. Classify the task.
   - review an old livestream
   - prepare the next livestream
   - distill reusable rules from the course materials
2. Separate upstream problems from expression problems.
   - upstream: audience, positioning, offer, price, trust, persona
   - expression: opening, pacing, topic order, interaction, proof, CTA
3. Use [references/analysis-rubric.md](references/analysis-rubric.md) to score the room.
4. Use [references/course-map.md](references/course-map.md) to find relevant course evidence.
   - Prefer `rg` or the helper script in `scripts/search_course.sh`.
   - Open only the most relevant transcript slices instead of bulk-loading the folder.
5. Produce a fixed, practical output:
   - one-sentence verdict
   - top 3 blockers
   - scorecard
   - specific rewrites
   - next-stream action list
   - optional short-video follow-up angles

## Output Contract

Default to this structure unless the user asks for something else:

1. `总体判断`
   - one short paragraph on the real bottleneck
2. `关键问题`
   - no more than 3, ranked by leverage
3. `评分`
   - use the rubric dimensions with 1-5 scores
4. `改法`
   - rewrite the opening, one transition, and the closing CTA
5. `下一场直播动作`
   - before stream
   - during stream
   - after stream

When the user asks for rewrite, give 2-3 versions only if the tradeoffs are meaningfully different, such as:

- steady and clear
- stronger conversion
- stronger persona

## Operating Principles

- Do not mistake a transcript problem for a copy problem if the real issue is positioning, offer, or persona.
- Treat the course transcripts as a reference library, not scripture.
- Separate `course-backed principle` from `your inference for this specific business`.
- Prefer practical changes that can be applied in the next livestream over elegant theory.
- Preserve the speaker's natural voice; do not rewrite into generic internet-sales language.
- Keep recommendations specific enough to execute line by line.

## References

- [references/livestream-methodology.md](references/livestream-methodology.md): distilled course operating system
- [references/concept-index.md](references/concept-index.md): jump table from user problem to source sessions
- [references/course-syllabus.md](references/course-syllabus.md): map of all 21 course files
- [references/analysis-rubric.md](references/analysis-rubric.md): scoring dimensions and failure patterns
- [references/course-map.md](references/course-map.md): where to search inside the course transcript folder
- [references/input-template.md](references/input-template.md): reusable intake template for future reviews
- `scripts/search_course.sh`: quick keyword search across the course transcripts
