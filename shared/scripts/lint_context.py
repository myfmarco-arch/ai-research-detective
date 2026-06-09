#!/usr/bin/env python3
"""
CONTEXT.md 质量底线 lint —— 反幻觉 H10/H13(任务漂移 + 空话化)。

地基不稳,后面所有产出都歪。这个脚本把 CONTEXT.md 的最低质量做成机器可查。

红线(任一非零 → exit 1,必须修):
- R_PLACEHOLDER     仍带 `<!-- 待用户补充 -->` 标记
- R_EMPTY           速读卡必填字段空 / 我的身份空 / 研究问题核心问题空
- R_RESEARCH_Q_THIN 研究问题主体 < 20 字(填充式问题"了解用户"通不过)
- R_TEMPLATE_BLOCK  模板使用说明的 HTML 注释块没删

黄线(警告,不阻断):
- Y_VAGUE_VERB        研究问题以"了解 / 探索 / 调研 / 弄清"+ 名词收尾,缺可证伪子问题
- Y_FILLER_BOTTOMLINE 底线段落出现"请谨慎使用 / 注意保密 / 客观真实"等填充式套话

CLI:
    python lint_context.py <CONTEXT.md path> [--quiet] [--no-warn]

Exit:
    0 = 无红线
    1 = 至少一条红线
    2 = 文件不存在 / 读取失败
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    rule_id: str
    rule_name: str
    line: int
    excerpt: str
    hint: str
    severity: str = "red"


# ---------- 解析 ----------

HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PLACEHOLDER_RE = re.compile(r"<!--\s*待用户补充\s*-->")
TEMPLATE_BLOCK_RE = re.compile(r"模板使用说明.*?AI 读到此处时遵循", re.DOTALL)


@dataclass
class Section:
    title: str
    level: int
    start_line: int   # 1-based,header 行
    body_start: int   # body 第一行(可能为空)
    end_line: int     # 不包含,下一个同/上级 header 的行号或 EOF+1
    body: str         # 段落内容(不含 header 行)


def parse_sections(text: str) -> list[Section]:
    lines = text.split("\n")
    headers: list[tuple[int, int, str]] = []
    for li, line in enumerate(lines, start=1):
        m = HEADER_RE.match(line)
        if m:
            headers.append((li, len(m.group(1)), m.group(2).strip()))

    sections: list[Section] = []
    for i, (line_no, level, title) in enumerate(headers):
        # 找下一个同/上级 header
        end_line = len(lines) + 1
        for j in range(i + 1, len(headers)):
            if headers[j][1] <= level:
                end_line = headers[j][0]
                break
        body_lines = lines[line_no:end_line - 1]  # 不含 header 行
        sections.append(Section(
            title=title, level=level,
            start_line=line_no,
            body_start=line_no + 1,
            end_line=end_line,
            body="\n".join(body_lines),
        ))
    return sections


def find_section(sections: list[Section], title_substr: str, parent_substr: str | None = None) -> Section | None:
    """按标题子串查 section。parent_substr 限定上级 section(可选)。"""
    if parent_substr is None:
        for s in sections:
            if title_substr in s.title:
                return s
        return None
    # 找 parent 范围
    parent = find_section(sections, parent_substr)
    if parent is None:
        return None
    for s in sections:
        if title_substr in s.title and parent.start_line < s.start_line < parent.end_line:
            return s
    return None


# ---------- 速读卡解析 ----------

# 速读卡每条形如 `- **字段名**: 值` 或 `- **字段名**:`
SUMMARY_FIELD_RE = re.compile(r"^\s*-\s*\*\*([^*]+)\*\*\s*[:：]\s*(.*?)$")

# 速读卡必填字段(模板里有但允许扩展)
REQUIRED_SUMMARY_FIELDS = ["要回答", "汇报给", "产出形式", "产出位置", "底线"]


def parse_summary_card(section: Section) -> dict[str, tuple[int, str]]:
    """返回 {字段名: (line_1based, 值)}。"""
    result: dict[str, tuple[int, str]] = {}
    if section is None:
        return result
    for offset, line in enumerate(section.body.split("\n")):
        m = SUMMARY_FIELD_RE.match(line)
        if m:
            field, value = m.group(1).strip(), m.group(2).strip()
            line_no = section.body_start + offset
            result[field] = (line_no, value)
    return result


# ---------- 规则 ----------

def _build_template_block_mask(lines: list[str]) -> list[bool]:
    """只 mask 文档开头"模板使用说明"那段大注释块。

    占位符 `<!-- 待用户补充 -->` 本身就是 HTML 注释,不能因为它是注释就跳过。
    我们只跳过明显的模板说明大段(以「模板使用说明」开头的跨行注释)。
    """
    mask = [False] * len(lines)
    in_template_block = False
    for li, line in enumerate(lines):
        if not in_template_block:
            if "<!--" in line and "模板使用说明" in line:
                in_template_block = True
                mask[li] = True
                if "-->" in line:
                    in_template_block = False
                continue
        else:
            mask[li] = True
            if "-->" in line:
                in_template_block = False
    return mask


def rule_r_placeholder(text: str, lines: list[str]) -> list[Finding]:
    findings = []
    template_mask = _build_template_block_mask(lines)
    for li, line in enumerate(lines, start=1):
        if template_mask[li - 1]:
            continue
        if PLACEHOLDER_RE.search(line):
            findings.append(Finding(
                rule_id="R_PLACEHOLDER",
                rule_name="残留 <!-- 待用户补充 --> 占位",
                line=li,
                excerpt=line.strip()[:120],
                hint="占位符还在 → 用户没补完。回到 cold_start 让用户一次性补齐这些字段后再交付。",
            ))
    return findings


def rule_r_template_block(text: str, lines: list[str]) -> list[Finding]:
    if TEMPLATE_BLOCK_RE.search(text):
        # 找首次出现的行号
        for li, line in enumerate(lines, start=1):
            if "模板使用说明" in line:
                return [Finding(
                    rule_id="R_TEMPLATE_BLOCK",
                    rule_name="模板使用说明注释块未清理",
                    line=li,
                    excerpt=line.strip()[:120],
                    hint="模板顶部的「模板使用说明」HTML 注释块在 cold_start 写入最终 CONTEXT.md 时必须删除。",
                )]
    return []


def rule_r_empty(sections: list[Section]) -> list[Finding]:
    findings: list[Finding] = []

    # 1. 速读卡必填
    summary = find_section(sections, "速读卡")
    if summary is None:
        findings.append(Finding(
            rule_id="R_EMPTY",
            rule_name="缺「速读卡」section",
            line=1,
            excerpt="(整篇 CONTEXT 都没有 ## 速读卡)",
            hint="CONTEXT 必须有 `## 速读卡` 段落,包含要回答/汇报给/产出形式/产出位置/底线。",
        ))
    else:
        fields = parse_summary_card(summary)
        for required in REQUIRED_SUMMARY_FIELDS:
            if required not in fields:
                findings.append(Finding(
                    rule_id="R_EMPTY",
                    rule_name=f"速读卡缺字段「{required}」",
                    line=summary.start_line,
                    excerpt=f"## 速读卡 / 缺 - **{required}**: ...",
                    hint=f"速读卡缺 `- **{required}**: ...` 字段。补齐后再交付。",
                ))
            else:
                line_no, value = fields[required]
                if not value or PLACEHOLDER_RE.search(value):
                    findings.append(Finding(
                        rule_id="R_EMPTY",
                        rule_name=f"速读卡「{required}」字段为空",
                        line=line_no,
                        excerpt=f"- **{required}**: (空)",
                        hint=f"速读卡 `{required}` 字段必须非空。",
                    ))

    # 2. 我的身份
    identity = find_section(sections, "我的身份")
    if identity is None:
        findings.append(Finding(
            rule_id="R_EMPTY",
            rule_name="缺「我的身份」section",
            line=1,
            excerpt="(无 ## 我的身份)",
            hint="CONTEXT 必须有 `## 我的身份` 段落,声明 AI 在本项目里的专业训练 + 角色。",
        ))
    elif not identity.body.strip() or PLACEHOLDER_RE.search(identity.body):
        findings.append(Finding(
            rule_id="R_EMPTY",
            rule_name="「我的身份」段落为空",
            line=identity.start_line,
            excerpt=identity.body.strip()[:120] if identity.body.strip() else "(空段)",
            hint="「我的身份」必须实际描述专业视角(社会学家/产品研究员/语言学家等),空着等同放弃视角约束。",
        ))

    # 3. 研究问题 - 核心问题
    research_q = find_section(sections, "研究问题")
    if research_q is None:
        findings.append(Finding(
            rule_id="R_EMPTY",
            rule_name="缺「研究问题」section",
            line=1,
            excerpt="(无 ## 研究问题)",
            hint="CONTEXT 必须有 `## 研究问题` 段落,至少含核心问题。",
        ))
    else:
        body = research_q.body
        # 检查"核心问题"标识 + 后面有内容
        # 形态可能是 `**核心问题**\n\n实际内容` 或 `**核心问题**: 内容`
        core_q_match = re.search(r"\*\*核心问题\*\*\s*[:：]?\s*(.*?)(?=\*\*辅助问题\*\*|\Z)", body, re.DOTALL)
        if not core_q_match:
            findings.append(Finding(
                rule_id="R_EMPTY",
                rule_name="研究问题缺「核心问题」标记",
                line=research_q.start_line,
                excerpt=body.strip()[:120],
                hint="研究问题段必须有 `**核心问题**` 标记 + 实际内容。",
            ))
        else:
            core_text = core_q_match.group(1).strip()
            if not core_text or PLACEHOLDER_RE.search(core_text):
                findings.append(Finding(
                    rule_id="R_EMPTY",
                    rule_name="「核心问题」内容为空",
                    line=research_q.start_line,
                    excerpt="**核心问题** (空)",
                    hint="核心问题必须实际写出来。这是本次研究的目标,空着 = AI 没有靶子。",
                ))
    return findings


def rule_r_research_q_thin(sections: list[Section]) -> list[Finding]:
    """核心问题主体长度 < 20 字 → 填充式问题。"""
    research_q = find_section(sections, "研究问题")
    if research_q is None:
        return []
    body = research_q.body
    core_q_match = re.search(r"\*\*核心问题\*\*\s*[:：]?\s*(.*?)(?=\*\*辅助问题\*\*|\Z)", body, re.DOTALL)
    if not core_q_match:
        return []
    core_text = core_q_match.group(1).strip()
    # 去掉 markdown 占位 + 空行
    core_text_clean = re.sub(r"\s+", "", core_text)
    if not core_text_clean or PLACEHOLDER_RE.search(core_text):
        return []   # 空问题已被 R_EMPTY 抓
    if len(core_text_clean) < 20:
        return [Finding(
            rule_id="R_RESEARCH_Q_THIN",
            rule_name=f"核心问题过短({len(core_text_clean)} 字)",
            line=research_q.start_line,
            excerpt=core_text[:60],
            hint="核心问题 < 20 字 = 填充式问题(『了解用户需求』『探索 X』)。要写到能让 AI 知道靶子的具体程度,例如『独居女性使用智能音箱时,在哪些场景下会主动关闭语音助手?触发关闭的具体顾虑是什么?』",
        )]
    return []


VAGUE_VERB_PATTERNS = [
    re.compile(r"^[^,。.\n]{0,5}(了解|探索|调研|弄清|研究|分析)[^?,。.\n!?]{0,30}$"),
]


def rule_y_vague_verb(sections: list[Section]) -> list[Finding]:
    """核心问题以填充式动词收尾,无可证伪子问题。"""
    research_q = find_section(sections, "研究问题")
    if research_q is None:
        return []
    body = research_q.body
    core_q_match = re.search(r"\*\*核心问题\*\*\s*[:：]?\s*(.*?)(?=\*\*辅助问题\*\*|\Z)", body, re.DOTALL)
    if not core_q_match:
        return []
    core_text = core_q_match.group(1).strip()
    # 取主句(第一行非空)
    first_line = next((ln for ln in core_text.split("\n") if ln.strip()), "")
    first_line_clean = first_line.strip()
    if not first_line_clean:
        return []

    # 过短的已经被 R_RESEARCH_Q_THIN 抓
    if len(re.sub(r"\s+", "", first_line_clean)) < 20:
        return []

    # 检查"了解/探索/调研..." + 短名词,无问号、无具体子问题
    for pat in VAGUE_VERB_PATTERNS:
        if pat.search(first_line_clean):
            return [Finding(
                rule_id="Y_VAGUE_VERB",
                rule_name="核心问题用填充式动词,无可证伪子问题",
                line=research_q.start_line,
                excerpt=first_line_clean[:80],
                hint="『了解 / 探索 / 调研 X』+ 名词 = 没有可证伪靶子。改写成可被回答(yes/no)或可比较(A vs B)的具体问题。",
                severity="yellow",
            )]
    return []


FILLER_BOTTOMLINE_PHRASES = [
    "请谨慎使用",
    "注意保密",
    "客观真实",
    "科学严谨",
    "确保准确",
    "保持中立",
    "注意细节",
]


def rule_y_filler_bottomline(sections: list[Section]) -> list[Finding]:
    summary = find_section(sections, "速读卡")
    if summary is None:
        return []
    fields = parse_summary_card(summary)
    if "底线" not in fields:
        return []
    line_no, value = fields["底线"]
    if not value:
        return []
    findings = []
    for phrase in FILLER_BOTTOMLINE_PHRASES:
        if phrase in value:
            findings.append(Finding(
                rule_id="Y_FILLER_BOTTOMLINE",
                rule_name=f"底线含填充式套话「{phrase}」",
                line=line_no,
                excerpt=f"- **底线**: {value[:80]}",
                hint="底线要写「违反就重写」的具体红线(例如:不允许把单条访谈说成『用户都……』、不允许跨过样本边界外推),不是『请谨慎使用』『客观真实』这种通用套话(等同于没写)。",
                severity="yellow",
            ))
    return findings


# ---------- 主流程 ----------

ALL_RULES_RED = [
    rule_r_placeholder,
    rule_r_template_block,
]
ALL_RULES_RED_SECTIONED = [
    rule_r_empty,
    rule_r_research_q_thin,
]
ALL_RULES_YELLOW_SECTIONED = [
    rule_y_vague_verb,
    rule_y_filler_bottomline,
]


def lint(path: Path) -> tuple[list[Finding], list[Finding]]:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    sections = parse_sections(text)

    red, yellow = [], []
    for rule in ALL_RULES_RED:
        for f in rule(text, lines):
            (red if f.severity == "red" else yellow).append(f)
    for rule in ALL_RULES_RED_SECTIONED:
        for f in rule(sections):
            (red if f.severity == "red" else yellow).append(f)
    for rule in ALL_RULES_YELLOW_SECTIONED:
        for f in rule(sections):
            (red if f.severity == "red" else yellow).append(f)

    # 去重
    def dedupe(fs):
        seen = set()
        out = []
        for f in fs:
            key = (f.rule_id, f.line, f.rule_name)
            if key in seen:
                continue
            seen.add(key)
            out.append(f)
        return out

    red = dedupe(red)
    yellow = dedupe(yellow)
    red.sort(key=lambda f: (f.line, f.rule_id))
    yellow.sort(key=lambda f: (f.line, f.rule_id))
    return red, yellow


def format_report(path: Path, red: list[Finding], yellow: list[Finding], show_warn: bool) -> str:
    out = [f"=== lint_context: {path} ==="]
    if not red and (not yellow or not show_warn):
        out.append(f"PASS — 无红线" + ("" if not yellow else f"({len(yellow)} 处黄线已抑制)"))
    else:
        status = "FAIL" if red else "WARN"
        parts = [f"红线 {len(red)} 处"]
        if show_warn:
            parts.append(f"黄线 {len(yellow)} 处")
        out.append(f"{status} — {' / '.join(parts)}")
    out.append("")

    for f in red:
        out.append(f"[{f.rule_id} · {f.rule_name}] L{f.line}")
        out.append(f"  > {f.excerpt}")
        out.append(f"  改: {f.hint}")
        out.append("")

    if show_warn:
        for f in yellow:
            out.append(f"[{f.rule_id} · {f.rule_name} (warn)] L{f.line}")
            out.append(f"  > {f.excerpt}")
            out.append(f"  改: {f.hint}")
            out.append("")

    out.append(f"Exit {1 if red else 0}.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CONTEXT.md 质量底线 lint")
    parser.add_argument("path", help="CONTEXT.md 路径")
    parser.add_argument("--quiet", action="store_true", help="只返回 exit code")
    parser.add_argument("--no-warn", action="store_true", help="不显示黄线")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.is_file():
        if not args.quiet:
            print(f"lint_context: 文件不存在: {path}", file=sys.stderr)
        return 2

    try:
        red, yellow = lint(path)
    except Exception as e:
        if not args.quiet:
            print(f"lint_context: 分析失败: {e}", file=sys.stderr)
        return 2

    show_warn = not args.no_warn
    if not args.quiet:
        print(format_report(path, red, yellow, show_warn))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
