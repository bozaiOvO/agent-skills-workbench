#!/usr/bin/env python3
"""K哥语料检索工具。

唯一真源指向 AutomationCenter：
- 抖音脚本库 / 时间排序：观点版本、时间线、当前判断
- 抖音脚本库 / TOP排序：爆款结构、表达节奏、用户痛点
- 直播脚本库：即时判断、连麦诊断、最新口语表达
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

AUTOMATION_CENTER = Path.home() / 'AutomationCenter'
KGE_BLOGGER_NAME = '程序员K哥'

DEFAULT_CORPUS_ROOTS = [
    ('time', AUTOMATION_CENTER / 'outputs' / 'bloggers' / '抖音脚本库' / '时间排序' / KGE_BLOGGER_NAME),
    ('top', AUTOMATION_CENTER / 'outputs' / 'bloggers' / '抖音脚本库' / 'TOP排序' / KGE_BLOGGER_NAME),
    ('live', AUTOMATION_CENTER / 'outputs' / 'live' / KGE_BLOGGER_NAME),
]
DEFAULT_JSONL_INDEX = AUTOMATION_CENTER / 'outputs' / '脚本库索引' / KGE_BLOGGER_NAME / 'kge_corpus_all.jsonl'


def delegate_to_shared_index() -> None:
    if os.environ.get('PERSONA_CORPUS_BACKEND', '').lower() == 'files':
        return
    fallback_flags = {'--corpus-dir', '--jsonl-index', '--no-jsonl', '--list-corpora'}
    if any(flag in sys.argv[1:] for flag in fallback_flags):
        return
    search_script = AUTOMATION_CENTER / 'scripts' / 'search_persona_corpus.py'
    sqlite_index = AUTOMATION_CENTER / 'outputs' / '脚本库索引' / KGE_BLOGGER_NAME / 'corpus.sqlite3'
    if search_script.is_file() and sqlite_index.is_file():
        os.execv(sys.executable, [sys.executable, str(search_script), *sys.argv[1:], '--persona', 'kge'])

SOURCE_PRESETS = {
    'all': {'time', 'top', 'live'},
    'current': {'time', 'live'},
    'timeline': {'time', 'live'},
    'style': {'top', 'live'},
    'time': {'time'},
    'top': {'top'},
    'live': {'live'},
}

LIVE_INCLUDE_NAMES = {
    'qa_verbatim.md',
    'raw_transcript.txt',
    'full_session_qa_for_analysis.md',
}

STOPWORDS = {
    '什么', '怎么', '是不是', '可以', '一下', '这个', '那个', '我们', '你们', '他们', '自己', '一个', '一种',
    '为什么', '如何', '哪些', '怎么做', '一下子', '就是', '还是', '还有', '以及', '如果', '但是', '然后',
    '时候', '事情', '问题', '因为', '所以', '已经', '没有', '需要', '想要', '感觉', '觉得', '关于', '对于',
    '能不能', '要不要', '应该', '现在', '未来', '直接', '真的', '比较', '特别', '可能', '大概', '这里', '那里',
}

# 排除模拟面试类文件：它们更像演示内容，默认不作为 K哥稳定观点证据。
EXCLUDE_PATTERNS = ['假扮', '摸底', '拉扯', '沉浸式', '压力面试', '模拟面试']

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


@dataclass(frozen=True)
class CorpusRoot:
    kind: str
    path: Path


@dataclass
class Doc:
    path: Path
    corpus_root: Path
    source_kind: str
    year: str
    rank: int | None
    title: str
    tags: List[str]
    heat: int | None
    body: str


def resolve_corpus_roots(explicit: str | None, source: str) -> List[CorpusRoot]:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_dir():
            raise SystemExit(f'Corpus dir not found: {p}')
        return [CorpusRoot('custom', p)]

    wanted = SOURCE_PRESETS[source]
    roots: List[CorpusRoot] = []
    for kind, path in DEFAULT_CORPUS_ROOTS:
        rp = path.expanduser().resolve()
        if kind in wanted and rp.is_dir():
            roots.append(CorpusRoot(kind, rp))

    if roots:
        return roots

    expected = ', '.join(str(p) for kind, p in DEFAULT_CORPUS_ROOTS if kind in wanted)
    raise SystemExit(f'No AutomationCenter corpus directory found. Expected one of: {expected}')


def should_exclude(path: Path) -> bool:
    return any(pat in path.name for pat in EXCLUDE_PATTERNS)


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith('---\n'):
        return {}
    parts = text.split('---\n', 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta


def strip_frontmatter(text: str) -> str:
    if not text.startswith('---\n'):
        return text
    parts = text.split('---\n', 2)
    return parts[2] if len(parts) >= 3 else text


def grab_markdown_h1(text: str) -> str:
    m = re.search(r'^#\s+(.+)$', text, re.M)
    return m.group(1).strip() if m else ''


def extract_short_video_body(text: str) -> str:
    text = strip_frontmatter(text)
    marker = '## 可读正文'
    if marker in text:
        return text.split(marker, 1)[1].strip()
    legacy_marker = '=======下为正文============'
    if legacy_marker in text:
        return text.split(legacy_marker, 1)[1].strip()
    return text.strip()


def extract_live_body(text: str, path: Path) -> str:
    if path.suffix == '.txt':
        return text.strip()
    marker = '## QA 逐字稿'
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return strip_frontmatter(text).strip()


def parse_year(path: Path, meta: dict[str, str]) -> str:
    for key in ('publish_time', 'time', 'date'):
        value = meta.get(key, '')
        m = re.search(r'(20\d{2})', value)
        if m:
            return m.group(1)
    for part in reversed(path.parts):
        m = re.search(r'(20\d{2})', part)
        if m:
            return m.group(1)
    return 'unknown'


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r'\D+', '', value)
    return int(digits) if digits else None


def parse_doc(path: Path, corpus_root: CorpusRoot) -> Doc:
    text = read_text(path)
    meta = parse_frontmatter(text)

    title = meta.get('title') or grab_markdown_h1(strip_frontmatter(text)) or path.stem
    tags_text = meta.get('tags_text') or meta.get('tags') or ''
    tags = [t for t in re.split(r'[\s,，/]+', tags_text) if t]

    if corpus_root.kind == 'live':
        body = extract_live_body(text, path)
        tags = tags or ['直播', path.name]
    else:
        body = extract_short_video_body(text)

    m = re.search(r'top(\d+)[_-]', path.name)
    rank = int(m.group(1)) if m else None
    heat = parse_int(meta.get('综合分') or meta.get('heat') or meta.get('score'))

    return Doc(
        path=path,
        corpus_root=corpus_root.path,
        source_kind=corpus_root.kind,
        year=parse_year(path, meta),
        rank=rank,
        title=title,
        tags=tags,
        heat=heat,
        body=body,
    )


def iter_candidate_paths(root: CorpusRoot) -> Iterable[Path]:
    if root.kind == 'live':
        for path in sorted(root.path.rglob('*')):
            if path.is_file() and path.name in LIVE_INCLUDE_NAMES:
                yield path
        return

    for suffix in ('*.md', '*.txt'):
        yield from sorted(root.path.rglob(suffix))


def iter_docs(corpus_roots: List[CorpusRoot], year: str | None = None) -> Iterable[Doc]:
    for root in corpus_roots:
        for path in iter_candidate_paths(root):
            if should_exclude(path):
                continue
            doc = parse_doc(path, root)
            if year and doc.year != year:
                continue
            yield doc


def iter_jsonl_docs(index_path: Path, source: str, year: str | None = None) -> Iterable[Doc]:
    allowed = SOURCE_PRESETS[source]
    with index_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            source_kind = str(row.get('source_type') or 'custom')
            if source_kind == 'short_video':
                rank = row.get('rank') if isinstance(row.get('rank'), int) else None
                if source == 'live':
                    continue
                if source == 'top' and rank is None:
                    continue
                source_kind = 'top' if source in {'top', 'style'} and rank is not None else 'time'
            elif source_kind not in allowed:
                continue
            row_year = str(row.get('year') or 'unknown')
            if year and row_year != year:
                continue
            path = Path(str(row.get('path') or ''))
            yield Doc(
                path=path,
                corpus_root=index_path,
                source_kind=source_kind,
                year=row_year,
                rank=row.get('rank') if isinstance(row.get('rank'), int) else None,
                title=str(row.get('title') or path.stem),
                tags=[str(t) for t in row.get('tags', []) if t],
                heat=row.get('heat') if isinstance(row.get('heat'), int) else None,
                body=str(row.get('text') or row.get('body') or ''),
            )


def extract_terms(query: str) -> List[str]:
    query = query.strip()
    terms: List[str] = []

    normalized_query = query.lower()
    for token in re.findall(r'[A-Za-z0-9][A-Za-z0-9+.#_-]{1,}', normalized_query):
        if token not in STOPWORDS:
            terms.append(token)
        terms.extend(t for t in TOPIC_SYNONYMS.get(token, []) if t not in STOPWORDS)

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
                    terms.extend(t for t in TOPIC_SYNONYMS.get(gram, []) if t not in STOPWORDS)

    seen = set()
    out = []
    for term in terms:
        if len(term) < 2 or term in seen:
            continue
        seen.add(term)
        out.append(term)
    return out[:120]


def normalize(text: str) -> str:
    return text.lower()


def term_count(text: str, term: str) -> int:
    return normalize(text).count(term.lower())


def source_bonus(doc: Doc, source: str) -> float:
    if source == 'style':
        return {'top': 18.0, 'live': 12.0, 'time': 2.0}.get(doc.source_kind, 0.0)
    if source == 'current':
        return {'live': 18.0, 'time': 10.0, 'top': -4.0}.get(doc.source_kind, 0.0)
    if source == 'timeline':
        return {'time': 14.0, 'live': 8.0, 'top': -2.0}.get(doc.source_kind, 0.0)
    return {'live': 10.0, 'time': 6.0, 'top': 4.0}.get(doc.source_kind, 0.0)


def year_bonus(year: str) -> float:
    if not year.isdigit():
        return 0.0
    y = int(year)
    if y >= 2026:
        return 10.0
    if y == 2025:
        return 4.0
    if y == 2024:
        return 1.0
    return 0.0


def doc_score(doc: Doc, query: str, terms: List[str], source: str) -> float:
    hay_title = doc.title or doc.path.name
    hay_tags = ' '.join(doc.tags)
    hay_body = doc.body
    score = source_bonus(doc, source) + year_bonus(doc.year)

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
    if doc.heat:
        score += min(16, math.log10(max(10, doc.heat)) * 2)

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


def main() -> int:
    ap = argparse.ArgumentParser(description='Search K哥 AutomationCenter corpus for high-fidelity grounding.')
    ap.add_argument('query', nargs='?', default='', help='Search query')
    ap.add_argument('--year', help='Limit to a year like 2024, 2025, 2026')
    ap.add_argument('--limit', type=int, default=8, help='Number of hits to show')
    ap.add_argument('--source', choices=sorted(SOURCE_PRESETS), default='all',
                    help='Corpus route: current=time+live, style=top+live, timeline=time+live')
    ap.add_argument('--corpus-dir', help='Explicit corpus directory; overrides --source')
    ap.add_argument('--jsonl-index', default=str(DEFAULT_JSONL_INDEX), help='JSONL corpus index path')
    ap.add_argument('--no-jsonl', action='store_true', help='Scan source directories instead of JSONL index')
    ap.add_argument('--show-body-path', action='store_true', help='Print absolute file path')
    ap.add_argument('--list-corpora', action='store_true', help='Print configured corpus roots and exit')
    args = ap.parse_args()

    corpus_roots = resolve_corpus_roots(args.corpus_dir, args.source)
    if args.list_corpora:
        for root in corpus_roots:
            print(f'{root.kind}\t{root.path}')
        return 0

    terms = extract_terms(args.query)
    results = []
    index_path = Path(args.jsonl_index).expanduser().resolve()
    use_jsonl = not args.no_jsonl and not args.corpus_dir and index_path.is_file()
    docs = iter_jsonl_docs(index_path, args.source, args.year) if use_jsonl else iter_docs(corpus_roots, args.year)

    for doc in docs:
        ds = doc_score(doc, args.query, terms, args.source)
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
    print(f'- Query: {args.query or "(empty)"}')
    print(f'- Source route: {args.source}')
    print(f'- Index: {index_path if use_jsonl else "(directory scan)"}')
    print(f'- Corpora: {", ".join(f"{r.kind}={r.path}" for r in corpus_roots)}')
    print(f'- Terms: {", ".join(terms[:20]) if terms else "(none)"}')
    print(f'- Hits: {len(results)}')
    print()

    if not results:
        print('没有命中结果。可以尝试换关键词、加年份过滤，或切换 --source。')
        return 0

    for idx, (score, doc, excerpt) in enumerate(results, 1):
        path_str = str(doc.path) if args.show_body_path else str(doc.path).replace(str(Path.home()), '~')
        print(
            f'## Hit {idx} | score={score:.1f} | source={doc.source_kind} '
            f'| year={doc.year} | rank={doc.rank or "?"} | heat={doc.heat or "?"}'
        )
        print(f'- File: {path_str}')
        if doc.title:
            print(f'- Title: {doc.title}')
        if doc.tags:
            print(f'- Tags: {" ".join(doc.tags[:12])}')
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
    delegate_to_shared_index()
    sys.exit(main())
