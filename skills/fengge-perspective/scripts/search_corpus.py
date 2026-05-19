#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


DATASET_ROOT = Path("/Users/bo/Desktop/TikTokDownloader-master/Volume/Zhoulifeng-Streaming-Dataset")
ORIGINAL_DIR = DATASET_ROOT / "orginal_text"
SFT_PATH = DATASET_ROOT / "refine_data_process" / "10_feng_sft_train.json"

ROUTE_TERMS = {
    "geo": [
        "缅北",
        "缅甸",
        "东南亚",
        "香港",
        "俄罗斯",
        "土耳其",
        "印尼",
        "迪拜",
        "美国",
        "中国",
        "工会",
        "留学生",
        "签证",
    ],
    "finance": [
        "A股",
        "股市",
        "牛市",
        "理财",
        "投资",
        "国家意志",
        "外汇",
        "ETF",
        "大盘",
    ],
    "history": [
        "历史",
        "元朝",
        "明朝",
        "清朝",
        "唐朝",
        "人性",
        "太阳底下没有新鲜事",
    ],
    "life": [
        "工作",
        "老婆",
        "结婚",
        "社恐",
        "幸福",
        "怨天尤人",
        "买房",
        "打工",
    ],
    "creator": [
        "直播",
        "拍视频",
        "拍片",
        "流量",
        "B站",
        "主播",
        "连麦",
        "节目效果",
    ],
    "health": [
        "登山",
        "心脏",
        "熬夜",
        "医生",
        "睡觉",
        "珠峰",
        "雪山",
        "高原",
    ],
}


@dataclass
class Hit:
    score: int
    source: str
    title: str
    year: str
    identifier: str
    snippet: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Fengge local corpus.")
    parser.add_argument("query", help="Search query.")
    parser.add_argument("--year", help="Filter by year, e.g. 2025.")
    parser.add_argument("--top", type=int, default=8, help="Max hits per source.")
    parser.add_argument(
        "--source",
        choices=["original", "sft", "all"],
        default="original",
        help="Corpus layer to search.",
    )
    parser.add_argument(
        "--include-variants",
        action="store_true",
        help="Include files marked incomplete or barrage/danmu variants.",
    )
    parser.add_argument(
        "--route",
        choices=sorted(ROUTE_TERMS.keys()),
        help="Apply a predefined topic route such as geo/finance/history/life/creator/health.",
    )
    return parser.parse_args()


def build_terms(query: str, route: str | None = None) -> List[str]:
    terms = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", query)
    cleaned = []
    for term in terms:
        term = term.strip()
        if not term:
            continue
        cleaned.append(term)
    if route:
        cleaned.extend(ROUTE_TERMS.get(route, []))
    if query not in cleaned:
        cleaned.insert(0, query)
    seen = set()
    unique = []
    for item in cleaned:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def score_text(text: str, title: str, terms: Iterable[str]) -> int:
    score = 0
    for term in terms:
        if not term:
            continue
        title_hits = title.count(term)
        text_hits = text.count(term)
        if title_hits:
            score += 40 + min(title_hits, 4) * 20
        if text_hits:
            score += min(text_hits, 8) * 6
    return score


def make_snippet(text: str, terms: Iterable[str], width: int = 90) -> str:
    lower_terms = [term for term in terms if term]
    index = -1
    chosen = ""
    for term in lower_terms:
        pos = text.find(term)
        if pos != -1:
            index = pos
            chosen = term
            break
    if index == -1:
        compact = re.sub(r"\s+", " ", text)
        return compact[: width * 2]
    start = max(0, index - width)
    end = min(len(text), index + len(chosen) + width)
    snippet = re.sub(r"\s+", " ", text[start:end])
    return snippet


def search_original(args: argparse.Namespace, terms: List[str]) -> List[Hit]:
    hits: List[Hit] = []
    if not ORIGINAL_DIR.exists():
        return hits

    for path in sorted(ORIGINAL_DIR.glob("*.txt")):
        name = path.name
        if args.year and f"-{args.year}" not in name:
            continue
        if not args.include_variants and ("不完整" in name or "弹幕版" in name):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        title = path.stem
        score = score_text(text, title, terms)
        if score <= 0:
            continue
        year_match = re.search(r"(20\d{2})\d{4}", name)
        year = year_match.group(1) if year_match else "unknown"
        hits.append(
            Hit(
                score=score,
                source="original",
                title=title,
                year=year,
                identifier=name,
                snippet=make_snippet(text, terms),
            )
        )

    hits.sort(key=lambda item: (-item.score, item.identifier))
    return hits[: args.top]


def search_sft(args: argparse.Namespace, terms: List[str]) -> List[Hit]:
    hits: List[Hit] = []
    if not SFT_PATH.exists():
        return hits
    try:
        data = json.loads(SFT_PATH.read_text())
    except Exception:
        return hits

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        text = "\n".join(
            [
                str(item.get("instruction", "")),
                str(item.get("input", "")),
                str(item.get("output", "")),
            ]
        )
        score = score_text(text, str(item.get("input", "")), terms)
        if score <= 0:
            continue
        hits.append(
            Hit(
                score=score,
                source="sft",
                title=str(item.get("input", ""))[:60],
                year=args.year or "mixed",
                identifier=f"sft#{idx}",
                snippet=make_snippet(text, terms),
            )
        )

    hits.sort(key=lambda item: (-item.score, item.identifier))
    return hits[: args.top]


def print_hits(label: str, hits: List[Hit]) -> None:
    print(f"{label}: {len(hits)} hit(s)")
    if not hits:
        return
    for i, hit in enumerate(hits, start=1):
        print(f"{i}. [{hit.source}] {hit.identifier} | year={hit.year} | score={hit.score}")
        print(f"   title: {hit.title}")
        print(f"   snippet: {hit.snippet}")


def main() -> None:
    args = parse_args()
    terms = build_terms(args.query, args.route)

    print(f"dataset: {DATASET_ROOT}")
    print(f"query: {args.query}")
    print(f"terms: {', '.join(terms)}")
    if args.route:
        print(f"route: {args.route}")
    if args.year:
        print(f"year-filter: {args.year}")
    print(f"source: {args.source}")
    print()

    if args.source in {"original", "all"}:
        print_hits("ORIGINAL", search_original(args, terms))
        print()
    if args.source in {"sft", "all"}:
        print_hits("SFT", search_sft(args, terms))


if __name__ == "__main__":
    main()
