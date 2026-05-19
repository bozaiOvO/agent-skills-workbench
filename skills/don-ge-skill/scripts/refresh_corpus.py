#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

DEFAULT_SOURCE = Path("/Users/bo/Desktop/TikTokDownloader-master/Volume/整理输出_按年份热度/dontbesilent 聊赚钱")

THEME_KEYWORDS = {
    "赚钱-创业": ["赚钱", "创业", "生意", "财务自由", "百万", "副业", "上班", "打工", "老板"],
    "内容-流量": ["流量", "内容", "短视频", "涨粉", "账号", "开头", "文案", "小红书", "抖音", "IP"],
    "定价-商业模式": ["定价", "价格", "引流款", "利润款", "商业模式", "变现", "客单价", "成交"],
    "私域-知识付费": ["私域", "知识付费", "课程", "咨询", "社群", "虚拟资料", "答疑"],
    "AI-工作流": ["AI", "人工智能", "Agent", "工作流", "模型", "数字人", "提示词"],
    "执行-心态": ["执行", "拖延", "主体性", "内耗", "安全感", "情绪", "边界", "白嫖"],
    "语言-思维": ["语言", "词", "定义", "精准", "用户需求", "逻辑", "反常识", "第一性原理"],
}

HEADER_KEYS = ["评论", "收藏", "分享", "点赞", "视频时长", "发布时间", "综合分", "标题", "标签"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Don 哥 corpus manifest and index files.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Source corpus directory")
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1], help="Skill root directory")
    parser.add_argument("--preview", action="store_true", help="Print summary to stdout")
    return parser.parse_args()


INT_FIELDS = {"评论", "收藏", "分享", "点赞", "综合分"}


def parse_int(value: str) -> int | None:
    digits = re.sub(r"[^\d-]", "", value)
    if not digits:
        return None
    return int(digits)



def parse_record(path: Path) -> dict[str, Any]:
    text = path.read_text(errors="ignore")
    if "=======下为正文============" in text:
        head, body = text.split("=======下为正文============", 1)
    else:
        head, body = text, ""

    meta: dict[str, Any] = {}
    for line in head.splitlines():
        if "：" not in line:
            continue
        key, value = line.split("：", 1)
        key = key.strip()
        value = value.strip()
        if key in HEADER_KEYS:
            meta[key] = value

    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    title = meta.get("标题", "")
    tags_raw = meta.get("标签", "")
    tags = [t.strip().lstrip("#") for t in re.split(r"[\s,，]+", tags_raw) if t.strip()]

    score = parse_int(meta.get("综合分", "")) or 0
    rank_match = re.match(r"top(\d+)_", path.name)
    rank = int(rank_match.group(1)) if rank_match else None

    record: dict[str, Any] = {
        "path": str(path),
        "file_name": path.name,
        "year": path.parent.name,
        "rank": rank,
        "title": title,
        "published_at": meta.get("发布时间", ""),
        "duration": meta.get("视频时长", ""),
        "tags": tags,
        "body_line_count": len(lines),
        "body_char_count": len("\n".join(lines)),
        "body_preview": " ".join(lines[:3])[:240],
        "empty_body": len(lines) == 0,
    }
    for field in INT_FIELDS:
        record[field] = parse_int(meta.get(field, ""))

    text_for_theme = f"{title} {' '.join(tags)} {' '.join(lines[:30])}"
    hits = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in text_for_theme for keyword in keywords):
            hits.append(theme)
    record["themes"] = hits
    record["score"] = score
    return record



