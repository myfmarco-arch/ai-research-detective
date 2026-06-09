#!/usr/bin/env python3
"""
review.md 结构 lint —— 反幻觉 H12(留足迹) + H6(证据强度自标自查)。

强制:
1. 每个核心结论必须有「**搜索记录**」段,confirmed 至少 3 轮 + 命中 2+ 个一手编号
2. weakened/challenged 结论必须有「**反面证据**」段且非空
3. review.md 整体必须包含「证据强度复核」表(detective 标 vs reviewer 重标 + 重标依据)

红线(任一非零 → exit 1):
- V_NO_SEARCH       某结论缺「**搜索记录**」段
- V_THIN_SEARCH     confirmed 结论搜索 < 3 轮 或 < 2 个 #interview_*/#survey_* 编号
- V_NO_COUNTER      weakened/challenged 缺「**反面证据**」段
- V_NO_RECHECK      整文档缺「证据强度复核」表
- V_RECHECK_THIN    复核表缺「重标依据」列或某行依据为空

CLI:
    python lint_review.py <review.md path> [--quiet]

Exit:
    0 = 通过
    1 = 至少一条红线
    2 = 路径错误
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


# ---------- 解析 ----------

# 结论块识别:## 结论 N: ... 或 ## 结论 N
CONCLUSION_HEADER_RE = re.compile(r"^##\s+结论\s*(\d+)\s*[:：]?\s*(.*?)\s*$")
JUDGMENT_RE = re.compile(r"\*\*判定\s*[:：]\s*(confirmed|weakened|challenged)\b", re.IGNORECASE)
SEARCH_HEADER_RE = re.compile(r"\*\*搜索记录")
COUNTER_HEADER_RE = re.compile(r"\*\*反面证据")
RECHECK_HEADER_RE = re.compile(r"##\s*证据强度复核")
SAMPLING_HEADER_RE = re.compile(r"##\s*采样一致性")
SAMPLING_MODE_RE = re.compile(r"\*\*核心结论筛选模式\*\*")
REF_ID_RE = re.compile(r"#(?:interview|survey|feedback)_[A-Za-z0-9_-]+")
ROUND_RE = re.compile(r"第\s*\d+\s*轮")


@dataclass
class ConclusionBlock:
    index: int
    title: str
    start_line: int      # 1-based,## 结论 N 行
    end_line: int        # 不含
    body: str            # 块内文本(不含 header)
    judgment: str | None  # confirmed/weakened/challenged


def parse_conclusions(text: str) -> list[ConclusionBlock]:
    lines = text.split("\n")
    headers: list[tuple[int, int, str]] = []  # (line_no, num, title)
    for li, line in enumerate(lines, start=1):
        m = CONCLUSION_HEADER_RE.match(line)
        if m:
            headers.append((li, int(m.group(1)), m.group(2).strip()))

    blocks: list[ConclusionBlock] = []
    for i, (line_no, num, title) in enumerate(headers):
        end_line = headers[i + 1][0] if i + 1 < len(headers) else len(lines) + 1
        # 但如果遇到下一个 ## 但不是「结论」(比如「证据强度复核」「附加发现」「交付检查」),也要终止
        for j in range(line_no, end_line - 1):
            if j < len(lines):
                later = lines[j]
                # 已经处理过 line_no 这一行(header)
                if later.startswith("## ") and not CONCLUSION_HEADER_RE.match(later):
                    # 不是结论 header,作为终止
                    end_line = j + 1
                    break
        body_lines = lines[line_no:end_line - 1]
        body = "\n".join(body_lines)

        jm = JUDGMENT_RE.search(body)
        judgment = jm.group(1).lower() if jm else None

        blocks.append(ConclusionBlock(
            index=num, title=title,
            start_line=line_no, end_line=end_line,
            body=body, judgment=judgment,
        ))
    return blocks


def find_recheck_table(text: str) -> tuple[bool, int, list[str]] | None:
    """找「证据强度复核」表。返回 (找到, 起始行, 表头单元格列表) 或 None。"""
    lines = text.split("\n")
    for li, line in enumerate(lines, start=1):
        if RECHECK_HEADER_RE.match(line):
            # 往后找第一个表格行(以 | 开头)
            for j in range(li, min(li + 20, len(lines))):
                row = lines[j]
                if row.strip().startswith("|") and "|" in row.strip()[1:]:
                    cells = [c.strip() for c in row.strip().strip("|").split("|")]
                    return True, j + 1, cells
            return True, li, []
    return None


def collect_recheck_rows(text: str) -> list[list[str]]:
    """收集「证据强度复核」表的数据行(跳过分隔行)。"""
    lines = text.split("\n")
    in_recheck = False
    rows: list[list[str]] = []
    after_separator = False
    for line in lines:
        if RECHECK_HEADER_RE.match(line):
            in_recheck = True
            continue
        if in_recheck:
            stripped = line.strip()
            if stripped.startswith("##") and not RECHECK_HEADER_RE.match(line):
                break
            if not stripped.startswith("|"):
                continue
            # 跳过分隔行 |---|---|
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                after_separator = True
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not after_separator:
                # 表头
                continue
            rows.append(cells)
    return rows


# ---------- 规则 ----------

def rule_v_no_search(blocks: list[ConclusionBlock]) -> list[Finding]:
    findings = []
    for b in blocks:
        if not SEARCH_HEADER_RE.search(b.body):
            findings.append(Finding(
                rule_id="V_NO_SEARCH",
                rule_name=f"结论 {b.index} 缺「**搜索记录**」段",
                line=b.start_line,
                excerpt=f"## 结论 {b.index}: {b.title[:40]}",
                hint="每个结论必须有 `**搜索记录**` 段,列出搜了哪里(grep / 读了什么文件)+ 命中的具体编号 + 原文摘录。这是反幻觉 H12「LLM 编造『搜了 3 轮』」的足迹。",
            ))
    return findings


def rule_v_thin_search(blocks: list[ConclusionBlock]) -> list[Finding]:
    findings = []
    for b in blocks:
        if b.judgment != "confirmed":
            continue
        # 取「搜索记录」段:从 **搜索记录 到下一个 ** 加粗段或下一个 ## header
        m = SEARCH_HEADER_RE.search(b.body)
        if not m:
            continue
        # 切出搜索记录段落
        rest = b.body[m.start():]
        # 终止于「**反面证据」「**未找到反面证据」「## 」「## 结论」
        end_match = re.search(r"(\*\*(?:反面证据|未找到反面证据|证据强度|判定)|^##\s)", rest[20:], re.MULTILINE)
        search_section = rest if not end_match else rest[:20 + end_match.start()]
        rounds = len(ROUND_RE.findall(search_section))
        ref_ids = len(set(REF_ID_RE.findall(search_section)))
        if rounds < 3 or ref_ids < 2:
            findings.append(Finding(
                rule_id="V_THIN_SEARCH",
                rule_name=f"结论 {b.index} (confirmed) 搜索深度不足(轮数 {rounds}, 命中编号 {ref_ids})",
                line=b.start_line,
                excerpt=f"结论 {b.index} 判定 confirmed,搜索记录只有 {rounds} 轮 / {ref_ids} 个一手编号",
                hint="confirmed = 主动搜了反面但没找到。门槛:至少 3 轮搜索 + 命中 2+ 个 #interview_* / #survey_* 编号。轮数标记用「第 1 轮 / 第 2 轮 / 第 3 轮」,命中编号要贴具体原文摘录。",
            ))
    return findings


def rule_v_no_counter(blocks: list[ConclusionBlock]) -> list[Finding]:
    findings = []
    for b in blocks:
        if b.judgment not in ("weakened", "challenged"):
            continue
        if not COUNTER_HEADER_RE.search(b.body):
            findings.append(Finding(
                rule_id="V_NO_COUNTER",
                rule_name=f"结论 {b.index} ({b.judgment}) 缺「**反面证据**」段",
                line=b.start_line,
                excerpt=f"## 结论 {b.index} 判定 {b.judgment}",
                hint=f"{b.judgment} 判定必须有 `**反面证据**` 段并贴具体引用 / 数据 + 来源编号。光下判定不算审查。",
            ))
            continue
        # 还要查段内有内容
        m = COUNTER_HEADER_RE.search(b.body)
        rest = b.body[m.end():]
        # 取这个段直到下一个 **xxx** 或 ## 或 EOF
        end_m = re.search(r"(\*\*[一-鿿\w]+|^##\s)", rest[5:], re.MULTILINE)
        section = rest if not end_m else rest[:5 + end_m.start()]
        section_clean = section.strip().lstrip(":：").strip()
        if len(section_clean) < 30:
            findings.append(Finding(
                rule_id="V_NO_COUNTER",
                rule_name=f"结论 {b.index} ({b.judgment}) 反面证据段空或过短",
                line=b.start_line,
                excerpt=f"反面证据段不足 30 字: {section_clean[:50]}",
                hint=f"{b.judgment} 判定的反面证据段不能空。要写「具体引用 / 数据,标注来源编号」+ 「与结论矛盾,因为...」。",
            ))
    return findings


def rule_v_no_recheck(text: str) -> list[Finding]:
    found = find_recheck_table(text)
    if found is None:
        return [Finding(
            rule_id="V_NO_RECHECK",
            rule_name="缺「证据强度复核」表",
            line=1,
            excerpt="(无 ## 证据强度复核 段落)",
            hint="reviewer 必须独立从 wiki 重新评估每个结论的证据强度,并给出对照表。这是反幻觉 H6「detective 自标 reviewer 自查」——同人评同人。表头至少含: 结论 / detective 标 / reviewer 重标 / 重标依据 / 差异原因。",
        )]
    return []


def rule_v_recheck_thin(text: str) -> list[Finding]:
    findings = []
    found = find_recheck_table(text)
    if found is None:
        return []  # V_NO_RECHECK 已抓
    _, header_line, header_cells = found
    if not header_cells:
        return [Finding(
            rule_id="V_RECHECK_THIN",
            rule_name="证据强度复核表无表头",
            line=header_line,
            excerpt="(找不到表头单元格)",
            hint="复核表必须有标准表头: 结论 / detective 标 / reviewer 重标 / 重标依据 / 差异原因。",
        )]
    # 检查必须列
    required = ["重标依据"]
    header_normalized = [h.lower().replace(" ", "") for h in header_cells]
    for req in required:
        req_norm = req.lower().replace(" ", "")
        if not any(req_norm in h for h in header_normalized):
            findings.append(Finding(
                rule_id="V_RECHECK_THIN",
                rule_name=f"复核表缺「{req}」列",
                line=header_line,
                excerpt=" | ".join(header_cells),
                hint=f"复核表必须有「{req}」列(reviewer 给出独立判定的依据,例如「严格只算主动展开论述的访谈,4/22」)。光列重标等级 = 二次自标,达不到反幻觉 H6 的目的。",
            ))

    # 检查行内容:重标依据列不能空
    rows = collect_recheck_rows(text)
    for row_idx, row in enumerate(rows, start=1):
        if len(row) != len(header_cells):
            continue
        for h, c in zip(header_cells, row):
            if "依据" in h and not c.strip():
                findings.append(Finding(
                    rule_id="V_RECHECK_THIN",
                    rule_name=f"复核表第 {row_idx} 行「{h}」为空",
                    line=header_line,
                    excerpt=" | ".join(row),
                    hint="重标依据不能空。每行都要写出 reviewer 独立判定的具体依据(数字 / 来源 / 边界条件),否则等同自标。",
                ))
    return findings


# ---------- 主流程 ----------

def rule_v_no_sampling_mode(text: str) -> list[Finding]:
    """检查筛选模式声明 + 采样一致性表(任一缺失即 fail,multi-agent 模式特别约束)。

    规则:头部必须有「**核心结论筛选模式**: ...」声明
    - 声明含 "multi-agent" 或 "采样" → 必须有 ## 采样一致性 表
    - 声明含 "降级" / "单 LLM" / "快速审" → 采样表可省略
    - 声明完全缺失 → fail(不知道用哪种模式 = 留给作弊空间)
    """
    findings: list[Finding] = []
    if not SAMPLING_MODE_RE.search(text):
        findings.append(Finding(
            rule_id="V_NO_SAMPLING_MODE",
            rule_name="缺「核心结论筛选模式」声明",
            line=1,
            excerpt="(头部找不到 **核心结论筛选模式**: ...)",
            hint="review.md 头部必须显式声明筛选模式: `**核心结论筛选模式**: multi-agent 采样取交集 / 降级单 LLM(原因:...)/ 快速审`。这是反幻觉 H1 的足迹——LLM 不能默默跳过 multi-agent 走单 LLM 而不告知。",
        ))
        return findings

    # 找到声明,看是哪种模式
    m = re.search(r"\*\*核心结论筛选模式\*\*\s*[:：]\s*(.*)", text)
    if not m:
        return findings
    mode_line = m.group(1).strip().lower()
    is_multi_agent = ("multi-agent" in mode_line) or ("采样" in mode_line)
    is_degraded = ("降级" in mode_line) or ("单 llm" in mode_line) or ("单llm" in mode_line) or ("快速审" in mode_line)

    if is_multi_agent and not is_degraded:
        # multi-agent 模式必须有采样一致性表
        if not SAMPLING_HEADER_RE.search(text):
            findings.append(Finding(
                rule_id="V_NO_SAMPLING_TABLE",
                rule_name="multi-agent 模式缺「采样一致性」表",
                line=1,
                excerpt="(声明 multi-agent 但找不到 ## 采样一致性)",
                hint="multi-agent 模式必须有 `## 采样一致性` 表,列出每个候选结论在 3 次独立 subagent 中的出现次数(3/3 / 2/3 / 1/3)+ 判定。这是 H1 防御的足迹。",
            ))
    return findings


def lint(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    blocks = parse_conclusions(text)
    findings: list[Finding] = []
    findings.extend(rule_v_no_search(blocks))
    findings.extend(rule_v_thin_search(blocks))
    findings.extend(rule_v_no_counter(blocks))
    findings.extend(rule_v_no_recheck(text))
    findings.extend(rule_v_recheck_thin(text))
    findings.extend(rule_v_no_sampling_mode(text))
    findings.sort(key=lambda f: (f.line, f.rule_id))
    return findings


def format_report(findings: list[Finding], path: Path) -> str:
    out = [f"=== lint_review: {path} ==="]
    if not findings:
        out.append("PASS — 搜索记录、反面证据、证据强度复核表齐备")
        return "\n".join(out)
    out.append(f"FAIL — {len(findings)} 处问题")
    out.append("")
    for f in findings:
        out.append(f"[{f.rule_id} · {f.rule_name}] L{f.line}")
        out.append(f"  > {f.excerpt}")
        out.append(f"  改: {f.hint}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="review.md 结构 lint")
    parser.add_argument("path", help="review.md 路径")
    parser.add_argument("--quiet", action="store_true", help="只返回 exit code")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.is_file():
        if not args.quiet:
            print(f"lint_review: 文件不存在: {path}", file=sys.stderr)
        return 2

    try:
        findings = lint(path)
    except Exception as e:
        if not args.quiet:
            print(f"lint_review: 分析失败: {e}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(format_report(findings, path))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
