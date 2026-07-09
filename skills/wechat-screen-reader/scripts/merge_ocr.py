#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path


def text_from_file(path: Path) -> str:
    if path.suffix == ".json":
        rows = json.loads(path.read_text(errors="ignore"))
        return "\n".join(row.get("text", "") for row in rows if row.get("text"))
    return path.read_text(errors="ignore")


def redact(text: str) -> str:
    text = re.sub(r"(微信/联系/[:：])\S+", r"\1[已脱敏]", text)
    text = re.sub(r"(?<!\d)(1[3-9]\d{9})(?!\d)", "[手机号已脱敏]", text)
    text = re.sub(r"(?<!\d)(\d{6,})(?!\d)", "[长数字已脱敏]", text)
    text = re.sub(r"(?<![A-Za-z0-9_])([A-Za-z0-9_]{3,}_[A-Za-z0-9_]{2,})(?![A-Za-z0-9_])", "[账号已脱敏]", text)
    return text


def compact_hash(text: str) -> str:
    return hashlib.md5("".join(text.split()).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge OCR txt/json files, dedupe pages, and optionally redact sensitive tokens.")
    parser.add_argument("inputs", nargs="+", help="OCR .txt/.json files or directories containing them")
    parser.add_argument("--out", required=True, help="Output markdown path")
    parser.add_argument("--title", default="微信聊天 OCR 合并稿")
    parser.add_argument("--reverse", action="store_true", help="Reverse unique page order, useful when captured newest-to-oldest")
    parser.add_argument("--redact", action="store_true", help="Redact likely accounts, phone numbers, and long numeric IDs")
    args = parser.parse_args()

    paths = []
    for raw in args.inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted([*path.glob("*.txt"), *path.glob("*.json")]))
        else:
            paths.append(path)

    unique = []
    seen = set()
    for path in sorted(paths):
        text = text_from_file(path).strip()
        if not text:
            continue
        h = compact_hash(text)
        if h in seen:
            continue
        seen.add(h)
        unique.append((path.stem, redact(text) if args.redact else text))

    if args.reverse:
        unique.reverse()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        f.write(f"# {args.title}\n\n")
        f.write("说明：来源为屏幕截图 OCR，不读取微信数据库；OCR 可能有错字、漏字和页面重叠。\n\n")
        for stem, text in unique:
            f.write(f"## {stem}\n\n```text\n{text.replace('```', '` ` `')}\n```\n\n")

    print(out)
    print(f"unique_pages={len(unique)}")


if __name__ == "__main__":
    main()
