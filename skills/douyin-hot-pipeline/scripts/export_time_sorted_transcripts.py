#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import organize_transcripts_by_year as organizer


DEFAULT_VOLUME_ROOT = organizer.DEFAULT_VOLUME_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Rewrite transcript txt files with metadata headers while keeping normal time-based filenames.'
    )
    parser.add_argument('--volume-root', type=Path, default=DEFAULT_VOLUME_ROOT)
    parser.add_argument('--transcript-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--stem', dest='stems', action='append', default=[])
    return parser.parse_args()


def transcript_map(folder: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in folder.iterdir():
        if not path.is_file() or organizer.is_temporary_file(path):
            continue
        if path.suffix.lower() != '.txt':
            continue
        result[path.stem] = path
    return result


def row_targets(row_data: dict[str, object], txt_files: dict[str, Path]) -> list[Path]:
    stem = organizer.expected_transcript_stem(row_data)
    transcript = txt_files.get(stem)
    if transcript is not None:
        return [transcript]
    prefix = organizer.transcript_prefix(row_data)
    if not prefix:
        return []
    return sorted(path for key, path in txt_files.items() if key.startswith(prefix))


def build_item(row_data: dict[str, object], transcript: Path) -> dict[str, object]:
    publish_time = organizer.normalize_datetime_text(row_data.get('发布时间'))
    work_id = str(row_data.get('作品ID') or '').strip()
    return {
        'stem': transcript.stem,
        'body': organizer.read_text_with_fallback(transcript),
        'comments': organizer.safe_int(row_data.get('评论数量')),
        'favorites': organizer.safe_int(row_data.get('收藏数量')),
        'shares': organizer.safe_int(row_data.get('分享数量')),
        'likes': organizer.safe_int(row_data.get('点赞数量')),
        'duration': str(row_data.get('视频时长') or ''),
        'publish_time': publish_time,
        'publish_sort': publish_time,
        'score': organizer.score_row(row_data),
        'title': organizer.extract_title(row_data.get('作品描述')),
        'tags': organizer.extract_tags(row_data.get('作品话题'), row_data.get('作品描述')),
        'work_id': work_id,
    }


def export_workbook(workbook_path: Path, transcript_dir: Path, output_dir: Path) -> tuple[int, int, int]:
    header, rows = organizer.workbook_rows(workbook_path)
    txt_files = transcript_map(transcript_dir)
    matched_files: set[Path] = set()
    matched_rows = 0
    unmatched_rows = 0
    written = 0

    for row in rows:
        row_data = organizer.row_to_dict(header, row)
        targets = row_targets(row_data, txt_files)
        if not targets:
            unmatched_rows += 1
            continue
        matched_rows += 1
        for transcript in targets:
            if transcript in matched_files:
                continue
            output_path = output_dir / transcript.name
            output_path.write_text(organizer.render_output(build_item(row_data, transcript)), encoding='utf-8')
            matched_files.add(transcript)
            written += 1

    return written, matched_rows, unmatched_rows


def main() -> int:
    args = parse_args()
    volume_root = args.volume_root.expanduser().resolve()
    transcript_dir = args.transcript_dir.expanduser().resolve()
    output_dir = (args.output_dir or args.transcript_dir).expanduser().resolve()
    data_root = volume_root / 'Data'
    stems = set(args.stems)

    if not volume_root.is_dir():
        raise SystemExit(f'Volume root not found: {volume_root}')
    if not data_root.is_dir():
        raise SystemExit(f'Data root not found: {data_root}')
    if not transcript_dir.is_dir():
        raise SystemExit(f'Transcript dir not found: {transcript_dir}')

    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_paths = sorted(
        path
        for path in data_root.glob('UID*.xlsx')
        if path.is_file() and not organizer.is_temporary_file(path) and (not stems or path.stem in stems)
    )

    total_written = 0
    total_matched_rows = 0
    total_unmatched_rows = 0
    for workbook_path in workbook_paths:
        written, matched_rows, unmatched_rows = export_workbook(workbook_path, transcript_dir, output_dir)
        total_written += written
        total_matched_rows += matched_rows
        total_unmatched_rows += unmatched_rows
        print(
            f'OK {workbook_path.stem} written={written} matched_rows={matched_rows} '
            f'unmatched_rows={unmatched_rows} output={output_dir}'
        )

    print(
        f'SUMMARY written={total_written} matched_rows={total_matched_rows} '
        f'unmatched_rows={total_unmatched_rows} output={output_dir}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
