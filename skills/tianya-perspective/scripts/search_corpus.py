#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CORPUS_DIRS = [
    ROOT / "assets" / "text-corpus" / "boards",
    ROOT / "references" / "research" / "boards",
    Path.home() / "Documents" / "mac_2026" / "杂七杂八" / "天涯合集" / "提取文本",
]

ENV_CORPUS_DIRS = "TIANYA_CORPUS_DIRS"

BOARD_ALIASES = {
    "房产": "kk合集",
    "阶层": "kk合集",
    "资产": "kk合集",
    "楼市": "股市楼市",
    "股票": "股市楼市",
    "投资": "股市楼市",
    "经济": "经济论坛",
    "货币": "经济论坛",
    "周期": "经济论坛",
    "地缘": "国际观察",
    "国际": "国际观察",
    "历史": "煮酒论史",
    "制度": "煮酒论史",
    "社会": "天涯杂谈",
    "热点": "天涯杂谈",
    "情感": "情感天地",
    "婚姻": "情感天地",
    "鬼": "莲蓬鬼话",
    "玄学": "中医命理",
    "中医": "中医命理",
    "故事": "天涯故事",
    "小说": "天涯小说",
}

STOPWORDS = {
    "什么",
    "怎么",
    "这个",
    "那个",
    "就是",
    "还是",
    "因为",
    "所以",
    "现在",
    "如果",
    "但是",
    "一个",
    "一种",
    "有没有",
    "为什么",
    "是不是",
    "能不能",
}


@dataclass
class Doc:
    path: Path
    root: Path
    board: str
    title: str
    body: str


def split_env_dirs(value: str | None) -> list[Path]:
    if not value:
        return []
    parts = [p for p in re.split(r"[:;]", value) if p.strip()]
    return [Path(p).expanduser() for p in parts]


def resolve_corpus_dirs(explicit: list[str]) -> list[Path]:
    dirs = [Path(p).expanduser() for p in explicit]
    dirs.extend(split_env_dirs(os.environ.get(ENV_CORPUS_DIRS)))
    dirs.extend(DEFAULT_CORPUS_DIRS)

    found: list[Path] = []
    seen: set[Path] = set()
    for d in dirs:
        try:
            rd = d.resolve()
        except OSError:
            continue
        if rd.is_dir() and rd not in seen:
            found.append(rd)
            seen.add(rd)
    if not found:
        raise SystemExit("No Tianya corpus directory found.")
    return found


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.name.startswith(".") or not path.is_file():
            continue
        if path.suffix.lower() in {".md", ".txt"}:
            yield path


def board_name(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_分析"):
        stem = stem[:-3]
    if stem.startswith("_ALL_"):
        return "综合"
    return stem


def parse_doc(path: Path, root: Path) -> Doc:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    return Doc(path=path, root=root, board=board_name(path), title=title, body=text)


def extract_terms(query: str) -> list[str]:
    terms: list[str] = []
    normalized = query.lower()
    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.#_-]{1,}", normalized):
        terms.append(token)
    for block in re.findall(r"[\u4e00-\u9fff]{2,}", query):
        if block not in STOPWORDS:
            terms.append(block)
        for key, alias in BOARD_ALIASES.items():
            if key in block:
                terms.append(alias)
        for n in (4, 3, 2):
            if len(block) >= n:
                for i in range(0, len(block) - n + 1):
                    gram = block[i : i + n]
                    if gram not in STOPWORDS:
                        terms.append(gram)

    out: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if len(term) < 2:
            continue
        if term not in seen:
            out.append(term)
            seen.add(term)
    return out[:100]


def count(text: str, term: str) -> int:
    return text.lower().count(term.lower())


def doc_score(doc: Doc, query: str, terms: list[str]) -> float:
    title = doc.title or doc.path.name
    body = doc.body
    score = 0.0
    if query and query in title:
        score += 35
    if query and query in body:
        score += 18
    for term in terms:
        title_hits = count(title, term)
        board_hits = count(doc.board, term)
        body_hits = count(body, term)
        score += title_hits * 16
        score += board_hits * 12
        score += min(body_hits, 20) * (3.0 if len(term) >= 4 else 1.5)
    if doc.path.name.endswith("_分析.md"):
        score += 5
    if doc.board == "综合":
        score += 3
    return score


def make_chunks(text: str, max_lines: int = 12, stride: int = 6) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return ["\n".join(lines)] if lines else []
    chunks = []
    for i in range(0, len(lines), stride):
        chunk = lines[i : i + max_lines]
        if chunk:
            chunks.append("\n".join(chunk))
        if i + max_lines >= len(lines):
            break
    return chunks


def chunk_score(chunk: str, query: str, terms: list[str]) -> float:
    score = 0.0
    if query and query in chunk:
        score += 20
    for term in terms:
        score += min(count(chunk, term), 8) * (4 if len(term) >= 4 else 2)
    return score


def best_snippet(doc: Doc, query: str, terms: list[str]) -> str:
    chunks = make_chunks(doc.body)
    if not chunks:
        return ""
    best = max(chunks, key=lambda c: chunk_score(c, query, terms))
    return best[:1200]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Tianya skill corpus.")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--corpus-dir", action="append", default=[], help="Extra corpus dir, e.g. a mounted NAS path")
    parser.add_argument("--board", help="Only include board name containing this text")
    parser.add_argument("--limit", type=int, default=6)
    args = parser.parse_args()

    terms = extract_terms(args.query)
    roots = resolve_corpus_dirs(args.corpus_dir)
    docs: list[Doc] = []
    for root in roots:
        for path in iter_text_files(root):
            doc = parse_doc(path, root)
            if args.board and args.board not in doc.board and args.board not in str(path):
                continue
            docs.append(doc)

    scored = []
    for doc in docs:
        score = doc_score(doc, args.query, terms)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)

    print(f"Query: {args.query}")
    print(f"Terms: {', '.join(terms[:20]) if terms else '(none)'}")
    print("Corpus dirs:")
    for root in roots:
        print(f"- {root}")
    print()

    if not scored:
        print("No strong match. Use the framework in SKILL.md and mark it as framework inference.")
        return

    for idx, (score, doc) in enumerate(scored[: max(args.limit, 1)], 1):
        snippet = best_snippet(doc, args.query, terms)
        rel = doc.path
        try:
            rel = doc.path.relative_to(doc.root)
        except ValueError:
            pass
        print("=" * 72)
        print(f"{idx}. score={score:.1f} board={doc.board} file={rel}")
        print(f"path={doc.path}")
        print("-" * 72)
        print(snippet)
        print()


if __name__ == "__main__":
    main()
