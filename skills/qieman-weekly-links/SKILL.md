---
name: qieman-weekly-links
description: "从飞书且曼周刊提取推荐视频和公开链接，生成本地 Markdown 与 JSON 汇总。"

---

# Qieman Weekly Links

## Dependency Note

This skill is runtime-dependent. The GitHub repo includes the extraction script and a portable generated Markdown snapshot at `assets/且曼周刊推荐内容链接汇总.md`, but not Feishu login state, the weeklies input JSON, or raw extraction JSON.

Runtime inputs can be configured with:

- `QIEMAN_WEEKLIES_PATH`
- `QIEMAN_OUTPUT_JSON`
- `QIEMAN_OUTPUT_MD`
- `CDP_PORT`
- `FEISHU_DOMAIN`

Do not assume `/private/tmp` files exist on another Mac. If the user only needs the existing summary, read the bundled Markdown snapshot instead of rerunning extraction.

Use this skill to extract recommended public links from Feishu wiki pages such as 且曼周刊/且曼内刊 and write a Markdown deliverable.

## Mac Mini Incremental Workflow

When a generated snapshot already exists, prefer an incremental patch workflow instead of rerunning the full archive.

Current stable baseline:

- Snapshot: `assets/且曼周刊推荐内容链接汇总.md`
- Known baseline coverage from the bundled snapshot: Vol.205-Vol.276, 71 pages.
- Known baseline gaps: Vol.274 missing; Vol.262 and Vol.265 marked as empty pages.
- Known post-baseline increment found on 2026-05-30: Vol.277 20260525.

Recommended local flow:

1. Treat the bundled Markdown snapshot as the source-of-truth baseline.
2. Only patch missing/new/problem volumes, currently Vol.262, Vol.265, Vol.274, and Vol.277.
3. Use this skill's extraction logic and output schema, but use the Codex Chrome/Agent Browser path for logged-in Feishu access when CDP is not already available.
4. Do not start a full rerun just because `/private/tmp/qieman_weeklies_2025_2026.json` or Chrome CDP port `9223` is missing.
5. Use the CDP script only when `curl -s http://127.0.0.1:9223/json/list` succeeds and the required weeklies JSON is present or has been reconstructed.

The Agent Browser incremental patch should preserve the same fields as the full extraction wherever possible: weekly title, weekly URL, catalogue section, original item text, stripped title, Feishu anchor, public links, raw links, and extraction errors.

### Feishu Virtual Scroll Rule

For small repair batches in logged-in Feishu pages, prefer a real-scroll rendered-block scan before catalogue-click extraction.

Feishu wiki pages virtualize both the catalogue and body content. On 2026-05-30, catalogue-click extraction was reliable for Vol.274/277 but slow and unstable for Vol.262/265 because the target catalogue rows disappeared outside the visible window. The faster repair path was:

1. Open the weekly page in the already logged-in Chrome/Codex browser.
2. Use real browser wheel scrolling from top to bottom.
3. At each viewport, read rendered `[data-record-id]` blocks.
4. Treat heading blocks whose text starts with `^\d+[.．、]\s*` as recommendation items.
5. Attach subsequent block links to the current numbered heading until the next numbered heading or section heading.
6. Merge snapshots by `data-record-id`, dedupe public links, then render the same Markdown format as the bundled snapshot.

Only fall back to catalogue-click extraction when the rendered-block scan misses expected sections or the page's headings are not numbered.

## What This Skill Does

- Reads a JSON list of weekly Feishu documents.
- Opens each weekly page through an already logged-in Chrome CDP session.
- Uses the Feishu catalogue to click each numbered recommendation item.
- Extracts public links from the item block, including Douyin, Bilibili, Xiaohongshu, Kuaishou, Xigua, YouTube, WeChat articles, web pages, etc.
- Preserves a Feishu anchor for each item so the user can verify the original source.
- Writes both Markdown and raw JSON, with a header summary for missing volumes, empty pages, and failed item定位.

## Default Local Paths

- Script: `scripts/extract_feishu_weekly_recommendation_links.mjs`
- Bundled snapshot: `assets/且曼周刊推荐内容链接汇总.md`
- Weeklies JSON: `QIEMAN_WEEKLIES_PATH`, or `/private/tmp/qieman_weeklies_2025_2026.json` if unset.
- Raw JSON output: `QIEMAN_OUTPUT_JSON`, or `/private/tmp/qieman_weekly_recommendation_links.json` if unset.
- Markdown output: `QIEMAN_OUTPUT_MD`, or `且曼周刊推荐内容链接汇总.md` in the current working directory if unset.

