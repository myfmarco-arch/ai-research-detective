#!/usr/bin/env python3
"""
detective 中间产物 lint —— 反幻觉 H12(表面合规)。

方法选择和侦探动作 3a-3e 必须分写入 6 个独立文件,字段达到最低门槛。
LLM 不能糊在一个 detective_analysis.md 里写「已完成盲区扫描」。

强制结构:
| 文件                                | 最低字段                                        |
|-------------------------------------|-------------------------------------------------|
| process/0_method_selection.md        | 写出研究类型 / 选用工具 / 未选工具及理由,且至少包含 1 个工具编号 |
| process/3a_coding.md                | 至少 5 条 #interview_*/#survey_* 引用(非 wiki 模式) |
| process/3b_blind_spots.md           | 至少 3 条「低频高强度」或「沉默信号」          |
| process/3c_associations.md          | 至少 1 条 N×N 跨主题关联(「主题 A ↔ 主题 B」)  |
| process/3d_contradictions_audit.md  | 每个核心结论必须有反面证据或显式「已搜未找到」+ 至少 1 条替代解释 |
| process/3e_evidence_chains.md       | 每个结论列支持 / 反对计数                      |

wiki 模式(传 --wiki-mode)放宽 3a:wiki 已经是编码产物,3a 文件可不存在。

CLI:
    python lint_process.py <process_dir> [--wiki-mode] [--quiet]

Exit:
    0 = 通过
    1 = 至少一个文件缺失或字段不达标
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
    file: str
    detail: str
    hint: str


REF_ID_RE = re.compile(r"#(?:interview|survey|feedback)_[A-Za-z0-9_-]+")
THEME_LINK_RE = re.compile(r"[一-鿿A-Za-z0-9_]{2,}\s*[↔<>→\-]+\s*[一-鿿A-Za-z0-9_]{2,}")
COUNTER_EVIDENCE_KEYWORDS = ["反面证据", "反例", "反驳", "已搜未找到", "未找到反例", "无反例"]
ALT_EXPLANATION_KEYWORDS = ["替代解释", "替代假设", "另一种解释", "也可能是", "备选解释", "竞争性解释"]
TOOL_REF_RE = re.compile(r"工具\s*\d+")



def check_0_method_selection(process_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    f = process_dir / "0_method_selection.md"
    if not f.is_file():
        findings.append(Finding(
            rule_id="P_MISSING_0_METHOD",
            rule_name="缺 process/0_method_selection.md(方法选择)",
            file="0_method_selection.md",
            detail="文件不存在",
            hint="正式侦探分析前必须记录研究类型、选用工具、未选工具及理由,防止工具箱被口头声明但未实际使用。",
        ))
        return findings
    text = f.read_text(encoding="utf-8")
    required = ["研究类型", "选用工具", "未选工具", "理由"]
    missing = [item for item in required if item not in text]
    tools = TOOL_REF_RE.findall(text)
    if missing or not tools:
        detail = []
        if missing:
            detail.append("缺少字段:" + ",".join(missing))
        if not tools:
            detail.append("未找到工具编号(如 工具 1)")
        findings.append(Finding(
            rule_id="P_THIN_0_METHOD",
            rule_name="0_method_selection.md 方法选择过薄",
            file="0_method_selection.md",
            detail="; ".join(detail),
            hint="写出研究类型、选用工具、未选工具及理由,并至少列出 1 个工具编号。",
        ))
    return findings

def check_3a_coding(process_dir: Path, wiki_mode: bool) -> list[Finding]:
    findings: list[Finding] = []
    f = process_dir / "3a_coding.md"
    if not f.is_file():
        if wiki_mode:
            return []
        findings.append(Finding(
            rule_id="P_MISSING_3A",
            rule_name="缺 process/3a_coding.md(全量记忆编码)",
            file="3a_coding.md",
            detail="文件不存在",
            hint="非 wiki 模式必须有 process/3a_coding.md。每份资料的六类信息(关键观察/引用/行为vs态度/痛点/积极/上下文)分批写入。",
        ))
        return findings
    text = f.read_text(encoding="utf-8")
    refs = REF_ID_RE.findall(text)
    if len(refs) < 5:
        findings.append(Finding(
            rule_id="P_THIN_3A",
            rule_name=f"3a_coding.md 引用过少({len(refs)} 条 < 5)",
            file="3a_coding.md",
            detail=f"找到 {len(refs)} 条 #interview_* / #survey_* 引用",
            hint="3a 必须包含至少 5 条来源编号引用。如果资料量本来就 <5,显式说明「资料数 = 全部」,否则视为编码偷懒。",
        ))
    return findings


def check_3b_blind_spots(process_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    f = process_dir / "3b_blind_spots.md"
    if not f.is_file():
        findings.append(Finding(
            rule_id="P_MISSING_3B",
            rule_name="缺 process/3b_blind_spots.md(盲区扫描)",
            file="3b_blind_spots.md",
            detail="文件不存在",
            hint="侦探动作 3b 盲区扫描必须留产物。即使写「未发现盲区」也要给出搜了哪些角度。",
        ))
        return findings
    text = f.read_text(encoding="utf-8")
    bullets = [ln for ln in text.split("\n") if ln.lstrip().startswith(("- ", "* ", "1.", "2.", "3."))]
    keywords_hit = sum(1 for kw in ("低频高强度", "沉默信号", "未出现", "应出现", "缺失", "异常") if kw in text)
    if len(bullets) < 3 and keywords_hit < 3:
        findings.append(Finding(
            rule_id="P_THIN_3B",
            rule_name=f"3b 盲区条目不足(列表 {len(bullets)} 条,关键词 {keywords_hit} 个)",
            file="3b_blind_spots.md",
            detail="期望:至少 3 条「低频高强度」或「沉默信号」或「应出现但缺失」的盲区",
            hint="3b 至少列 3 条盲区(低频高强度 / 沉默信号 / 异常观察)。如果真的没找到任何盲区,显式写「搜了 X、Y、Z 三个角度,均未发现」并附搜索过程。",
        ))
    return findings


def check_3c_associations(process_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    f = process_dir / "3c_associations.md"
    if not f.is_file():
        findings.append(Finding(
            rule_id="P_MISSING_3C",
            rule_name="缺 process/3c_associations.md(全局关联)",
            file="3c_associations.md",
            detail="文件不存在",
            hint="侦探动作 3c 全局关联必须留产物。即使没发现关联也要写「做了 N×N 比对,未发现共变」。",
        ))
        return findings
    text = f.read_text(encoding="utf-8")
    has_pair = bool(THEME_LINK_RE.search(text)) or "共变" in text or "共现" in text or "关联" in text
    if not has_pair:
        findings.append(Finding(
            rule_id="P_THIN_3C",
            rule_name="3c 找不到 N×N 跨主题关联描述",
            file="3c_associations.md",
            detail="未找到「主题 A ↔ 主题 B」「共变」「共现」「关联」等关联表述",
            hint="3c 必须有具体的跨主题关联条目,例如「推送疲劳 ↔ 反复手动检查 / 同时出现率 5/8」。如果做了 N×N 比对未发现共变,显式说明「比对了 N 对主题,未发现统计意义共变」。",
        ))
    return findings


def check_3d_contradictions_audit(process_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    f = process_dir / "3d_contradictions_audit.md"
    if not f.is_file():
        findings.append(Finding(
            rule_id="P_MISSING_3D",
            rule_name="缺 process/3d_contradictions_audit.md(矛盾审计)",
            file="3d_contradictions_audit.md",
            detail="文件不存在",
            hint="侦探动作 3d 矛盾审计必须留产物。每个核心结论必须有反面证据或显式「已搜未找到」。",
        ))
        return findings
    text = f.read_text(encoding="utf-8")
    keywords_hit = [kw for kw in COUNTER_EVIDENCE_KEYWORDS if kw in text]
    if not keywords_hit:
        findings.append(Finding(
            rule_id="P_THIN_3D",
            rule_name="3d 找不到反面证据 / 反例标记",
            file="3d_contradictions_audit.md",
            detail="未找到「反面证据」「反例」「已搜未找到」等关键词",
            hint="3d 是矛盾审计,每个结论必须明确写出反面证据;如果搜过没找到,要写「已搜未找到」并说明搜了什么。光列结论不算审计。",
        ))
    alt_hit = [kw for kw in ALT_EXPLANATION_KEYWORDS if kw in text]
    if not alt_hit:
        findings.append(Finding(
            rule_id="P_NO_ALT_3D",
            rule_name="3d 缺竞争性解释 / 替代解释",
            file="3d_contradictions_audit.md",
            detail="未找到「替代解释」「替代假设」「也可能是」「竞争性解释」等关键词",
            hint="3d 矛盾审计要求每个核心结论至少列 1 条替代解释(避免过早收敛)。写法:「替代解释:也可能是 Y 导致,而非 X」。",
        ))
    return findings


def check_3e_evidence_chains(process_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    f = process_dir / "3e_evidence_chains.md"
    if not f.is_file():
        findings.append(Finding(
            rule_id="P_MISSING_3E",
            rule_name="缺 process/3e_evidence_chains.md(证据链)",
            file="3e_evidence_chains.md",
            detail="文件不存在",
            hint="侦探动作 3e 证据链必须留产物。每个结论列支持 / 反对证据计数 + 置信度。",
        ))
        return findings
    text = f.read_text(encoding="utf-8")
    has_support = "支持" in text
    has_oppose = ("反对" in text) or ("反例" in text) or ("反面" in text)
    has_count = bool(re.search(r"\d+\s*[条人位/份]", text)) or bool(re.search(r"\d+\s*/\s*\d+", text))
    if not (has_support and has_oppose and has_count):
        missing = []
        if not has_support:
            missing.append("「支持证据」")
        if not has_oppose:
            missing.append("「反对/反面证据」")
        if not has_count:
            missing.append("具体计数(N 条 / N 人 / N/M)")
        findings.append(Finding(
            rule_id="P_THIN_3E",
            rule_name=f"3e 缺{'、'.join(missing)}",
            file="3e_evidence_chains.md",
            detail=f"未找到的元素: {missing}",
            hint="3e 证据链必须给每个结论同时列「支持证据 X 条 / 反对证据 Y 条」,光说「证据充分」不算证据链。",
        ))
    return findings


def lint(process_dir: Path, wiki_mode: bool) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_0_method_selection(process_dir))
    findings.extend(check_3a_coding(process_dir, wiki_mode))
    findings.extend(check_3b_blind_spots(process_dir))
    findings.extend(check_3c_associations(process_dir))
    findings.extend(check_3d_contradictions_audit(process_dir))
    findings.extend(check_3e_evidence_chains(process_dir))
    return findings


def format_report(findings: list[Finding], process_dir: Path, wiki_mode: bool) -> str:
    out = [f"=== lint_process: {process_dir} (wiki_mode={wiki_mode}) ==="]
    if not findings:
        out.append("PASS — 5 个侦探动作产物齐备且达到最低字段要求")
        return "\n".join(out)
    out.append(f"FAIL — {len(findings)} 处问题")
    out.append("")
    for f in findings:
        out.append(f"[{f.rule_id} · {f.rule_name}]")
        out.append(f"  文件: {f.file}")
        out.append(f"  详情: {f.detail}")
        out.append(f"  改: {f.hint}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="detective 中间产物 lint")
    parser.add_argument("process_dir", help="process/ 目录路径")
    parser.add_argument("--wiki-mode", action="store_true",
                        help="wiki 模式(已用 archivist 入库,放宽 3a 文件)")
    parser.add_argument("--quiet", action="store_true", help="只返回 exit code")
    args = parser.parse_args(argv)

    process_dir = Path(args.process_dir)
    if not process_dir.is_dir():
        if not args.quiet:
            print(f"lint_process: 目录不存在: {process_dir}", file=sys.stderr)
        return 2

    try:
        findings = lint(process_dir, args.wiki_mode)
    except Exception as e:
        if not args.quiet:
            print(f"lint_process: 分析失败: {e}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(format_report(findings, process_dir, args.wiki_mode))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
