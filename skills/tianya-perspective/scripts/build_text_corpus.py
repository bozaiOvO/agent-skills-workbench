#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree


SUPPORTED_TEXT = {".md", ".txt"}
SUPPORTED_DOCX = {".docx"}
SUPPORTED_EPUB = {".epub"}
SUPPORTED_PDF = {".pdf"}
REFERENCE_EXTS = SUPPORTED_TEXT | SUPPORTED_DOCX | SUPPORTED_EPUB | SUPPORTED_PDF

BOARD_NAMES = [
    "kk合集【无水印】",
    "中医命理",
    "其他",
    "国际观察",
    "天涯小说",
    "天涯故事",
    "天涯杂谈",
    "情感天地",
    "煮酒论史",
    "经济论坛",
    "股市楼市",
    "莲蓬鬼话",
    "资料大合集",
]


@dataclass
class CorpusItem:
    item_id: str
    board: str
    title: str
    source_path: str
    relative_path: str
    ext: str
    size_bytes: int
    status: str
    text_chars: int
    output_path: str | None
    note: str


def stable_id(path: Path, root: Path) -> str:
    rel = str(path.relative_to(root))
    return hashlib.sha1(rel.encode("utf-8")).hexdigest()[:12]


def detect_board(path: Path, root: Path) -> str:
    rel_parts = path.relative_to(root).parts
    if len(rel_parts) == 1 and path.suffix.lower() in SUPPORTED_TEXT:
        return path.stem
    for part in rel_parts:
        if part in BOARD_NAMES:
            return part
    if rel_parts:
        return rel_parts[0]
    return "未分类"


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def read_plain(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "gb18030", "gbk", "big5", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", ns):
        texts = [node.text for node in para.findall(".//w:t", ns) if node.text]
        if texts:
            paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def read_epub(path: Path, max_chars: int) -> str:
    html_re = re.compile(r"<[^>]+>")
    parts: list[str] = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            lower = name.lower()
            if not lower.endswith((".html", ".xhtml", ".htm")):
                continue
            raw = zf.read(name).decode("utf-8", errors="ignore")
            text = html_re.sub(" ", raw)
            text = re.sub(r"\s+", " ", text)
            if text.strip():
                parts.append(text.strip())
            if sum(len(p) for p in parts) >= max_chars:
                break
    return "\n\n".join(parts)[:max_chars]


def read_pdf(path: Path, max_pages: int, max_chars: int) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        return "", f"pypdf unavailable: {exc}"

    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        pages = min(page_count, max_pages)
        parts: list[str] = []
        for idx in range(pages):
            try:
                page_text = reader.pages[idx].extract_text() or ""
            except Exception as exc:
                page_text = f"[page {idx + 1} extract failed: {exc}]"
            if page_text.strip():
                parts.append(page_text.strip())
            if sum(len(p) for p in parts) >= max_chars:
                break
        text = "\n\n".join(parts)[:max_chars]
        note = f"pdf_pages_read={pages}/{page_count}"
        if len(text.strip()) < 200:
            note += "; weak_text_or_scanned_pdf"
        return text, note
    except Exception as exc:
        return "", f"pdf_extract_failed: {exc}"


def extract_text(path: Path, max_pdf_pages: int, max_chars: int) -> tuple[str, str, str]:
    ext = path.suffix.lower()
    try:
        if ext in SUPPORTED_TEXT:
            return clean_text(read_plain(path)[:max_chars]), "ok", "plain_text"
        if ext in SUPPORTED_DOCX:
            return clean_text(read_docx(path)[:max_chars]), "ok", "docx"
        if ext in SUPPORTED_EPUB:
            return clean_text(read_epub(path, max_chars)), "ok", "epub"
        if ext in SUPPORTED_PDF:
            text, note = read_pdf(path, max_pdf_pages, max_chars)
            text = clean_text(text)
            status = "ok" if len(text) >= 200 else "weak"
            return text, status, note
        return "", "skipped", "unsupported_ext"
    except Exception as exc:
        return "", "failed", f"{type(exc).__name__}: {exc}"


def safe_name(name: str) -> str:
    name = re.sub(r"[/:\\]", "_", name)
    return name[:160]


def iter_source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.name.startswith(".") or not path.is_file():
            continue
        yield path


def split_chunks(text: str, chunk_chars: int, overlap: int) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def write_jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an agent-friendly Tianya text corpus.")
    parser.add_argument("--source", required=True, help="Original Tianya collection root")
    parser.add_argument("--output", required=True, help="Output corpus directory")
    parser.add_argument("--max-pdf-pages", type=int, default=30)
    parser.add_argument("--max-chars-per-file", type=int, default=120000)
    parser.add_argument("--chunk-chars", type=int, default=1800)
    parser.add_argument("--chunk-overlap", type=int, default=180)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"source not found: {source}")
    if args.reset and output.exists():
        shutil.rmtree(output)
    (output / "boards").mkdir(parents=True, exist_ok=True)
    (output / "items").mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    chunks: list[dict] = []
    summary: dict[str, dict[str, int]] = {}

    for path in iter_source_files(source):
        ext = path.suffix.lower()
        board = detect_board(path, source)
        size = path.stat().st_size
        item_id = stable_id(path, source)
        title = path.stem

        if ext not in REFERENCE_EXTS:
            item = CorpusItem(
                item_id=item_id,
                board=board,
                title=title,
                source_path=str(path),
                relative_path=str(path.relative_to(source)),
                ext=ext or "[noext]",
                size_bytes=size,
                status="archive_only",
                text_chars=0,
                output_path=None,
                note="kept as NAS/original archive; not useful for direct agent reading",
            )
            manifest.append(asdict(item))
            summary.setdefault(board, {}).setdefault("archive_only", 0)
            summary[board]["archive_only"] += 1
            continue

        text, status, note = extract_text(path, args.max_pdf_pages, args.max_chars_per_file)
        out_path = None
        if text:
            board_dir = output / "items" / safe_name(board)
            board_dir.mkdir(parents=True, exist_ok=True)
            out_file = board_dir / f"{item_id}_{safe_name(title)}.md"
            header = [
                "---",
                f"item_id: {item_id}",
                f"board: {json.dumps(board, ensure_ascii=False)}",
                f"title: {json.dumps(title, ensure_ascii=False)}",
                f"source_path: {json.dumps(str(path), ensure_ascii=False)}",
                f"relative_path: {json.dumps(str(path.relative_to(source)), ensure_ascii=False)}",
                f"status: {status}",
                f"note: {json.dumps(note, ensure_ascii=False)}",
                "---",
                "",
                f"# {title}",
                "",
            ]
            out_file.write_text("\n".join(header) + text + "\n", encoding="utf-8")
            out_path = str(out_file)
            for idx, chunk in enumerate(split_chunks(text, args.chunk_chars, args.chunk_overlap), 1):
                chunks.append(
                    {
                        "item_id": item_id,
                        "chunk_id": f"{item_id}-{idx:04d}",
                        "board": board,
                        "title": title,
                        "source_path": str(path),
                        "relative_path": str(path.relative_to(source)),
                        "chunk_index": idx,
                        "text": chunk,
                    }
                )

        item = CorpusItem(
            item_id=item_id,
            board=board,
            title=title,
            source_path=str(path),
            relative_path=str(path.relative_to(source)),
            ext=ext or "[noext]",
            size_bytes=size,
            status=status,
            text_chars=len(text),
            output_path=out_path,
            note=note,
        )
        manifest.append(asdict(item))
        summary.setdefault(board, {}).setdefault(status, 0)
        summary[board][status] += 1

    write_jsonl(output / "manifest.jsonl", manifest)
    write_jsonl(output / "chunks.jsonl", chunks)

    board_texts: dict[str, list[str]] = {}
    for row in chunks:
        board_texts.setdefault(row["board"], []).append(
            f"\n\n## {row['title']} · chunk {row['chunk_index']}\n\n{row['text']}"
        )
    for board, parts in board_texts.items():
        (output / "boards" / f"{safe_name(board)}.md").write_text(
            f"# 天涯本地语料 · {board}\n" + "".join(parts), encoding="utf-8"
        )

    report = {
        "source": str(source),
        "output": str(output),
        "manifest_items": len(manifest),
        "chunks": len(chunks),
        "summary": summary,
    }
    (output / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