## Required Login State

The extraction script needs a debuggable Chrome tab with access to the Feishu workspace.

Preferred flow:

1. Open Chrome with remote debugging on a known port, usually `9223`, using the user's logged-in Feishu state when possible.
2. If the page redirects to login, ask the user to scan/confirm login once.
3. Verify CDP is live with:

```bash
curl -s http://127.0.0.1:9223/json/list
```

Do not claim a full extraction if login is missing or the page only shows the Feishu login screen.

## Commands

Run the full extraction:

```bash
node {{SKILL_DIR}}/scripts/extract_feishu_weekly_recommendation_links.mjs \
  --weeklies "${QIEMAN_WEEKLIES_PATH:-/private/tmp/qieman_weeklies_2025_2026.json}" \
  --output-md "${QIEMAN_OUTPUT_MD:-且曼周刊推荐内容链接汇总.md}" \
  --output-json "${QIEMAN_OUTPUT_JSON:-/private/tmp/qieman_weekly_recommendation_links.json}" \
  --cdp-port 9223
```

Rerender Markdown from existing JSON without opening Feishu:

```bash
node {{SKILL_DIR}}/scripts/extract_feishu_weekly_recommendation_links.mjs \
  --render-from-json "${QIEMAN_OUTPUT_JSON:-/private/tmp/qieman_weekly_recommendation_links.json}" \
  --output-md "${QIEMAN_OUTPUT_MD:-且曼周刊推荐内容链接汇总.md}"
```

Patch-run only specific volumes:

```bash
node {{SKILL_DIR}}/scripts/extract_feishu_weekly_recommendation_links.mjs \
  --weeklies "${QIEMAN_WEEKLIES_PATH:-/private/tmp/qieman_weeklies_2025_2026.json}" \
  --output-md /private/tmp/qieman_patch.md \
  --output-json /private/tmp/qieman_patch.json \
  --volumes 262,265 \
  --cdp-port 9223
```

## Verification

After a run, report these numbers from the raw JSON:

- pages processed
- catalogue entries
- entries with public links
- video-like entries
- empty pages
- missing volumes

Use a quick one-liner like:

```bash
node -e "const fs=require('fs'); const p=process.env.QIEMAN_OUTPUT_JSON||'/private/tmp/qieman_weekly_recommendation_links.json'; const d=JSON.parse(fs.readFileSync(p,'utf8')); const pages=d.results||[]; let entries=0,withPublic=0,video=0,empty=[]; for(const page of pages){ if(!(page.entries||[]).length) empty.push(page.weekly.title); for(const e of page.entries||[]){ entries++; if((e.publicLinks||[]).length) withPublic++; if((e.publicLinks||[]).some(u=>/(douyin\\.com|iesdouyin\\.com|bilibili\\.com|b23\\.tv|xiaohongshu\\.com|xhslink\\.com|kuaishou\\.com|ixigua\\.com|youtube\\.com|youtu\\.be|v\\.qq\\.com)/i.test(u)&&!/\\/(search|hashtag)\\//i.test(u))) video++; }} console.log(JSON.stringify({pages:pages.length,entries,withPublic,video,empty,missingVolumes:d.missingVolumes},null,2));"
```

## Known Failure Modes

- **Chrome CDP closed**: `http://127.0.0.1:9223/json/list` fails. Reopen Chrome with remote debugging or use an approved browser automation path.
- **Feishu login missing**: page redirects to `accounts.feishu.cn`. Ask the user to scan/confirm login, then rerun.
- **Empty pages**: the script reached the document but found no catalogue entries. Treat as a verification issue, not success. Try rerunning those volumes after login/state is stable.
- **Missing volume in directory JSON**: the script cannot invent the source URL. Either update the weeklies JSON from the Feishu directory or add the missing weekly object manually after verifying the URL.

## Output Rule

Final response should link the Markdown file, summarize counts, and explicitly name unresolved missing/empty pages. Do not imply 100% completeness unless empty pages and missing volumes are both empty.
