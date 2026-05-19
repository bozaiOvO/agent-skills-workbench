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
    Path.home() / "Desktop" / "TikTokDownloader-master" / "Volume" / "整理输出_按年份热度" / "程序员luck",
]

YEAR_BOOSTS = {
    "2025": 1.0,
    "2026": 4.0,
}

STOPWORDS = {
    "什么", "怎么", "是不是", "可以", "一下", "这个", "那个", "我们", "你们", "他们", "自己",
    "一个", "一种", "为什么", "如何", "哪些", "就是", "还是", "还有", "以及", "如果", "但是",
    "然后", "时候", "事情", "问题", "因为", "所以", "已经", "没有", "需要", "想要", "感觉",
    "觉得", "关于", "对于", "能不能", "应该", "现在", "未来", "直接", "真的", "比较", "特别",
}

TOPIC_SYNONYMS = {
    "实习": ["校招", "项目", "八股", "算法题", "找工作"],
    "标准": ["详细", "程度", "够用", "要求", "上场"],
    "找工作": ["求职", "投递", "岗位", "就业", "简历"],
    "就业": ["找工作", "岗位", "实习", "应届生"],
    "考研": ["读研", "就业", "工作", "性价比"],
    "专升本": ["大专", "本科", "门槛", "机会成本"],
    "大专": ["专科", "本科", "门槛", "就业"],
    "学历": ["大专", "本科", "双非", "双一流"],
    "ai": ["人工智能", "大模型", "智能体", "agent", "mcp", "rag"],
    "人工智能": ["AI", "大模型", "智能体", "应用开发"],
    "java": ["后端", "开发", "岗位"],
    "python": ["数据分析", "AI", "爬虫"],
    "岗位": ["方向", "就业", "薪资"],
    "高薪": ["岗位", "薪资", "方向"],
    "离职": ["薪资", "风险", "现金流"],
    "裁员": ["自保", "转岗", "AI"],
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
            if key.lower() in block.lower():
                terms.extend(synonyms)
        for n in (4, 3, 2):
            if len(block) >= n:
                for i in range(0, len(block) - n + 1):
                    gram = block[i:i + n]
                    if gram not in STOPWORDS:
                        terms.append(gram)
                    for syn in TOPIC_SYNONYMS.get(gram.lower(), []):
                        if syn not in STOPWORDS:
                            terms.append(syn)

    seen = set()
    out = []
    for t in terms:
        if len(t) < 2:
            continue
        tl = t.lower()
        if tl not in seen:
            seen.add(tl)
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


def iter_docs(corpus_dirs: List[Path], year: str | None) -> Iterable[Doc]:
    seen = set()
    for corpus_dir in corpus_dirs:
        for path in corpus_dir.rglob("*.txt"):
            if year and path.parent.name != year:
                continue
            dedupe_key = (path.parent.name, path.name)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            yield parse_doc(path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Search the 程序员luck corpus.")
    ap.add_argument("query", help="Search query")
    ap.add_argument("--year", help="Limit to year, e.g. 2026")
    ap.add_argument("--top", type=int, default=8, help="Number of hits to show")
    ap.add_argument("--corpus-dir", help="Override corpus directory")
    args = ap.parse_args()

    corpus_dirs = resolve_corpus_dirs(args.corpus_dir)
    terms = extract_terms(args.query)
    scored = []
    for doc in iter_docs(corpus_dirs, args.year):
        score = doc_score(doc, args.query, terms)
        if score <= 0:
            continue
        excerpt_score, excerpt = best_excerpt(doc, args.query, terms)
        scored.append((score + excerpt_score, doc, excerpt))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_hits = scored[: args.top]

    print("# 程序员luck语料检索")
    print(f"- Query: {args.query}")
    print(f"- Corpora: {', '.join(str(p) for p in corpus_dirs)}")
    if args.year:
        print(f"- Year filter: {args.year}")
    print("- Year bias: prefer newer views by default (2026 > 2025)")
    print(f"- Terms: {', '.join(terms) if terms else '(none)'}")
    print(f"- Hits: {len(top_hits)}")
    print()

    for i, (score, doc, excerpt) in enumerate(top_hits, start=1):
        print(f"## Hit {i} | score={score:.1f} | year={doc.year} | rank={doc.rank} | heat={doc.score}")
        print(f"- File: {doc.path}")
        print(f"- Title: {doc.title}")
        print(f"- Tags: {' '.join(doc.tags)}")
        if excerpt:
            print("- Excerpt:")
            print("```text")
            print(excerpt)
            print("```")
        print()


if __name__ == "__main__":
    main()
