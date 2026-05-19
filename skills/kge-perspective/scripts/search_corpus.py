#!/usr/bin/env python3
"""K哥语料检索工具。搜索程序员K哥的抖音转录语料，按相关度排序输出。"""
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
    Path.home() / 'Desktop' / 'TikTokDownloader-master' / 'Volume' / '整理输出_按年份热度' / '程序员K哥',
]
STOPWORDS = {
    '什么', '怎么', '是不是', '可以', '一下', '这个', '那个', '我们', '你们', '他们', '自己', '一个', '一种',
    '为什么', '如何', '哪些', '怎么做', '一下子', '就是', '还是', '还有', '以及', '如果', '但是', '然后',
    '时候', '事情', '问题', '因为', '所以', '已经', '没有', '需要', '想要', '感觉', '觉得', '关于', '对于',
    '能不能', '要不要', '应该', '现在', '未来', '直接', '真的', '比较', '特别', '可能', '大概', '这里', '那里',
}

# 排除模拟面试类文件
EXCLUDE_PATTERNS = ['假扮', '摸底', '拉扯', '沉浸式', '压力面试', '模拟面试']

# 轻量主题词映射：给常见用户问法补近义召回
TOPIC_SYNONYMS = {
    '考研': ['读研', '学历', '硕士', '二战', '三战', '数学'],
    '读研': ['考研', '学历', '硕士'],
    '工作': ['上班', '求职', '就业', '入职', '找工作'],
    '找工作': ['求职', '就业', '投简历', '面试'],
    '面试': ['八股文', '简历', '包装', '自我介绍', '项目经验'],
    '八股文': ['面试', '理论', 'mysql', 'redis', 'jvm', '并发'],
    '培训': ['报班', '线下班', '组织', '燕雀教育', '自学'],
    '报班': ['培训', '线下班', '组织', '花钱', '投资自己'],
    '自学': ['报班', '培训', '路径', '路线'],
    '实习': ['应届生', '校招', '秋招', '春招'],
    '跳槽': ['涨薪', '离职', '骑驴找马', '五年三跳'],
    '涨薪': ['跳槽', '薪资', '月薪', '年薪'],
    '外包': ['自研', '小公司', '大厂'],
    'ai': ['人工智能', '风口', '大模型', 'agent', '淘汰'],
    '人工智能': ['ai', '风口', '大模型', 'agent'],
    '风口': ['ai', '红利', '窗口期', '供需'],
    'java': ['后端', '苍穹外卖', 'spring', 'springboot'],
    '苍穹外卖': ['java', '项目', '敲两遍'],
    '包装': ['简历', 'boxing', '面试', '项目经验'],
    '简历': ['包装', '投递', 'boss', '海投'],
    '城市': ['北京', '上海', '杭州', '深圳', '一线'],
    '薪资': ['月薪', '年薪', '涨薪', '万'],
    '前端': ['后端', '全栈', '淘汰'],
    '花钱': ['投资自己', '报班', '培训', '学费'],
    '投资自己': ['花钱', '报班', '加速'],
    '学历': ['考研', '本科', '专科', '双非', '985', '211'],
}


@dataclass
class Doc:
    path: Path
    corpus_root: Path
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


def should_exclude(path: Path) -> bool:
    name = path.name
    return any(pat in name for pat in EXCLUDE_PATTERNS)


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

    # 年份加权：2026 > 2025 > 2024，最新观点更权威
    year_bonus = {'2026': 8, '2025': 3, '2024': 0}
    score += year_bonus.get(doc.year, 0)

    if doc.year in query:
        score += 15

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


def iter_docs(corpus_dirs: List[Path], year: str | None = None) -> Iterable[Doc]:
    seen = set()
    for corpus_dir in corpus_dirs:
        for path in sorted(corpus_dir.rglob('*.txt')):
            if should_exclude(path):
                continue
            if year and path.parent.name != year:
                continue
            dedupe_key = (path.parent.name, path.name)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            yield parse_doc(path, corpus_dir)


def main() -> int:
    ap = argparse.ArgumentParser(description='Search K哥 corpus for high-fidelity grounding.')
    ap.add_argument('query', help='Search query')
    ap.add_argument('--year', help='Limit to a year like 2024, 2025, 2026')
    ap.add_argument('--limit', type=int, default=8, help='Number of hits to show')
    ap.add_argument('--corpus-dir', help='Explicit corpus directory')
    ap.add_argument('--show-body-path', action='store_true', help='Print absolute file path')
    args = ap.parse_args()

    corpus_dirs = resolve_corpus_dirs(args.corpus_dir)
    terms = extract_terms(args.query)
    results = []

    for doc in iter_docs(corpus_dirs, args.year):
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

    print('# K哥语料检索')
    print(f'- Query: {args.query}')
    print(f'- Corpora: {", ".join(str(p) for p in corpus_dirs)}')
    print(f'- Terms: {", ".join(terms[:20]) if terms else "(none)"}')
    print(f'- Hits: {len(results)}')
    print()

    if not results:
        print('没有命中结果。可以尝试换关键词或加年份过滤。')
        return 0

    for idx, (score, doc, excerpt) in enumerate(results, 1):
        path_str = str(doc.path) if args.show_body_path else str(doc.path).replace(str(Path.home()), '~')
        print(f'## Hit {idx} | score={score:.1f} | year={doc.year} | rank={doc.rank or "?"} | heat={doc.score or "?"}')
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
                excerpt = excerpt[:900] + '\n...'
            print(excerpt)
            print('```')
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
