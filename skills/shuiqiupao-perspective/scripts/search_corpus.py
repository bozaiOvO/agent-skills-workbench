#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIRS = [
    ROOT / 'assets' / 'corpus',
    ROOT / 'assets' / 'paopaoshuo',
    Path.home() / 'Desktop' / 'TikTokDownloader-master' / 'Volume' / '整理输出_按年份热度' / '水球泡',
    Path.home() / 'Desktop' / 'TikTokDownloader-master' / 'Volume' / '整理输出_按年份热度' / '泡泡说',
]
STOPWORDS = {
    '什么', '怎么', '是不是', '可以', '一下', '这个', '那个', '我们', '你们', '他们', '自己', '一个', '一种',
    '为什么', '如何', '哪些', '怎么做', '一下子', '就是', '还是', '还有', '以及', '如果', '但是', '然后',
    '时候', '事情', '问题', '因为', '所以', '已经', '没有', '需要', '想要', '感觉', '觉得', '关于', '对于',
    '能不能', '要不要', '应该', '现在', '未来', '直接', '真的', '比较', '特别', '可能', '大概', '这里', '那里',
}


SOURCE_ALIASES = {
    'corpus': '水球泡',
    'paopaoshuo': '泡泡说',
    '水球泡': '水球泡',
    '泡泡说': '泡泡说',
}

# 轻量主题词映射：不是做语义搜索替代，而是给常见用户问法补一点近义召回。
# 规则保持保守，避免把完全不相关的问题硬拉到一起。
TOPIC_SYNONYMS = {
    '读研': ['考研', '学历', '门票', '平台', '应届生'],
    '考研': ['读研', '学历', '门票', '平台'],
    '工作': ['上班', '求职', '就业', '入职'],
    '创业': ['生意', '副业', '卧底', '信任银行', '上桌'],
    '报班': ['培训', '课程', '自学', '花钱买加速', '公开外挂'],
    '培训': ['报班', '课程', '自学', '花钱买加速'],
    '自学': ['报班', '培训', '纠错', '输出', '路径'],
    '实习': ['应届生', '学生', '上桌', '城市', '开放世界'],
    '学生': ['社会人', '上桌', '开放世界', '实习'],
    '社会人': ['学生', '开放世界', '上桌', '任务'],
    'ai': ['人工智能', '风口', '进场', '版本'],
    '人工智能': ['ai', '风口', '进场', '版本'],
    '城市': ['一线城市', '圈层', '机会密度'],
    '花钱': ['投资自己', '报班', '公开外挂', '加速'],
    '投资自己': ['花钱', '报班', '加速', '公开外挂'],
}


@dataclass
class Doc:
    path: Path
    corpus_root: Path
    source: str
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
        raise SystemExit(f'Corpus dir not found: {p}')

    found = []
    seen = set()
    for p in DEFAULT_CORPUS_DIRS:
        rp = p.expanduser().resolve()
        if rp.is_dir() and rp not in seen:
            found.append(rp)
            seen.add(rp)

    if found:
        return found
    raise SystemExit('No corpus directory found.')


def normalize_source_name(name: str) -> str:
    return SOURCE_ALIASES.get(name, name)


def parse_doc(path: Path, corpus_root: Path) -> Doc:
    text = path.read_text(encoding='utf-8', errors='ignore')

    def grab(label: str) -> str:
        m = re.search(rf'^{re.escape(label)}：(.*)$', text, re.M)
        return m.group(1).strip() if m else ''

    body = text.split('=======下为正文============', 1)[1].strip() if '=======下为正文============' in text else text
    year = path.parent.name
    m = re.search(r'top(\d+)_', path.name)
    rank = int(m.group(1)) if m else None
    score = grab('综合分')
    return Doc(
        path=path,
        corpus_root=corpus_root,
        source=normalize_source_name(corpus_root.name),
        year=year,
        rank=rank,
        title=grab('标题'),
        tags=[t for t in grab('标签').split() if t],
        score=int(score) if score.isdigit() else None,
        body=body,
    )


