---
name: wechat-screen-reader
description: Safely read and summarize WeChat chat history through controlled screen screenshots and OCR, without decrypting local WeChat databases. Use when the user asks to read, capture, OCR, analyze, summarize, or package WeChat chat records from a visible Mac WeChat window, especially when chat images/screenshots and file attachments must be opened, extracted, and analyzed too.
---

# WeChat Screen Reader

## Overview

Use this skill to read WeChat chats from the visible UI by screenshot + OCR. Do not access WeChat databases, memory keys, or full local message stores.

## Workflow

1. **Scope and safety**
   - Confirm the exact target: contact name or group name.
   - Tell the user this is screen-level reading: anything visible can be captured.
   - Ask the user to open WeChat or allow you to activate it. Do not send messages.

2. **Prepare tools**
   - Set `SKILL_DIR` to this skill folder and `WORK_DIR` to a task-specific output folder before running commands.
   - Prefer a human-readable output root such as `<current workspace>/微信聊天记录分析/`; avoid opaque nested folders like `reports/` unless the user asks for that structure.
   - Compile local helpers when needed:
     ```bash
     swiftc "$SKILL_DIR/scripts/ocr_vision.swift" -o "$WORK_DIR/ocr_vision"
     swiftc "$SKILL_DIR/scripts/click_at.swift" -o "$WORK_DIR/click_at"
     swiftc "$SKILL_DIR/scripts/right_click_at.swift" -o "$WORK_DIR/right_click_at"
     swiftc "$SKILL_DIR/scripts/scroll_at.swift" -o "$WORK_DIR/scroll_at"
     ```
   - Use `screencapture` for screenshots and `ocr_vision` for OCR.

3. **Verify target**
   - Hide Codex if needed, activate WeChat, capture a full-screen confirmation screenshot.
   - OCR the full screenshot.
   - Confirm the right-side chat title exactly matches the requested target.
   - For private chats, do not treat a name merely appearing in the left sidebar as sufficient.
   - Save this confirmation screenshot.

4. **Capture text pages**
   - Capture only the chat content region when possible, avoiding the left sidebar.
   - Scroll in small batches.
   - After each batch, OCR sample pages and compare fingerprints. If pages repeat, refocus the chat region and retest scrolling.
   - Capture both directions if needed: newest-to-oldest and oldest-to-newest.
   - If the user says not to use OCR tools, use visual reading instead:
     - Capture high-resolution screenshots.
     - Inspect them with the model's vision ability.
     - Do not run OCR scripts or command-line OCR.
     - Do not promise verbatim completeness; produce a faithful structured summary and quote only text that is clearly legible.

5. **Handle images**
   - Inspect screenshots for image thumbnails, long screenshots, quoted screenshots, and article cards.
   - Do not rely only on thumbnail OCR or blurred chat-page crops.
   - Primary strategy: save the original image from the visible WeChat message into the task folder. Use cache scanning only as a fallback/candidate source.
   - For long histories, never use local cache scanning as the primary image strategy because it produces unrelated files and loses the binding between image, message order, and nearby text.
   - For each image thumbnail:
     - Record the source page, visible date/time if available, sender side, nearby text before/after, and rough position in the chat page.
     - Click the thumbnail to open the full-size image viewer, or use the WeChat context menu on the visible message.
     - Prefer WeChat's own `保存图片` / `另存为` / `保存到...` action and save into `$WORK_DIR/images_saved/`.
     - Before typing, pasting, or pressing Enter in any save workflow, positively verify that a macOS save panel or WeChat save sheet is focused. If no save panel is visible/detected, abort the save attempt; never paste a filesystem path while the WeChat chat input may be focused.
     - Name saved originals deterministically, such as `img_001_page03_2026-06-08_1420.png`; if the exact time is not visible, use the page/index and note the uncertainty.
     - Verify the saved file exists before moving on.
     - Also capture the opened image viewer as evidence into `$WORK_DIR/image_opened/`; avoid sidebars and desktop clutter.
     - If direct UI save is unavailable, save/export/share from the opened viewer. If that still fails, use a tight full-size viewer screenshot as the fallback artifact and mark it `screenshot_fallback`.
     - If cache scanning is used, copy only plausible candidates into `$WORK_DIR/images_cache_candidates/`, mark them as `unverified cache candidate`, and do not insert them into the transcript unless matched back to a visible chat message.
     - Analyze saved originals first; use opened viewer screenshots only when the original cannot be saved or inspected.
     - If the image is small or text is dense, upscale the saved original or viewer crop before OCR/visual inspection.
     - If the image is a long screenshot, segment the saved original or clear viewer crop into overlapping slices before OCR/visual inspection:
       ```bash
       python3 "$SKILL_DIR/scripts/segment_image_for_ocr.py" "$WORK_DIR/images_saved/img_001.png" --out-dir "$WORK_DIR/image_segments/img_001"
       ```
     - OCR every segment separately and merge in visual order, unless the user requested no OCR tools.
     - In no-OCR visual mode, inspect each opened image/segment directly with model vision; summarize clearly visible content and mark unclear text as unreadable instead of guessing.
     - If OCR output contains obvious corruption, such as broken Chinese phrases, hallucinated glyphs, or missing sentence boundaries, mark that segment as low-confidence and inspect the saved image manually before summarizing.
     - Close the viewer before continuing.
   - Preserve image order and insert each image summary at its chronological message position in the full body text.
   - Label image OCR/visual reading separately in the final output, with links or filenames for the saved originals when preserved.

