#!/usr/bin/env python3
"""Lightweight quality gate for livestream structured reading docs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CALL_SECTION_RE = re.compile(r"^##\s+整场连麦咨询", re.M)
QA_SECTION_RE = re.compile(r"^##\s+普通\s*QA\s*问答", re.M)
TEACH_SECTION_RE = re.compile(r"^##\s+主播主动讲解", re.M)
CHECK_SECTION_RE = re.compile(r"^##\s+分段核对版", re.M)
ITEM_RE = re.compile(r"^###\s+([LQT])(\d+)\.\s+(.+)$", re.M)
DEEP_QA_TOPIC_RE = re.compile(
    r"Java|Python|AI|大模型|Agent|前端|后端|测试|运维|云计算|网络安全|网安|嵌入式|"
    r"秋招|春招|校招|社招|实习|就业|薪资|工资|简历|面试|项目|学历|本科|专科|"
    r"机构|报班|培训|先学后付|零元|贷款|转行|考研|读研|方向|路线|周期",
    re.I,
)


def section(text: str, heading_pattern: re.Pattern[str]) -> str:
    match = heading_pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.M)
    if not next_heading:
        return text[start:]
    return text[start : start + next_heading.start()]


def line_count(text: str) -> int:
    return len([line for line in text.splitlines() if line.strip()])


def dialogue_stats(block: str) -> tuple[int, int]:
    marker = re.search(r"完整对话(?:（[^）]*）)?|完整对话整理", block)
    if not marker:
        return 0, 0
    dialogue = block[marker.end() :]
    next_meta = re.search(r"^\*\*(?:沟通技法拆解|连麦处理策略|可复用指数|来源定位|问题|回答要点)", dialogue, re.M)
    if next_meta:
        dialogue = dialogue[: next_meta.start()]
    turns = len(re.findall(r"^\*\*(?:连麦人|主播|咨询者|嘉宾|学生|家长)[^：]{0,8}：", dialogue, re.M))
    chars = len(re.sub(r"\s+", "", dialogue))
    return turns, chars


def audit(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    warnings: list[str] = []

    stripped = text.lstrip()
    if not (stripped.startswith("---") or stripped.startswith("# 结构化阅读稿")):
        errors.append("not_markdown_document_start")
    for marker in (
        "codex_core::",
        "session id:",
        "\nexec\n",
        "/bin/zsh -lc",
        "succeeded in",
        "model_provider",
        "approval_policy",
    ):
        if marker in text:
            errors.append(f"codex_log_contamination: {marker}")

    if len(text.strip()) < 1200:
        errors.append("document_too_short: output is suspiciously tiny")

    for label, pattern in (
        ("整场连麦咨询", CALL_SECTION_RE),
        ("普通 QA 问答", QA_SECTION_RE),
        ("主播主动讲解", TEACH_SECTION_RE),
        ("分段核对版", CHECK_SECTION_RE),
    ):
        if not pattern.search(text):
            errors.append(f"missing_section: {label}")

    items = ITEM_RE.findall(text)
    if not items:
        errors.append("missing_items: no Lxx/Qxx/Txx entries found")

    call_text = section(text, CALL_SECTION_RE)
    call_blocks = re.findall(
        r"^###\s+L(\d+)\..*?\n(.*?)(?=^###\s+[LQT]\d+\.|^##\s+|\Z)",
        call_text,
        re.S | re.M,
    )
    for number, block in call_blocks:
        dialogue_marker_count = len(
            re.findall(r"\*\*完整对话(?:（[^）]*）|整理)?[：:]", block)
        )
        if dialogue_marker_count > 1:
            errors.append(
                f"L{number}: multiple_dialogue_sections: count={dialogue_marker_count}"
            )
        if re.search(r"[^\n][ \t]*\*\*完整对话(?:（[^）]*）|整理)?[：:]", block):
            errors.append(f"L{number}: inline_dialogue_heading")
        for required in (
            "来源定位",
            "连麦状态",
            "连麦人基本情况",
            "连麦大致内容",
            "核心建议",
        ):
            if required not in block:
                errors.append(f"L{number}: missing_field: {required}")
        if "完整对话" not in block and "完整对话整理" not in block:
            warnings.append(f"L{number}: missing_dialogue")
        else:
            turns, chars = dialogue_stats(block)
            high_value = re.search(r"案例价值\s*[：:][^\n]*高", block) is not None
            medium_value = re.search(r"案例价值\s*[：:][^\n]*中", block) is not None
            if turns < 8 or chars < 450:
                errors.append(
                    f"L{number}: dialogue_too_short_for_call: turns={turns} chars={chars}"
                )
            elif high_value and (turns < 10 or chars < 650):
                errors.append(
                    f"L{number}: dialogue_too_short_for_high_value: turns={turns} chars={chars}"
                )
            elif medium_value and (turns < 8 or chars < 450):
                warnings.append(
                    f"L{number}: dialogue_maybe_too_short_for_medium_value: turns={turns} chars={chars}"
                )
        if "沟通技法拆解" not in block:
            errors.append(f"L{number}: missing_communication_technique_breakdown")

    qa_text = section(text, QA_SECTION_RE)
    teach_text = section(text, TEACH_SECTION_RE)
    qa_blocks = re.findall(
        r"^###\s+Q(\d+)\..*?\n(.*?)(?=^###\s+[QT]\d+\.|^##\s+|\Z)",
        qa_text,
        re.S | re.M,
    )
    for number, block in qa_blocks:
        if "原文优化版" not in block:
            errors.append(f"Q{number}: missing_optimized_original_text")
    if len(qa_blocks) >= 4:
        short_deep_candidates = 0
        expanded_deep_candidates = 0
        for _number, block in qa_blocks:
            compact = re.sub(r"\s+", "", block)
            if DEEP_QA_TOPIC_RE.search(block):
                if "回答展开" in block or len(compact) >= 260:
                    expanded_deep_candidates += 1
                elif len(compact) < 220:
                    short_deep_candidates += 1
        if short_deep_candidates >= max(3, len(qa_blocks) // 3) and expanded_deep_candidates == 0:
            warnings.append(
                f"qa_answers_may_be_overcompressed: short_deep_candidates={short_deep_candidates} qa_count={len(qa_blocks)}"
            )
    if line_count(qa_text) > 220:
        warnings.append("qa_section_long: QA may be repeating transcript instead of summarizing")
    if line_count(teach_text) > 260:
        warnings.append("teaching_section_long: host-led teaching may be repeating transcript")

    operations_terms = "福袋|扣 ?6|扣六|点关注|进粉丝群|资料领取|连麦加灯牌|付款|分期|贷款"
    for title in re.findall(r"^###\s+L\d+\.\s+(.+)$", call_text, re.M):
        if re.search(operations_terms, title):
            warnings.append(f"suspicious_call_title: {title}")

    titles = [title.strip() for kind, _, title in items if kind == "L"]
    normalized: dict[str, int] = {}
    for title in titles:
        key = re.sub(r"[（(].*?[）)]", "", title)
        key = re.sub(r"\s+", "", key)
        if not key:
            continue
        normalized[key] = normalized.get(key, 0) + 1
    for key, count in normalized.items():
        if count > 1:
            errors.append(f"duplicate_call_title: {key} appears {count} times")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit livestream structured reading markdown files.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        errors, warnings = audit(path)
        print(f"== {path} ==")
        if not errors and not warnings:
            print("PASS")
            continue
        for item in errors:
            print(f"ERROR {item}")
        for item in warnings:
            print(f"WARN {item}")
        if errors:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