def extract_terms(query: str) -> List[str]:
    query = query.strip()
    terms: List[str] = []

    normalized_query = query.lower()
    for token in re.findall(r'[A-Za-z0-9][A-Za-z0-9+.#_-]{1,}', normalized_query):
        if token not in STOPWORDS:
            terms.append(token)
        for syn in TOPIC_SYNONYMS.get(token, []):
            if syn not in STOPWORDS:
                terms.append(syn)

    for block in re.findall(r'[\u4e00-\u9fff]{2,}', query):
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
    hay_tags = ' '.join(doc.tags)
    hay_body = doc.body
    score = 0.0

    if query and query in hay_title:
        score += 40
    if query and query in hay_body:
        score += 20

    for term in terms:
        c_title = term_count(hay_title, term)
        c_tags = term_count(hay_tags, term)
        c_body = term_count(hay_body, term)
        if c_title:
            score += 18 * c_title
        if c_tags:
            score += 14 * c_tags
        if c_body:
            score += min(12, c_body) * (3.5 if len(term) >= 4 else 2.2 if len(term) == 3 else 1.2)

    if doc.rank:
        score += max(0, 12 - math.log2(doc.rank + 1) * 2)
    if doc.score:
        score += min(16, math.log10(max(10, doc.score)) * 2)

    if doc.year in query:
        score += 15

    # 泡泡说切片更口语、更短兵相接，但更容易放大情绪；
    # 默认给长文本语料轻微优先级，避免只被切片带偏。
    if doc.source == '水球泡':
        score += 5

    return score


def make_chunks(body: str, max_lines: int = 12, stride: int = 6) -> List[str]:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return []
    if len(lines) <= max_lines:
        return ['\n'.join(lines)]
    chunks = []
    for i in range(0, len(lines), stride):
        chunk = lines[i:i + max_lines]
        if chunk:
            chunks.append('\n'.join(chunk))
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
        return 0.0, ''
    best = max(chunks, key=lambda c: chunk_score(c, query, terms))
    return chunk_score(best, query, terms), best


def iter_docs(corpus_dirs: List[Path], year: str | None = None, source: str | None = None) -> Iterable[Doc]:
    seen = set()
    for corpus_dir in corpus_dirs:
        normalized_source = normalize_source_name(corpus_dir.name)
        if source and normalized_source != source:
            continue
        for path in sorted(corpus_dir.rglob('*.txt')):
            if year and path.parent.name != year:
                continue
            dedupe_key = (normalized_source, path.parent.name, path.name)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            yield parse_doc(path, corpus_dir)


def main() -> int:
    ap = argparse.ArgumentParser(description='Search Shuiqiupao corpus for high-fidelity grounding.')
    ap.add_argument('query', help='Search query')
    ap.add_argument('--year', help='Limit to a year like 2024')
    ap.add_argument('--limit', type=int, default=8, help='Number of hits to show')
    ap.add_argument('--corpus-dir', help='Explicit corpus directory')
    ap.add_argument('--source', choices=['水球泡', '泡泡说'], help='Limit to one source corpus when needed')
    ap.add_argument('--show-body-path', action='store_true', help='Print absolute file path without shorthand')
    args = ap.parse_args()

    corpus_dirs = resolve_corpus_dirs(args.corpus_dir)
    terms = extract_terms(args.query)
    results = []

    for doc in iter_docs(corpus_dirs, args.year, args.source):
        ds = doc_score(doc, args.query, terms)
        if ds <= 0:
            continue
        es, excerpt = best_excerpt(doc, args.query, terms)
        total = ds + es
        if total <= 0:
            continue
        results.append((total, doc, excerpt))

    results.sort(key=lambda x: x[0], reverse=True)
    results = results[: args.limit]

    print('# 水球泡语料检索')
    print(f'- Query: {args.query}')
    print(f'- Corpora: {", ".join(str(p) for p in corpus_dirs)}')
    if args.source:
        print(f'- Source filter: {args.source}')
    print(f'- Terms: {", ".join(terms[:20]) if terms else "(none)"}')
    print(f'- Hits: {len(results)}')
    print()

    if not results:
        print('没有命中结果。可以尝试换关键词、加年份、加 --source，或拆成更短的问题。')
        return 0

    for idx, (score, doc, excerpt) in enumerate(results, 1):
        path_str = str(doc.path) if args.show_body_path else str(doc.path).replace(str(Path.home()), '~')
        print(f'## Hit {idx} | score={score:.1f} | source={doc.source} | year={doc.year} | rank={doc.rank or "?"} | heat={doc.score or "?"}')
        print(f'- File: {path_str}')
        if doc.title:
            print(f'- Title: {doc.title}')
        if doc.tags:
            print(f'- Tags: {" ".join(doc.tags)}')
        if excerpt:
            print('- Excerpt:')
            print('```text')
            excerpt = excerpt.strip()
            if len(excerpt) > 900:
                excerpt = excerpt[:900] + '\n…'
            print(excerpt)
            print('```')
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
