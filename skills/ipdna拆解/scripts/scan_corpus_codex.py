#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


META_KEYS = ["评论", "收藏", "分享", "点赞", "综合分", "标题", "发布时间", "视频时长"]


def parse_txt_metadata(path: Path) -> dict:
    data = {}
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")

    for line in text.splitlines()[:20]:
        for key in META_KEYS:
            prefix = f"{key}："
            if line.startswith(prefix):
                data[key] = line[len(prefix):].strip()
    return data


def infer_year(path: Path) -> str:
    for part in path.parts[::-1]:
        if re.fullmatch(r"20\d{2}", part):
            return part
    match = re.search(r"(20\d{2})", path.name)
    return match.group(1) if match else "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory a local short-video script corpus.")
    parser.add_argument("folder", help="Corpus folder path")
    parser.add_argument("--output", help="Write JSON inventory to this file")
    parser.add_argument("--top", type=int, default=20, help="Top scored items to keep")
    args = parser.parse_args()

    root = Path(args.folder).expanduser().resolve()
    files = sorted(
        [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".txt", ".md"}]
    )

    inventory = {"folder": str(root), "total_files": len(files), "years": {}, "files": []}

    for path in files:
        item = {
            "path": str(path),
            "year": infer_year(path),
            "suffix": path.suffix.lower(),
            "name": path.name,
        }
        if path.suffix.lower() == ".txt":
            item["meta"] = parse_txt_metadata(path)
            score = item["meta"].get("综合分")
            try:
                item["score"] = int(score)
            except (TypeError, ValueError):
                item["score"] = None
        else:
            item["score"] = None

        inventory["files"].append(item)
        inventory["years"].setdefault(item["year"], 0)
        inventory["years"][item["year"]] += 1

    scored = [item for item in inventory["files"] if item.get("score") is not None]
    scored.sort(key=lambda item: item["score"], reverse=True)
    inventory["top_candidates"] = scored[: args.top]

    output = json.dumps(inventory, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).expanduser().resolve().write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