6. **Handle files**
   - Inspect screenshots for file cards such as PDF, Word, Excel, PPT, text, ZIP, audio, or generic attachments.
   - Do not claim file contents were read from the chat card alone.
   - For each file card, if the user authorized file access:
     - Click/open the file card through the WeChat UI.
     - If WeChat opens a preview, capture evidence of the filename and visible preview.
     - If WeChat downloads or opens the file locally, copy or move the downloaded file into `$WORK_DIR/files/`.
     - Record the source page, filename, extension, size when available, and whether it was opened, downloaded, parsed, or skipped.
   - Analyze downloaded files by type:
     - `.txt`, `.md`, `.csv`, `.json`: read directly.
     - `.pdf`: extract text with available PDF tooling; OCR page images only if text extraction fails.
     - `.docx`, `.pptx`, `.xlsx`: use the relevant Codex document/presentation/spreadsheet tooling or bundled workspace dependencies.
     - images: OCR as image attachments.
     - audio/video/archives/unknown formats: do not pretend to read them; summarize metadata and ask before extra processing.
   - Add a separate "File Attachments" section to the final output with per-file summaries and coverage limits.

7. **Merge and redact**
   - Convert OCR JSON to text, dedupe pages by compact text hash, and write both raw and redacted Markdown:
     ```bash
     python3 "$SKILL_DIR/scripts/merge_ocr.py" "$WORK_DIR/ocr" --out "$WORK_DIR/merged.md" --title "微信聊天 OCR 合并稿"
     python3 "$SKILL_DIR/scripts/merge_ocr.py" "$WORK_DIR/ocr" --out "$WORK_DIR/merged_redacted.md" --title "微信聊天 OCR 脱敏合并稿" --redact
     ```
   - Redact likely phone numbers, WeChat IDs, long numeric identifiers, and contact lines by default.

8. **Analyze**
   - If the user asks for a complete transcript, original chat record, or explicitly says they do not want a summary, produce a transcript-first report. In that mode, do not substitute AI summary/mainline for message text; either omit summary sections or keep them short and after the complete body.
   - Produce the final report in this exact order:
     1. Title containing target name and date range.
     2. Time range: `YYYY-MM-DD HH:mm ～ YYYY-MM-DD HH:mm`, with uncertainty noted if OCR only shows relative dates such as "昨天".
     3. Generated-at timestamp: `YYYY-MM-DD HH:mm:ss`.
     4. AI summary.
     5. Conversation mainline.
     6. Full body text in chronological order.
     7. Image OCR and file attachment summaries.
     8. Coverage limits and cleanup note.
   - Name the final report as `微信_<target>_<YYYY-MM-DD>～<YYYY-MM-DD>_聊天记录_<generated-at-YYYYMMDD_HHMMSS>.md`; if exact chat dates are uncertain, use the best inferred dates and state the inference inside the report.
   - Separate facts from inferences.
   - State coverage limits: date range, number of unique pages, images opened, files analyzed, images/files not opened, voice/links not read.

9. **Clean temporary artifacts**
   - If the user asks not to leave sensitive artifacts, delete raw screenshots, opened images, image crops/segments, downloaded files, and OCR JSON after the final report is created.
   - Run a dry run first:
     ```bash
     python3 "$SKILL_DIR/scripts/cleanup_sensitive_artifacts.py" "$WORK_DIR" --dry-run
     ```
   - Then run cleanup, keeping only the final Markdown reports unless the user asks to preserve evidence:
     ```bash
     python3 "$SKILL_DIR/scripts/cleanup_sensitive_artifacts.py" "$WORK_DIR" --include-ocr-json
     ```

## Guardrails

- Never use `wx init`, decrypt databases, scan memory keys, or read local WeChat database files for this skill.
- Never proceed if the visible chat title does not match the target.
- Never claim “all records” unless the scroll reached the chat start and newest end with evidence.
- Never claim a file attachment was analyzed unless it was actually opened/downloaded and parsed.
- Never trust low-quality image OCR blindly. If text looks broken, return to the saved image crop, segment/upscale it, or mark it as uncertain.
- Never paste a target folder path into WeChat unless a save panel has been positively confirmed. If focus is uncertain, stop automation, return Codex to the foreground, and report the risk.
- Keep original screenshots in a named output directory and warn they may contain sensitive data.
- Delete temporary image/file artifacts at the end when the user requests cleanup or when the task is highly sensitive.
- After screen capture is complete, bring Codex back to the foreground so the user knows they can use the computer again.
- Read `references/risk-checklist.md` before substantial captures or when the task involves private data, images, files, or long histories.
