#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIRS = [
    ROOT / "assets" / "corpus",
    Path.home() / "Desktop" / "TikTokDownloader-master" / "Volume" / "整理输出_按年份热度" / "程序员K哥",
]

YEAR_BOOSTS = {
    "2022": -2.0,
    "2023": -1.0,
    "2024": 0.0,
    "2025": 3.0,
    "2026": 8.0,
}

EXCLUDE_TITLE_TOKENS = [
    "假扮",
    "摸底",
    "拉扯",
    "沉浸式",
    "压力面试",
    "模拟面试",
    "技术摸底",
]

STOPWORDS = {
    "什么", "怎么", "是不是", "可以", "一下", "这个", "那个", "我们", "你们", "他们", "自己",
    "一个", "一种", "为什么", "如何", "哪些", "就是", "还是", "还有", "以及", "如果", "但是",
    "然后", "时候", "事情", "问题", "因为", "所以", "已经", "没有", "需要", "想要", "感觉",
    "觉得", "关于", "对于", "能不能", "应该", "现在", "未来", "直接", "真的", "比较", "特别",
}

TOPIC_SYNONYMS = {
    "java": ["后端", "spring", "springboot", "八股", "项目"],
    "求职": ["找工作", "面试", "offer", "简历"],
    "找工作": ["求职", "面试", "offer", "简历"],
    "面试": ["八股", "项目", "简历", "谈薪"],
    "春招": ["校招", "应届", "找工作"],
    "秋招": ["校招", "应届", "找工作"],
    "实习": ["校招", "项目", "大厂"],
    "培训": ["报班", "线下班", "自学", "学习环境"],
    "自学": ["培训", "报班", "路线", "项目"],
    "考研": ["学历", "工作", "就业", "二战"],
    "跳槽": ["涨薪", "外包", "大厂", "面试"],
    "ai": ["agent", "淘汰", "风口", "程序员", "大模型", "应用开发", "生态位"],
    "大模型": ["ai", "agent", "应用开发", "风口"],
    "应用开发": ["ai", "大模型", "agent", "业务", "落地"],
    "生态位": ["ai", "行业", "现金流", "岗位", "业务"],
    "算法": ["刷题", "力扣", "题"],
}


@dataclass
class Doc:
    path: Path
    year: str
    rank: int | None
    title: str
    tags: List[str]
    score: int | None
    body: str


def resolve_corpus_dirs(explicit: str | None) -> List[Path]:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if p.is_dir():
            return [p]
        raise SystemExit(f"Corpus dir not found: {p}")

    found = []
    seen = set()
    for p in DEFAULT_CORPUS_DIRS:
        rp = p.expanduser().resolve()
        if rp.is_dir() and rp not in seen:
            found.append(rp)
            seen.add(rp)
    if found:
        return found
    raise SystemExit("No corpus directory found.")


def parse_doc(path: Path) -> Doc:
    text = path.read_text(encoding="utf-8", errors="ignore")

    def grab(label: str) -> str:
        m = re.search(rf"^{re.escape(label)}：(.*)$", text, re.M)
        return m.group(1).strip() if m else ""

    body = text.split("=======下为正文============", 1)[1].strip() if "=======下为正文============" in text else text
    year = path.parent.name
    m = re.search(r"top(\d+)_", path.name)
    rank = int(m.group(1)) if m else None
    score = grab("综合分")
    return Doc(
        path=path,
        year=year,
        rank=rank,
        title=grab("标题"),
        tags=[t for t in grab("标签").split() if t],
        score=int(score) if score.isdigit() else None,
        body=body,
    )


def extract_terms(query: str) -> List[str]:
    terms: List[str] = []
    normalized_query = query.lower().strip()

    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.#_-]{1,}", normalized_query):
        if token not in STOPWORDS:
            terms.append(token)
        for syn in TOPIC_SYNONYMS.get(token, []):
            if syn not in STOPWORDS:
                terms.append(syn)

    for block in re.findall(r"[\u4e00-\u9fff]{2,}", query):
        if block not in STOPWORDS:
            terms.append(block)
        for key, synonyms in TOPIC_SYNONYMS.items():
            if key in block:
                terms.extend(synonyms)
        for n in (4, 3, 2):
            if len(block) >= n:
                for i in range(0, len(block) - n + 1):
                    gram = block[i:i + n]
                    if gram not in STOPWORDS:
                        terms.append(gram)
                    for syn in TOPIC_SYNONYMS.get(gram, []):
                        if syn not in STOPWORDS:
                            terms.append(syn)

    seen = set()
    out = []
    for t in terms:
        if len(t) < 2:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:120]


def normalize(text: str) -> str:
    return text.lower()


def term_count(text: str, term: str) -> int:
    return normalize(text).count(term.lower())


