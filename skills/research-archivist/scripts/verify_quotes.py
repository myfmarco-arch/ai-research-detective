#!/usr/bin/env python3
"""
wiki 引用真实性全量校验 —— 反幻觉 H3(引用改写)。

扫 wiki/themes/*.md 「证据」栏 + wiki/quotes.md 中所有形如
    - #interview_xx: "..."
的引用,逐条到 data/<id>.* 原始资料里子串匹配。改一个字就 fail。

容忍:
- 省略号 `...` / `…`:按省略号切片,每段都必须在原文出现且按顺序
- 空白:连续空白(空格/换行/Tab)归一
- 引号:中英文引号、书名号、单/双都视作等价分隔符
- 标点:全/半角逗号、句号、问号、感叹号互通

不校验:
- 「分析增量」栏(允许改写型摘录)
- `#analysis_*` / `#review_*` 编号(那些是分析涌现,不是一手引用)

CLI:
    python verify_quotes.py <wiki_dir> [--data-dir <data_dir>] [--quiet]

默认 data_dir = wiki_dir/../data。

Exit:
    0 = 全部命中
    1 = 至少一条引用未在原始资料中找到
    2 = 路径错误 / 读取失败
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


# ---------- 数据结构 ----------

@dataclass
class QuoteRef:
    source_file: Path        # wiki 文件
    source_line: int         # 1-based
    ref_id: str              # interview_07 / survey_03 / feedback_12
    quote: str               # 原始引用串(尚未 normalize)


@dataclass
class VerifyResult:
    quote: QuoteRef
    found: bool
    data_path: Path | None   # 命中的原始资料路径(找不到时为 None)
    reason: str              # 失败原因


# ---------- 引用提取 ----------

# 主题页「证据」栏标记:从 `## 证据` 行到下一个同级 / 上级 header
EVIDENCE_HEADER_RE = re.compile(r"^##\s+证据")
NEXT_HEADER_RE = re.compile(r"^#{1,6}\s+")

# 引用条目:行内必须有 #interview_xx / #survey_xx / #feedback_xx 编号 + 引号包裹的引用
# 引号支持:中文「」『』、双引号 ""、英文 "" ''
REF_ID_RE = re.compile(r"#((?:interview|survey|feedback)_[A-Za-z0-9_-]+)")
QUOTE_PATTERNS = [
    re.compile(r"「([^」\n]{2,})」"),
    re.compile(r"『([^』\n]{2,})』"),
    re.compile(r"\"([^\"\n]{2,})\""),
    re.compile(r"“([^”\n]{2,})”"),
    re.compile(r"‘([^’\n]{2,})’"),
    re.compile(r"'([^'\n]{2,})'"),
]


def extract_quotes_from_themes(wiki_dir: Path) -> list[QuoteRef]:
    """扫 wiki/themes/*.md 的「证据」栏。"""
    refs: list[QuoteRef] = []
    themes_dir = wiki_dir / "themes"
    if not themes_dir.is_dir():
        return refs

    for md_file in sorted(themes_dir.glob("*.md")):
        refs.extend(_extract_from_file(md_file, evidence_only=True))
    return refs


def extract_quotes_from_quotes_page(wiki_dir: Path) -> list[QuoteRef]:
    """扫 wiki/quotes.md(整页都视为证据,因为这页本来就是引用集合)。"""
    refs: list[QuoteRef] = []
    quotes_file = wiki_dir / "quotes.md"
    if quotes_file.is_file():
        refs.extend(_extract_from_file(quotes_file, evidence_only=False))
    return refs


def _extract_from_file(md_file: Path, evidence_only: bool) -> list[QuoteRef]:
    """从单个文件提取引用条目。

    evidence_only=True:只扫 `## 证据` 段落,跳过「分析增量」「关联主题」等。
    evidence_only=False:整文件扫(quotes.md 用)。
    """
    refs: list[QuoteRef] = []
    try:
        text = md_file.read_text(encoding="utf-8")
    except Exception:
        return refs

    lines = text.split("\n")
    in_evidence = not evidence_only  # quotes.md 整页都进
    in_skip_section = False           # 「分析增量」栏要主动跳过

    for li, line in enumerate(lines, start=1):
        if evidence_only:
            if EVIDENCE_HEADER_RE.match(line):
                in_evidence = True
                in_skip_section = False
                continue
            if NEXT_HEADER_RE.match(line):
                # 遇到下一个 header → 退出证据栏
                in_evidence = False
                in_skip_section = False
                continue
            if not in_evidence:
                continue

        # 行内必须有 ref id + 引号
        id_match = REF_ID_RE.search(line)
        if not id_match:
            continue
        for pat in QUOTE_PATTERNS:
            for qm in pat.finditer(line):
                quote_text = qm.group(1).strip()
                # 过滤掉明显不是引用的:例如标签 ("行为/态度") / 类型注释
                if len(quote_text) < 2:
                    continue
                if quote_text in ("行为", "态度", "痛点", "积极", "高", "中", "低"):
                    continue
                refs.append(QuoteRef(
                    source_file=md_file,
                    source_line=li,
                    ref_id=id_match.group(1),
                    quote=quote_text,
                ))
    return refs


# ---------- 文本归一化 ----------

# 同一字符在 NFKC 下的折叠 + 标点归一(全角→半角)+ 空白合并
PUNCT_MAP = str.maketrans({
    "，": ",", "。": ".", "?": "?", "!": "!",
    "?": "?", "!": "!", ",": ",", ".": ".",
    "：": ":", ":": ":", "；": ";", ";": ";",
    "「": '"', "」": '"', "『": '"', "』": '"',
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "（": "(", "）": ")", "(": "(", ")": ")",
    "—": "-", "–": "-", "…": "...",
})
WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(PUNCT_MAP)
    text = WS_RE.sub("", text)  # 完全去空白(中文文本之间空格无意义)
    return text.lower()


# ---------- 子串匹配(支持省略号切片) ----------

ELLIPSIS_PATTERNS = ["...", "…"]


def find_quote_in_corpus(quote: str, corpus: str) -> tuple[bool, str]:
    """quote 是否在 corpus 中(归一化后子串)。

    支持省略号:把 quote 按 `...` / `…` 切片,每段必须按顺序在 corpus 出现。
    返回 (是否命中, 失败时未命中的片段)。
    """
    norm_quote = normalize(quote)
    norm_corpus = normalize(corpus)

    # 检查是否有省略号
    has_ellipsis = any(e in quote for e in ELLIPSIS_PATTERNS)
    if not has_ellipsis:
        if norm_quote in norm_corpus:
            return True, ""
        return False, norm_quote

    # 切片(归一化时省略号被替换成 "...")
    segments = [s for s in norm_quote.split("...") if s]
    if not segments:
        return True, ""

    pos = 0
    for seg in segments:
        idx = norm_corpus.find(seg, pos)
        if idx == -1:
            return False, seg
        pos = idx + len(seg)
    return True, ""


# ---------- 资料文件查找 ----------

def find_data_file(data_dir: Path, ref_id: str) -> Path | None:
    """找 data/<ref_id>.*。

    支持的扩展:.md .txt .csv .json
    支持的命名:精确 ref_id / 大小写不敏感
    """
    if not data_dir.is_dir():
        return None
    candidates = [
        data_dir / f"{ref_id}.md",
        data_dir / f"{ref_id}.txt",
        data_dir / f"{ref_id}.csv",
        data_dir / f"{ref_id}.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    # fallback: glob 容错(大小写或后缀变化)
    for f in data_dir.iterdir():
        if not f.is_file():
            continue
        name_no_ext = f.stem.lower()
        if name_no_ext == ref_id.lower():
            return f
    return None


# ---------- 主流程 ----------

def verify(wiki_dir: Path, data_dir: Path) -> tuple[list[VerifyResult], int]:
    refs = extract_quotes_from_themes(wiki_dir) + extract_quotes_from_quotes_page(wiki_dir)
    results: list[VerifyResult] = []

    # 资料文件内容缓存
    corpus_cache: dict[Path, str] = {}

    for ref in refs:
        data_path = find_data_file(data_dir, ref.ref_id)
        if data_path is None:
            results.append(VerifyResult(
                quote=ref, found=False, data_path=None,
                reason=f"找不到原始资料文件 data/{ref.ref_id}.* (尝试了 .md/.txt/.csv/.json)",
            ))
            continue
        if data_path not in corpus_cache:
            try:
                corpus_cache[data_path] = data_path.read_text(encoding="utf-8")
            except Exception as e:
                results.append(VerifyResult(
                    quote=ref, found=False, data_path=data_path,
                    reason=f"读取失败:{e}",
                ))
                continue
        corpus = corpus_cache[data_path]
        ok, missing = find_quote_in_corpus(ref.quote, corpus)
        if ok:
            results.append(VerifyResult(quote=ref, found=True, data_path=data_path, reason=""))
        else:
            results.append(VerifyResult(
                quote=ref, found=False, data_path=data_path,
                reason=f"原始资料中找不到子串:{missing[:40]}{'...' if len(missing) > 40 else ''}",
            ))
    return results, len(refs)


# ---------- 输出 ----------

def format_report(results: list[VerifyResult], total: int, wiki_dir: Path) -> str:
    failed = [r for r in results if not r.found]
    lines = [f"=== verify_quotes: {wiki_dir} ==="]
    if not failed:
        lines.append(f"PASS — 全部 {total} 条引用在原始资料中命中")
        return "\n".join(lines)
    lines.append(f"FAIL — {len(failed)} / {total} 条引用未命中")
    lines.append("")
    for r in failed:
        rel = r.quote.source_file.name
        lines.append(f"[#{r.quote.ref_id}] {rel}:L{r.quote.source_line}")
        lines.append(f"  引用: \"{r.quote.quote}\"")
        lines.append(f"  原因: {r.reason}")
        lines.append("")
    return "\n".join(lines)


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="wiki 引用真实性全量校验(反幻觉 H3)",
    )
    parser.add_argument("wiki_dir", help="wiki 目录路径(包含 themes/, quotes.md)")
    parser.add_argument("--data-dir", default=None, help="原始资料目录(默认 wiki_dir/../data)")
    parser.add_argument("--quiet", action="store_true", help="只返回 exit code")
    args = parser.parse_args(argv)

    wiki_dir = Path(args.wiki_dir)
    if not wiki_dir.is_dir():
        if not args.quiet:
            print(f"verify_quotes: wiki 目录不存在: {wiki_dir}", file=sys.stderr)
        return 2
    data_dir = Path(args.data_dir) if args.data_dir else wiki_dir.parent / "data"
    if not data_dir.is_dir():
        if not args.quiet:
            print(f"verify_quotes: data 目录不存在: {data_dir}", file=sys.stderr)
        return 2

    try:
        results, total = verify(wiki_dir, data_dir)
    except Exception as e:
        if not args.quiet:
            print(f"verify_quotes: 校验失败: {e}", file=sys.stderr)
        return 2

    failed = [r for r in results if not r.found]
    if not args.quiet:
        print(format_report(results, total, wiki_dir))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
