#!/usr/bin/env python3
"""
AI 接力包（information_pack_*.md）lint —— 三类机器可查规则。

对照 contracts/information_pack.md §3 / §7 的红线条款实现:
1. 清理类:无 HTML 注释、无 {{...}} 占位符、frontmatter 必填字段已填
2. 跨 ID 完整性:F-/Q-/D-/L-/M-/G-/P-/CON-/S-/C-/U- 引用的目标 ID 在对应章节真实存在
3. 结构类:§0 协议保留、§1.2 负面清单非空、§4.1/4.2 至少各 1 条、§7 至少 1 条

CLI:
    python scripts/lint_information_pack.py <path> [--format=text|md] [--quiet]

Exit:
    0 = 无红线
    1 = 至少一条红线
    2 = 文件不存在 / 读取失败 / 参数错误 / frontmatter 解析失败
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------- 数据结构 ----------

@dataclass
class Finding:
    rule_id: str
    rule_name: str
    line: int               # 1-based;0 表示文件级
    detail: str             # 具体描述,含命中的 ID 或字段名
    hint: str               # 修复指引


@dataclass
class Pack:
    raw: str
    lines: list[str]
    frontmatter: dict       # 解析后的 frontmatter(浅层 dict,值可能是 dict/str/None)
    body: str               # frontmatter 之后的正文
    body_offset: int        # 正文在原文件中的起始行号(1-based)


# ---------- 加载与 frontmatter 解析 ----------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_pack(path: Path) -> Pack:
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        print(
            f"[ERROR] 文件 {path} 没有合法的 YAML frontmatter(必须以 --- 开头并以 --- 结束)",
            file=sys.stderr,
        )
        sys.exit(2)

    fm_text = m.group(1)
    fm = parse_simple_yaml(fm_text)
    body = raw[m.end():]
    body_offset = raw[: m.end()].count("\n") + 1
    return Pack(raw=raw, lines=lines, frontmatter=fm, body=body, body_offset=body_offset)


def parse_simple_yaml(text: str) -> dict:
    """
    极简 YAML 解析:只支持 key: value 和一级缩进的嵌套 map。
    够 AI 接力包 frontmatter 用,不引入第三方依赖。
    """
    result: dict = {}
    current_key: str | None = None
    for raw_line in text.split("\n"):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("  ") or raw_line.startswith("\t"):
            if current_key is None:
                continue
            stripped = raw_line.strip()
            if ":" in stripped:
                k, _, v = stripped.partition(":")
                if not isinstance(result.get(current_key), dict):
                    result[current_key] = {}
                result[current_key][k.strip()] = strip_quotes(v.strip())
        else:
            if ":" in raw_line:
                k, _, v = raw_line.partition(":")
                k = k.strip()
                v = v.strip()
                current_key = k
                if v == "":
                    result[k] = {}
                else:
                    result[k] = strip_quotes(v)
    return result


def strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


# ---------- 规则 1:清理类 ----------

PLACEHOLDER_RE = re.compile(r"\{\{[^}]*\}\}")
HTML_COMMENT_OPEN_RE = re.compile(r"<!--")
FENCE_RE = re.compile(r"^(\s*)(```|~~~)")

REQUIRED_FRONTMATTER_FIELDS = [
    "schema_version",
    "type",
    "research_question",
    "research_question_slug",
    "generated_at",
    "specialization",
    "valid_until",
    "status",
]
NULLABLE_NESTED = {
    "generated_from": ["full_report", "a1_summary", "a2_evidence_chain", "wiki_revision"],
}


def check_cleanup(pack: Pack) -> list[Finding]:
    out: list[Finding] = []

    # HTML 注释:全文(含 frontmatter)不允许出现
    for i, line in enumerate(pack.lines, start=1):
        if HTML_COMMENT_OPEN_RE.search(line):
            out.append(Finding(
                rule_id="C1",
                rule_name="残留 HTML 注释",
                line=i,
                detail=f"行 {i} 含 `<!--`",
                hint="模板里的注释是给 detective 的指引,生成最终 AI 接力包时必须全部删除",
            ))

    # 占位符 {{...}}:全文不允许出现
    for i, line in enumerate(pack.lines, start=1):
        for m in PLACEHOLDER_RE.finditer(line):
            out.append(Finding(
                rule_id="C2",
                rule_name="残留占位符",
                line=i,
                detail=f"行 {i} 含 `{m.group(0)}`",
                hint="替换为具体值;无内容写'未提供'(正文)或 null(frontmatter)",
            ))

    # frontmatter 顶层必填字段
    fm = pack.frontmatter
    for field_name in REQUIRED_FRONTMATTER_FIELDS:
        if field_name not in fm or fm[field_name] in ("", None):
            out.append(Finding(
                rule_id="C3",
                rule_name="frontmatter 必填字段缺失",
                line=0,
                detail=f"frontmatter 缺少 `{field_name}`",
                hint="在 frontmatter 里补齐该字段",
            ))

    # specialization 必须是合法值
    spec = fm.get("specialization")
    if spec and spec not in ("general", "prd", "design", "strategy"):
        out.append(Finding(
            rule_id="C4",
            rule_name="specialization 取值非法",
            line=0,
            detail=f"specialization=`{spec}`",
            hint="只能是 general / prd / design / strategy 之一",
        ))

    # generated_from 嵌套字段:可以为 null,但不能缺失键
    gf = fm.get("generated_from", {})
    if not isinstance(gf, dict):
        out.append(Finding(
            rule_id="C5",
            rule_name="generated_from 不是嵌套结构",
            line=0,
            detail="generated_from 应该是 map",
            hint="frontmatter 里 generated_from: 后跟换行 + 缩进的子键",
        ))
    else:
        for key in NULLABLE_NESTED["generated_from"]:
            if key not in gf:
                out.append(Finding(
                    rule_id="C6",
                    rule_name="generated_from 子键缺失",
                    line=0,
                    detail=f"generated_from.{key} 未出现",
                    hint=f"补 {key}: null 或具体路径",
                ))

    return out


# ---------- 规则 2:跨 ID 完整性 ----------

# ID 语法:大写字母前缀 + 短横 + 数字。CON 是三字母前缀。
ID_DEFINITION_RE = re.compile(r"\[([A-Z]+)-(\d+)\]")
ID_REFERENCE_RE = re.compile(r"(?<![A-Z\[])([A-Z]+)-(\d+)(?![\d:])")
# 注:不匹配定义本身([X-N]),只匹配引用形式 X-N

VALID_PREFIXES = {"Q", "D", "L", "M", "G", "P", "CON", "S", "F", "C", "U"}


def collect_ids(text: str) -> tuple[set[str], dict[str, int]]:
    """
    收集所有定义的 ID(用 [X-N] 形式)和引用的 ID(裸 X-N)。
    返回:(defined_ids, referenced_with_first_line)
    """
    defined: set[str] = set()
    refs_first_line: dict[str, int] = {}

    for line_num, line in enumerate(text.split("\n"), start=1):
        for m in ID_DEFINITION_RE.finditer(line):
            prefix, num = m.group(1), m.group(2)
            if prefix in VALID_PREFIXES:
                defined.add(f"{prefix}-{num}")

    # 表格里的定义可能不带 []:扫表格行,行首格的 [X-N] 已被上面捕获,
    # 但表格里 |F-1| 这种形式没有方括号——补一遍:取表格首列里形如 X-N 的也算定义
    for line in text.split("\n"):
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells:
                first = cells[0]
                m = re.fullmatch(r"([A-Z]+)-(\d+)", first)
                if m and m.group(1) in VALID_PREFIXES:
                    defined.add(first)

    # 引用扫描(全文,不区分定义和引用上下文)
    for line_num, line in enumerate(text.split("\n"), start=1):
        # 跳过表头分隔行
        if re.fullmatch(r"\|?\s*[-:|\s]+\|?", line):
            continue
        for m in ID_REFERENCE_RE.finditer(line):
            prefix, num = m.group(1), m.group(2)
            if prefix not in VALID_PREFIXES:
                continue
            ref_id = f"{prefix}-{num}"
            refs_first_line.setdefault(ref_id, line_num)

    return defined, refs_first_line


def check_id_integrity(pack: Pack) -> list[Finding]:
    out: list[Finding] = []
    defined, refs = collect_ids(pack.body)

    # 引用必须有定义(自引用算定义,collect_ids 已合并)
    for ref_id, line_num in sorted(refs.items()):
        if ref_id not in defined:
            absolute_line = pack.body_offset + line_num - 1
            out.append(Finding(
                rule_id="I1",
                rule_name="引用了未定义的 ID",
                line=absolute_line,
                detail=f"`{ref_id}` 在文档中没有对应的 [{ref_id}] 定义",
                hint=f"在对应章节定义 {ref_id},或修正引用",
            ))

    return out


# ---------- 规则 3:结构类 ----------

REQUIRED_SECTIONS = [
    ("0. AI 操作协议", r"##\s*0\.\s*AI\s*操作协议"),
    ("1.2 负面清单", r"###\s*1\.2"),
    ("4.1 用户分群", r"###\s*4\.1"),
    ("4.2 痛点合并清单", r"###\s*4\.2"),
    ("4.3 设计约束", r"###\s*4\.3"),
    ("7. 未解决的问题", r"##\s*7\.\s*未解决"),
]


def check_structure(pack: Pack) -> list[Finding]:
    out: list[Finding] = []
    body = pack.body

    # 检查必须章节存在
    for name, pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, body):
            out.append(Finding(
                rule_id="S1",
                rule_name="缺少必填章节",
                line=0,
                detail=f"未找到章节 `{name}`",
                hint=f"对照模板补齐 {name} 章节",
            ))

    # §1.2 负面清单非空(至少 1 条 "不能" 开头的列表项)
    sec_neg = extract_section(body, r"###\s*1\.2", r"###\s*1\.3|##\s*\d+\.")
    if sec_neg is not None:
        items = [
            ln for ln in sec_neg.split("\n")
            if ln.strip().startswith("- 不能")
        ]
        if not items:
            out.append(Finding(
                rule_id="S2",
                rule_name="§1.2 负面清单为空",
                line=0,
                detail="§1.2 没有任何 `- 不能...` 条目",
                hint="负面清单是给下游 AI 的护栏,必须列 3-5 条具体的'不能用于'",
            ))

    # §4.1 至少 1 个 G-N 定义
    sec_g = extract_section(body, r"###\s*4\.1", r"###\s*4\.2|##\s*\d+\.")
    if sec_g is not None:
        if not re.search(r"\bG-\d+\b", sec_g):
            out.append(Finding(
                rule_id="S3",
                rule_name="§4.1 用户分群为空",
                line=0,
                detail="§4.1 没有定义任何 G-N",
                hint="至少定义 1 个用户分群",
            ))

    # §4.2 至少 1 个 P-N 定义
    sec_p = extract_section(body, r"###\s*4\.2", r"###\s*4\.3|##\s*\d+\.")
    if sec_p is not None:
        if not re.search(r"\bP-\d+\b", sec_p):
            out.append(Finding(
                rule_id="S4",
                rule_name="§4.2 痛点清单为空",
                line=0,
                detail="§4.2 没有定义任何 P-N",
                hint="至少定义 1 个痛点",
            ))

    # §7 至少 1 个 U-N 定义
    sec_u = extract_section(body, r"##\s*7\.\s*未解决", r"##\s*8\.|^---")
    if sec_u is not None:
        if not re.search(r"U-\d+", sec_u):
            out.append(Finding(
                rule_id="S5",
                rule_name="§7 未解决问题为空",
                line=0,
                detail="§7 没有定义任何 U-N",
                hint="即便研究覆盖很全也要列至少 1 条 U-N(可写'目前未识别新的开放问题');不允许整节空",
            ))

    return out


def extract_section(body: str, start_pat: str, end_pat: str) -> str | None:
    start = re.search(start_pat, body)
    if not start:
        return None
    rest = body[start.end():]
    end = re.search(end_pat, rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


# ---------- 报告 ----------

def render_text(findings: list[Finding], path: Path) -> str:
    if not findings:
        return f"[OK] {path}: lint 通过(0 红线)"
    lines = [f"[FAIL] {path}: {len(findings)} 条红线"]
    for f in findings:
        loc = f"行 {f.line}" if f.line > 0 else "文件级"
        lines.append(f"  [{f.rule_id}] {f.rule_name} ({loc})")
        lines.append(f"      详情: {f.detail}")
        lines.append(f"      修复: {f.hint}")
    return "\n".join(lines)


def render_md(findings: list[Finding], path: Path) -> str:
    if not findings:
        return f"## AI 接力包 lint: {path.name}\n\n通过(0 红线)。\n"
    lines = [f"## AI 接力包 lint: {path.name}", "", f"**红线 {len(findings)} 条**", ""]
    lines.append("| 规则 | 名称 | 位置 | 详情 | 修复 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for f in findings:
        loc = f"行 {f.line}" if f.line > 0 else "文件级"
        lines.append(f"| {f.rule_id} | {f.rule_name} | {loc} | {f.detail} | {f.hint} |")
    return "\n".join(lines) + "\n"


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="lint AI 接力包（清理 / 跨 ID 完整性 / 结构）",
    )
    parser.add_argument("path", type=str, help="information_pack_*.md 路径")
    parser.add_argument(
        "--format",
        choices=("text", "md"),
        default="text",
        help="输出格式",
    )
    parser.add_argument("--quiet", action="store_true", help="只输出 exit code")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"[ERROR] 文件不存在: {path}", file=sys.stderr)
        return 2

    try:
        pack = load_pack(path)
    except Exception as e:
        print(f"[ERROR] 读取失败: {e}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    findings.extend(check_cleanup(pack))
    findings.extend(check_id_integrity(pack))
    findings.extend(check_structure(pack))

    findings.sort(key=lambda f: (f.line if f.line > 0 else 0, f.rule_id))

    if not args.quiet:
        if args.format == "md":
            print(render_md(findings, path))
        else:
            print(render_text(findings, path))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