def doc_score(doc: Doc, query: str, terms: List[str]) -> float:
    hay_title = doc.title or doc.path.name
    hay_tags = " ".join(doc.tags)
    hay_body = doc.body
    score = 0.0

    if query and query in hay_title:
        score += 40
    if query and query in hay_body:
        score += 22

    for term in terms:
        c_title = term_count(hay_title, term)
        c_tags = term_count(hay_tags, term)
        c_body = term_count(hay_body, term)
        if c_title:
            score += 18 * c_title
        if c_tags:
            score += 14 * c_tags
        if c_body:
            score += min(12, c_body) * (3.5 if len(term) >= 4 else 2.0 if len(term) == 3 else 1.2)

    if doc.rank:
        score += max(0, 12 - math.log2(doc.rank + 1) * 2)
    if doc.score:
        score += min(16, math.log10(max(10, doc.score)) * 2)
    if doc.year in query:
        score += 15
    score += YEAR_BOOSTS.get(doc.year, 0.0)

    return score


def make_chunks(body: str, max_lines: int = 12, stride: int = 6) -> List[str]:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return []
    if len(lines) <= max_lines:
        return ["\n".join(lines)]
    chunks = []
    for i in range(0, len(lines), stride):
        chunk = lines[i:i + max_lines]
        if chunk:
            chunks.append("\n".join(chunk))
        if i + max_lines >= len(lines):
            break
    return chunks


def chunk_score(chunk: str, query: str, terms: List[str]) -> float:
    score = 0.0
    if query and query in chunk:
        score += 30
    for term in terms:
        c = term_count(chunk, term)
        if c:
            score += min(10, c) * (3.5 if len(term) >= 4 else 2.0 if len(term) == 3 else 1.0)
    return score


def best_excerpt(doc: Doc, query: str, terms: List[str]) -> tuple[float, str]:
    chunks = make_chunks(doc.body)
    if not chunks:
        return 0.0, ""
    best = max(chunks, key=lambda c: chunk_score(c, query, terms))
    return chunk_score(best, query, terms), best


def iter_docs(corpus_dirs: List[Path], year: str | None, include_interviews: bool) -> Iterable[Doc]:
    seen = set()
    for corpus_dir in corpus_dirs:
        for path in corpus_dir.rglob("*.txt"):
            if year and path.parent.name != year:
                continue
            if (not include_interviews) and any(token in path.name for token in EXCLUDE_TITLE_TOKENS):
                continue
            dedupe_key = (path.parent.name, path.name)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            yield parse_doc(path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Search the 程序员K哥 corpus.")
    ap.add_argument("query", help="Search query")
    ap.add_argument("--year", help="Limit to year, e.g. 2025")
    ap.add_argument("--top", type=int, default=8, help="Number of hits to show")
    ap.add_argument("--include-interviews", action="store_true", help="Include interview-recording style transcripts")
    ap.add_argument("--corpus-dir", help="Override corpus directory")
    args = ap.parse_args()

    corpus_dirs = resolve_corpus_dirs(args.corpus_dir)
    terms = extract_terms(args.query)
    scored = []
    for doc in iter_docs(corpus_dirs, args.year, args.include_interviews):
        score = doc_score(doc, args.query, terms)
        if score <= 0:
            continue
        excerpt_score, excerpt = best_excerpt(doc, args.query, terms)
        scored.append((score + excerpt_score, doc, excerpt))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_hits = scored[: args.top]

    print("# K哥语料检索")
    print(f"- Query: {args.query}")
    print(f"- Corpora: {', '.join(str(p) for p in corpus_dirs)}")
    if args.year:
        print(f"- Year filter: {args.year}")
    print(f"- Include interviews: {'yes' if args.include_interviews else 'no'}")
    print("- Version rule: newer views override older views when they conflict (2026 > 2025 > 2024 > 2023 > 2022)")
    print(f"- Terms: {', '.join(terms) if terms else '(none)'}")
    print(f"- Hits: {len(top_hits)}")
    print()

    if not top_hits:
        print("没有命中结果。可以尝试换关键词、加年份，或者显式加 --include-interviews。")
        return

    for idx, (score, doc, excerpt) in enumerate(top_hits, 1):
        print(f"## Hit {idx} | score={score:.1f} | year={doc.year} | rank={doc.rank or '?'} | heat={doc.score or '?'}")
        print(f"- File: {doc.path}")
        print(f"- Title: {doc.title or doc.path.name}")
        print(f"- Tags: {' '.join(doc.tags) if doc.tags else '(none)'}")
        if excerpt:
            print("- Excerpt:")
            print("```text")
            print(excerpt)
            print("```")
        print()


if __name__ == "__main__":
    main()