def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_year: dict[str, list[dict[str, Any]]] = defaultdict(list)
    tag_counter: Counter[str] = Counter()
    theme_counter: Counter[str] = Counter()
    empty_files: list[str] = []

    for record in records:
        by_year[record["year"]].append(record)
        tag_counter.update(record["tags"])
        theme_counter.update(record["themes"])
        if record["empty_body"]:
            empty_files.append(record["file_name"])

    years_summary: dict[str, Any] = {}
    for year, rows in sorted(by_year.items()):
        scores = [r["score"] or 0 for r in rows]
        lines = [r["body_line_count"] for r in rows]
        years_summary[year] = {
            "count": len(rows),
            "avg_score": round(mean(scores), 1) if scores else 0,
            "avg_body_lines": round(mean(lines), 1) if lines else 0,
            "top_titles": [
                {
                    "rank": r["rank"],
                    "title": r["title"],
                    "score": r["score"],
                }
                for r in sorted(rows, key=lambda x: (-(x["score"] or 0), x["rank"] or 9999))[:5]
            ],
        }

    return {
        "source": str(DEFAULT_SOURCE),
        "source_used": str(records[0]["path"]).split("/202", 1)[0] if records else "",
        "total_files": len(records),
        "total_body_lines": sum(r["body_line_count"] for r in records),
        "total_body_chars": sum(r["body_char_count"] for r in records),
        "empty_body_count": len(empty_files),
        "empty_body_files": empty_files,
        "years": years_summary,
        "top_tags": tag_counter.most_common(30),
        "theme_counts": theme_counter.most_common(),
    }



def render_markdown(summary: dict[str, Any], records: list[dict[str, Any]], source: Path) -> str:
    by_year: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_year[record["year"]].append(record)

    lines: list[str] = []
    lines.append("# Don 哥语料索引")
    lines.append("")
    lines.append(f"- 源目录：`{source}`")
    lines.append(f"- 总文件数：{summary['total_files']}")
    lines.append(f"- 正文总行数：{summary['total_body_lines']}")
    lines.append(f"- 正文总字数（近似字符）：{summary['total_body_chars']}")
    lines.append(f"- 空正文文件数：{summary['empty_body_count']}")
    lines.append("")
    lines.append("## 年度概况")
    lines.append("")
    lines.append("| 年份 | 文件数 | 平均综合分 | 平均正文行数 | 头部标题样本 |")
    lines.append("| --- | ---: | ---: | ---: | --- |")
    for year, info in summary["years"].items():
        sample = "；".join(item["title"] for item in info["top_titles"][:3])
        lines.append(f"| {year} | {info['count']} | {info['avg_score']} | {info['avg_body_lines']} | {sample} |")
    lines.append("")
    lines.append("## 高频标签")
    lines.append("")
    for tag, count in summary["top_tags"]:
        lines.append(f"- {tag}: {count}")
    lines.append("")
    lines.append("## 主题命中统计（启发式）")
    lines.append("")
    for theme, count in summary["theme_counts"]:
        lines.append(f"- {theme}: {count}")
    lines.append("")
    if summary["empty_body_files"]:
        lines.append("## 空正文 / OCR 缺失")
        lines.append("")
        for file_name in summary["empty_body_files"]:
            lines.append(f"- {file_name}")
        lines.append("")

    lines.append("## 全量文件清单")
    lines.append("")
    for year in sorted(by_year):
        rows = sorted(by_year[year], key=lambda x: x["rank"] or 9999)
        lines.append(f"### {year}")
        lines.append("")
        lines.append("| Rank | 综合分 | 标题 | 标签 | 正文行数 | 主题 |")
        lines.append("| ---: | ---: | --- | --- | ---: | --- |")
        for row in rows:
            title = row["title"].replace("|", "／") if row["title"] else "[无标题]"
            tags = ", ".join(row["tags"][:6])
            themes = ", ".join(row["themes"])
            lines.append(f"| {row['rank'] or ''} | {row['score'] or 0} | {title} | {tags} | {row['body_line_count']} | {themes} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"



def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    skill_root = args.skill_root.expanduser().resolve()
    refs_dir = skill_root / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for path in sorted(source.glob("*/*.txt")):
        if path.name.startswith("._"):
            continue
        records.append(parse_record(path))

    summary = summarize(records)
    manifest = {
        "source": str(source),
        "summary": summary,
        "records": records,
    }

    manifest_path = refs_dir / "corpus-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    markdown_path = refs_dir / "corpus-map.md"
    markdown_path.write_text(render_markdown(summary, records, source))

    if args.preview:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"\nWrote:\n- {manifest_path}\n- {markdown_path}")


if __name__ == "__main__":
    main()
