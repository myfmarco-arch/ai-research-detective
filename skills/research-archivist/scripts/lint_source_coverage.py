#!/usr/bin/env python3
"""lint wiki/_source_coverage.md for per-source intake depth records."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ["关键观察", "原始引用", "痛点", "积极信号", "矛盾", "未归类"]
LOW_REASON_KEYS = ["少量提取原因", "少量原因", "提取较少原因"]
SOURCE_RE = re.compile(r"#(interview|survey|feedback)_[A-Za-z0-9_-]+")


def source_ids(data_dir: Path) -> list[str]:
    ids: list[str] = []
    for p in sorted(data_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".json", ".csv"}:
            stem = p.stem
            if re.match(r"(?:interview|survey|feedback)_[A-Za-z0-9_-]+$", stem):
                ids.append(stem)
    return ids


def lint(wiki_dir: Path, data_dir: Path) -> list[str]:
    findings: list[str] = []
    coverage = wiki_dir / "_source_coverage.md"
    if not coverage.is_file():
        return ["[COV_MISSING] 缺 wiki/_source_coverage.md。每份资料必须有覆盖台账。"]
    text = coverage.read_text(encoding="utf-8")
    ids = source_ids(data_dir)
    for sid in ids:
        marker = f"#{sid}"
        if marker not in text:
            findings.append(f"[COV_SOURCE_MISSING] 缺 {marker} 的覆盖记录。")
            continue
        start = text.find(marker)
        next_match = SOURCE_RE.search(text, start + len(marker))
        section = text[start: next_match.start() if next_match else len(text)]
        missing = [field for field in REQUIRED_FIELDS if field not in section]
        if missing:
            findings.append(f"[COV_FIELD_MISSING] {marker} 缺字段: {', '.join(missing)}。")
        nums = [int(n) for n in re.findall(r"(?:关键观察|原始引用|痛点|积极信号|矛盾|未归类)[^\n\d]*(\d+)", section)]
        total = sum(nums)
        has_reason = any(k in section for k in LOW_REASON_KEYS)
        if total <= 3 and not has_reason:
            findings.append(f"[COV_LOW_NO_REASON] {marker} 提取量很少({total})但未写少量提取原因。")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="lint wiki/_source_coverage.md coverage depth records")
    parser.add_argument("wiki_dir", help="wiki/ directory")
    parser.add_argument("--data-dir", help="data/ directory; defaults to wiki/../data")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    wiki_dir = Path(args.wiki_dir)
    data_dir = Path(args.data_dir) if args.data_dir else wiki_dir.parent / "data"
    if not wiki_dir.is_dir():
        if not args.quiet:
            print(f"lint_source_coverage: wiki 目录不存在: {wiki_dir}", file=sys.stderr)
        return 2
    if not data_dir.is_dir():
        if not args.quiet:
            print(f"lint_source_coverage: data 目录不存在: {data_dir}", file=sys.stderr)
        return 2
    findings = lint(wiki_dir, data_dir)
    if args.quiet:
        return 1 if findings else 0
    if findings:
        print(f"FAIL — {len(findings)} 个覆盖问题")
        for f in findings:
            print(f)
        return 1
    print("PASS — _source_coverage.md 覆盖台账完整")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
