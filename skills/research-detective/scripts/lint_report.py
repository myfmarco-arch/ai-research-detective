#!/usr/bin/env python3
"""
研究报告写作风格 lint —— 机器可识别的红线/黄线检查。

覆盖 skills/research-detective/guides/writing_style.md 中可正则化的部分。
论证层（建议是否悬空、标题是否 finding statement、稻草人否定）需要语义判断，
不在本工具范围，仍由 research-reviewer + 人审兜底。

CLI:
    python scripts/lint_report.py <path> [--format=text|md] [--quiet] [--no-warn]

Exit:
    0 = 无红线（黄线不影响）
    1 = 至少一条红线
    2 = 文件不存在 / 读取失败 / 参数错误
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
    rule_id: str           # 语义短名：R_VOCAB / R_HEDGE_BUFFER / Y_BOLD / Y_TITLE 等
    rule_name: str
    line: int              # 1-based
    matched: str           # 命中的具体串
    excerpt: str           # ±20 字上下文
    hint: str              # 改写指引
    severity: str = "red"  # "red" | "yellow"


@dataclass
class Doc:
    """文档预处理结果。"""
    raw: str                                # 原始文本
    lines: list[str]                        # split by \n
    skip_mask: list[bool] = field(default_factory=list)  # per-line: True = 跳过
    paragraphs: list[tuple[int, str]] = field(default_factory=list)
    # paragraphs: list of (start_line_1based, paragraph_text)
    headers: list[tuple[int, int, str]] = field(default_factory=list)
    # headers: list of (line_1based, level, title_text)


# ---------- Markdown 预处理：识别跳过区间 ----------

FENCE_RE = re.compile(r"^(\s*)(```|~~~)")
COMMENT_OPEN = "<!--"
COMMENT_CLOSE = "-->"


def preprocess(raw: str) -> Doc:
    lines = raw.split("\n")
    n = len(lines)
    skip = [False] * n

    # 1) front matter: 文档开头第一行是 --- 时，找下一行 ---
    i = 0
    if n > 0 and lines[0].strip() == "---":
        skip[0] = True
        i = 1
        while i < n:
            skip[i] = True
            if lines[i].strip() == "---":
                i += 1
                break
            i += 1

    # 2) 代码块: ``` 或 ~~~ 配对（保留 indent 容忍）
    in_fence = False
    fence_marker = None
    while i < n:
        m = FENCE_RE.match(lines[i])
        if m:
            marker = m.group(2)
            if not in_fence:
                in_fence = True
                fence_marker = marker
                skip[i] = True
            elif marker == fence_marker:
                in_fence = False
                fence_marker = None
                skip[i] = True
            else:
                skip[i] = True
        elif in_fence:
            skip[i] = True
        i += 1

    # 3) HTML 注释 <!-- ... -->（可跨行）
    in_comment = False
    for li, line in enumerate(lines):
        if skip[li]:
            continue
        cur = line
        pos = 0
        while pos < len(cur):
            if not in_comment:
                idx = cur.find(COMMENT_OPEN, pos)
                if idx == -1:
                    break
                in_comment = True
                # 标记从注释开始到行尾
                if idx == 0 and not cur.strip().endswith(COMMENT_CLOSE) and cur.find(COMMENT_CLOSE, idx) == -1:
                    skip[li] = True
                pos = idx + len(COMMENT_OPEN)
                # 看本行内是否闭合
                close = cur.find(COMMENT_CLOSE, pos)
                if close != -1:
                    in_comment = False
                    # 同行开+闭：把整行的注释段视为 skip 内容（但保留非注释部分匹配会漏，
                    # 简化：整行跳过更安全，研究报告极少在一行中混注释和正文）
                    skip[li] = True
                    pos = close + len(COMMENT_CLOSE)
                else:
                    skip[li] = True
                    break
            else:
                close = cur.find(COMMENT_CLOSE, pos)
                if close == -1:
                    skip[li] = True
                    break
                else:
                    in_comment = False
                    skip[li] = True
                    pos = close + len(COMMENT_CLOSE)

    # 4) Mustache 占位 {{...}}：把内部内容替换成等长空格，让规则匹配不到
    #    （不是整行跳过，因为占位符可能与正文混在同一行）
    MUSTACHE_RE = re.compile(r"\{\{[^{}]*\}\}")
    for li, line in enumerate(lines):
        if skip[li]:
            continue
        new_line = line
        changed = False
        while True:
            m = MUSTACHE_RE.search(new_line)
            if not m:
                break
            new_line = new_line[:m.start()] + (" " * (m.end() - m.start())) + new_line[m.end():]
            changed = True
        if changed:
            lines[li] = new_line

    doc = Doc(raw=raw, lines=lines, skip_mask=skip)

    # 5) 解析段落（连续非空 + 非 skip 行 = 一段）
    cur_start = None
    cur_buf: list[str] = []
    for li, line in enumerate(lines):
        if skip[li] or not line.strip():
            if cur_buf:
                doc.paragraphs.append((cur_start + 1, "\n".join(cur_buf)))
                cur_buf = []
                cur_start = None
        else:
            if cur_start is None:
                cur_start = li
            cur_buf.append(line)
    if cur_buf:
        doc.paragraphs.append((cur_start + 1, "\n".join(cur_buf)))

    # 6) 解析 headers
    header_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    for li, line in enumerate(lines):
        if skip[li]:
            continue
        m = header_re.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            doc.headers.append((li + 1, level, title))

    return doc


# ---------- 工具函数 ----------

def excerpt_for(doc: Doc, line_idx_1based: int, match_start: int, match_len: int, ctx: int = 20) -> str:
    line = doc.lines[line_idx_1based - 1]
    start = max(0, match_start - ctx)
    end = min(len(line), match_start + match_len + ctx)
    s = line[start:end]
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(line) else ""
    return f"{prefix}{s}{suffix}"


def is_skipped(doc: Doc, line_idx_1based: int) -> bool:
    return doc.skip_mask[line_idx_1based - 1]


# ---------- 红线规则 ----------

# ===== 词法层（黑名单可查） =====

# R_VOCAB 概念癌词组：禁词表（substring 子串匹配）
R_VOCAB_BANNED_SUBSTRS = [
    # "结构性 X" / "X 悖论" 等：用前后缀匹配
    "结构性",
    "悖论",
    "赋能",
    "重构",
    "跃迁",
    "的本质",
    "的深层",
    "的底层",
    # AI 抒情动词（参考 humanizer #7 AI vocabulary，对应中文 underscore/showcase/tapestry 一类）
    # 在研究报告里出现 = 用文学修辞包装"我有判断"，与禁词同性质
    "彰显",
    "铸就",
    "谱写",
    "织就",
    "勾勒出",
]


def rule_r_vocab(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for word in R_VOCAB_BANNED_SUBSTRS:
            start = 0
            while True:
                idx = line.find(word, start)
                if idx == -1:
                    break
                # "结构性" 误判过滤：是否后接非汉字（如英文/标点）→ 大概率不是概念癌
                # 大部分概念癌后接 1-3 个汉字，做轻校验
                after = line[idx + len(word): idx + len(word) + 1]
                if word == "结构性" and after and not ('一' <= after <= '鿿'):
                    start = idx + len(word)
                    continue
                findings.append(Finding(
                    rule_id="R_VOCAB",
                    rule_name="概念癌词组",
                    line=li,
                    matched=word,
                    excerpt=excerpt_for(doc, li, idx, len(word)),
                    hint="概念癌词组：用大词包装『我有判断』。改成具体场景描述（参考 writing_style.md 替代方案表）",
                ))
                start = idx + len(word)
    return findings


# R_ABSTRACT 抽象偏正结构（"被理解的 X" / "X 的隐形 Y" / "X 的双重 Y"）
# 与 R_VOCAB 拆开：R_VOCAB 是黑名单词法，R_ABSTRACT 是正则句法
# 注意："被理解的"是抽象偏正，但"被问到的""被忽略的"是普通被动语态——
# 通过黑名单常见动词来过滤误报。
R_ABSTRACT_PASSIVE_VERB_BLACKLIST = {
    "问", "问到", "看到", "看见", "听到", "听见", "提到", "提及",
    "忽略", "忽视", "记住", "记录", "标记", "选择", "选中", "选定",
    "调研", "调查", "采访", "访谈", "测试", "邀请", "推荐",
    "发现", "证实", "证明", "排除", "纳入", "排查", "检测", "捕捉",
    "标注", "归类", "归入", "分到", "派到",
}
R_ABSTRACT_PATTERNS = [
    (re.compile(r"被([一-鿿]{1,8})的[一-鿿]{2,}"), "被X的Y"),
    (re.compile(r"[一-鿿]{2,}的隐形[一-鿿]{2,}"), "X的隐形Y"),
    (re.compile(r"[一-鿿]{2,}的双重[一-鿿]{2,}"), "X的双重Y"),
]


def rule_r_abstract(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for pat, label in R_ABSTRACT_PATTERNS:
            for m in pat.finditer(line):
                # "被X的Y" 中如果 X 起头是普通被动动词（被问到/被忽略/被问到时），
                # 不算抽象偏正——这是普通被动语态
                if label == "被X的Y":
                    inner = m.group(1) if m.groups() else ""
                    if any(inner == v or inner.startswith(v) for v in R_ABSTRACT_PASSIVE_VERB_BLACKLIST):
                        continue
                findings.append(Finding(
                    rule_id="R_ABSTRACT",
                    rule_name=f"抽象偏正结构（{label}）",
                    line=li,
                    matched=m.group(0),
                    excerpt=excerpt_for(doc, li, m.start(), len(m.group(0))),
                    hint="抽象偏正：定语堆名词，信息量为零。改成『谁/在什么情境/做了什么』的具体描述",
                ))
    return findings


# R2 "不是 X，而是 Y" 全文出现 >1 次
# 覆盖 writing_style.md 红线 2 列举的所有变体：不是/不仅/不止/不只 + 并非 + ...而是/而为
R2_PATTERN = re.compile(
    r"(?:不[是仅止只]|并非)[^，,。\n]{1,30}[，,]\s*而[是为][^，,。\n]{1,30}"
)


def rule_r_parallel(doc: Doc) -> list[Finding]:
    hits = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for m in R2_PATTERN.finditer(line):
            hits.append((li, m))
    if len(hits) <= 1:
        return []
    findings = []
    for li, m in hits:
        findings.append(Finding(
            rule_id="R_PARALLEL",
            rule_name="\"不是X，而是Y\"重复使用（全文最多1次）",
            line=li,
            matched=m.group(0),
            excerpt=excerpt_for(doc, li, m.start(), len(m.group(0))),
            hint="『不是 X，而是 Y』全文最多 1 次：重复 = 修辞模板批量生产。删掉或改成直接陈述",
        ))
    return findings


# R4 凑数标题
R4_PHRASES = [
    "三方向", "三步曲", "三位一体", "三大支柱",
    "五大发现", "五重困境", "四大趋势", "三大方向",
]


def rule_r_filler_num(doc: Doc) -> list[Finding]:
    findings = []
    for line_no, level, title in doc.headers:
        for phrase in R4_PHRASES:
            if phrase in title:
                idx = title.find(phrase)
                findings.append(Finding(
                    rule_id="R_FILLER_NUM",
                    rule_name="凑整齐数字标题",
                    line=line_no,
                    matched=phrase,
                    excerpt=title,
                    hint="凑数标题：数量由数据决定。报告里不暴露数字，叫『主要发现』即可",
                ))
    return findings


# R5 N<30 + 百分比
R5_N_PATTERNS = [
    re.compile(r"N\s*=\s*(\d+)", re.IGNORECASE),
    re.compile(r"n\s*=\s*(\d+)"),
    re.compile(r"(\d+)\s*[人位](?:受访者|访谈|店主|用户|被试|参与者|消费者|样本)"),
    re.compile(r"共\s*(\d+)\s*[人位]"),
    re.compile(r"访谈了?\s*(\d+)\s*[人位]"),
]
R5_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def rule_r_small_n(doc: Doc) -> list[Finding]:
    # 全文找最小 N
    sample_n = None
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for pat in R5_N_PATTERNS:
            for m in pat.finditer(line):
                try:
                    n = int(m.group(1))
                    if sample_n is None or n < sample_n:
                        sample_n = n
                except (ValueError, IndexError):
                    pass

    if sample_n is None or sample_n >= 30:
        return []

    findings = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for m in R5_PERCENT_PATTERN.finditer(line):
            findings.append(Finding(
                rule_id="R_SMALL_N",
                rule_name=f"N<30 ({sample_n}) 用百分比",
                line=li,
                matched=m.group(0),
                excerpt=excerpt_for(doc, li, m.start(), len(m.group(0))),
                hint=f"小样本（N={sample_n}<30）禁用百分比：百分比是强证据语感，撑不起来。改用计数『{sample_n} 人中 X 人』或案例编号『S3、S7、S11』",
            ))
    return findings


# ===== 春秋笔法层 =====
#
# 春秋笔法 = 不直接下判断，而是用语气词、定语、缓冲层暗示立场。
# AI 比人更系统地犯，因为 RLHF 训过它"避免直接下判断 / 保持平衡 / 软化措辞"。
#
# 4 种语法形态：
#   R_HEDGE_BUFFER    让步缓冲词        诚然 / 不可否认 / 客观地说 ... (黑名单)
#   R_HEDGE_TIME      时间副词偷渡定语   长期被 X / 一直被 X / 迟迟未 X (正则)
#   R_HEDGE_SIGNPOST  signposting       综上所述 / 值得注意的是 ... (黑名单)
#   Y_HEDGE_PASSIVE   假被动密度         单段 ≥3 处「被认为/被视为」(启发式)
#
# 前 3 个是黑名单/正则 → 红线（确定性高，触线即拒）
# 第 4 个是密度阈值 → 黄线（启发式，可能误判）

# 引号/blockquote 豁免：受保护区间内的春秋笔法词 = 引用原话/示例
# - blockquote: 行首 `>` (markdown 引用块) → 整行豁免
# - 中文引号「」『』+ 英文引号 ""'' + 中文书名号《》→ 区间内豁免
HEDGE_QUOTE_PAIRS = [("「", "」"), ("『", "』"), ('"', '"'), ("'", "'"), ("《", "》")]


def _hedge_protected_spans(line: str) -> list[tuple[int, int]]:
    """返回该行内被引号包围的 [start, end) 区间列表。"""
    spans: list[tuple[int, int]] = []
    for open_q, close_q in HEDGE_QUOTE_PAIRS:
        pos = 0
        while True:
            o = line.find(open_q, pos)
            if o == -1:
                break
            c = line.find(close_q, o + len(open_q))
            if c == -1:
                break
            spans.append((o, c + len(close_q)))
            pos = c + len(close_q)
    # 直引号 " ... "（同字符）按成对处理
    for q in ['"', "'"]:
        positions = [i for i, ch in enumerate(line) if ch == q]
        for i in range(0, len(positions) - 1, 2):
            spans.append((positions[i], positions[i + 1] + 1))
    return spans


def _is_in_protected_span(idx: int, spans: list[tuple[int, int]]) -> bool:
    return any(s <= idx < e for s, e in spans)


def _hedge_eligible(doc: Doc, li: int, line: str) -> tuple[bool, list[tuple[int, int]]]:
    """判断该行是否进入春秋笔法检查 + 返回引号豁免区间。"""
    if is_skipped(doc, li) or line.lstrip().startswith(">"):
        return False, []
    return True, _hedge_protected_spans(line)


# R_HEDGE_BUFFER 让步缓冲词
R_HEDGE_BUFFER_WORDS = [
    "诚然", "不可否认", "客观地说", "客观而言", "相对而言",
    "平心而论", "毋庸讳言", "毋庸置疑", "毫无疑问", "无可厚非",
]
R_HEDGE_BUFFER_PATTERNS = [
    re.compile(rf"(?:^|[，,。；;\s（()])({re.escape(w)})(?=[，,。；;\s：:])")
    for w in R_HEDGE_BUFFER_WORDS
]


def rule_r_hedge_buffer(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        ok, spans = _hedge_eligible(doc, li, line)
        if not ok:
            continue
        for pat in R_HEDGE_BUFFER_PATTERNS:
            for m in pat.finditer(line):
                if _is_in_protected_span(m.start(1), spans):
                    continue
                word = m.group(1)
                findings.append(Finding(
                    rule_id="R_HEDGE_BUFFER",
                    rule_name=f"春秋笔法 · 让步缓冲词「{word}」",
                    line=li,
                    matched=word,
                    excerpt=excerpt_for(doc, li, m.start(1), len(word)),
                    hint="让步缓冲词：用语气词暗示立场 = 偷渡判断。直接写结论，不用『诚然/不可否认』开场",
                ))
    return findings


# R_HEDGE_TIME 时间副词偷渡定语
R_HEDGE_TIME_PATTERNS = [
    (re.compile(r"长期被[一-鿿]{2,4}"), "长期被X"),
    (re.compile(r"一直被[一-鿿]{2,4}"), "一直被X"),
    (re.compile(r"迟迟未[一-鿿]{1,3}"), "迟迟未X"),
    (re.compile(r"始终未能[一-鿿]{2,4}"), "始终未能X"),
]


def rule_r_hedge_time(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        ok, spans = _hedge_eligible(doc, li, line)
        if not ok:
            continue
        for pat, label in R_HEDGE_TIME_PATTERNS:
            for m in pat.finditer(line):
                if _is_in_protected_span(m.start(), spans):
                    continue
                findings.append(Finding(
                    rule_id="R_HEDGE_TIME",
                    rule_name=f"春秋笔法 · 时间副词偷渡「{label}」",
                    line=li,
                    matched=m.group(0),
                    excerpt=excerpt_for(doc, li, m.start(), len(m.group(0))),
                    hint="时间副词偷渡：『长期被 X / 一直被 X』把判断伪装成定语。改成具体年限 + 数据（『过去 3 年财报显示...』）",
                ))
    return findings


# R_HEDGE_SIGNPOST signposting 假权威开场（从原 Y_BUREAU 升出来）
# 性质同 R_HEDGE_BUFFER：用语气词假装做了论证，黑名单可查 → 红线
R_HEDGE_SIGNPOST_WORDS = [
    "综上所述", "归根结底", "说到底", "值得注意的是",
    "不难看出", "显而易见", "不言而喻",
]
R_HEDGE_SIGNPOST_PATTERNS = [
    re.compile(rf"(?:^|[，,。；;\s（()])({re.escape(w)})(?=[，,。；;\s：:])")
    for w in R_HEDGE_SIGNPOST_WORDS
]


def rule_r_hedge_signpost(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        ok, spans = _hedge_eligible(doc, li, line)
        if not ok:
            continue
        for pat in R_HEDGE_SIGNPOST_PATTERNS:
            for m in pat.finditer(line):
                if _is_in_protected_span(m.start(1), spans):
                    continue
                word = m.group(1)
                findings.append(Finding(
                    rule_id="R_HEDGE_SIGNPOST",
                    rule_name=f"春秋笔法 · signposting「{word}」",
                    line=li,
                    matched=word,
                    excerpt=excerpt_for(doc, li, m.start(1), len(word)),
                    hint="signposting / 假权威开场：用语气词假装做了论证。直接陈述结论，不用『综上所述/值得注意的是』预告判断",
                ))
    return findings


# R8 摘要堆引语角标
R8_SUMMARY_TITLES = ("摘要", "执行摘要", "中心论点", "Executive Summary", "executive summary")
R8_FOOTNOTE_PATTERN = re.compile(r"\[\d+\]")


def rule_r_footnote(doc: Doc) -> list[Finding]:
    findings = []
    summary_ranges: list[tuple[int, int]] = []  # (start_line_1based, end_line_1based)
    for idx, (line_no, level, title) in enumerate(doc.headers):
        if any(t in title for t in R8_SUMMARY_TITLES):
            # 这个 section 范围 = 从 line_no 到下一个同级或更高级 header 之前
            end_line = len(doc.lines)
            for next_line, next_level, _ in doc.headers[idx + 1:]:
                if next_level <= level:
                    end_line = next_line - 1
                    break
            summary_ranges.append((line_no, end_line))

    if not summary_ranges:
        return []

    # 在 summary section 内：单段（连续非空非 skip 行）内 [n] 出现 ≥ 5 次
    for sec_start, sec_end in summary_ranges:
        for para_start, para_text in doc.paragraphs:
            para_end = para_start + para_text.count("\n")
            if para_end < sec_start or para_start > sec_end:
                continue
            matches = R8_FOOTNOTE_PATTERN.findall(para_text)
            if len(matches) >= 5:
                findings.append(Finding(
                    rule_id="R_FOOTNOTE",
                    rule_name="摘要内单段堆引语角标 ≥5",
                    line=para_start,
                    matched=f"{len(matches)} 个角标",
                    excerpt=para_text[:80] + ("..." if len(para_text) > 80 else ""),
                    hint="摘要堆角标：摘要是结论，不是论证。把引语下沉到主体章节，摘要只留 1-2 个最强证据",
                ))
    return findings


# R_DASH_TAIL 破折号反转拖腔（确定性短语黑名单 → 红线）
R_DASH_TAIL_PATTERNS = [
    re.compile(r"——而(?![已未])"),
    re.compile(r"——但(?![书是凡])"),
    re.compile(r"——这就是"),
    re.compile(r"——它就是"),
    re.compile(r"——这恰好是"),
    re.compile(r"——这正是"),
]


def rule_r_dash_tail(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for pat in R_DASH_TAIL_PATTERNS:
            for m in pat.finditer(line):
                findings.append(Finding(
                    rule_id="R_DASH_TAIL",
                    rule_name="破折号反转拖腔",
                    line=li,
                    matched=m.group(0),
                    excerpt=excerpt_for(doc, li, m.start(), len(m.group(0))),
                    hint="破折号反转拖腔：『——而/——但/——这就是』改成句号，直接陈述",
                ))
    return findings


# ---------- 黄线规则 ----------

# Y1 抽象主语
Y1_PATTERNS = [
    (re.compile(r"^[她他]们(普遍|普通|大多|多数|都)"), "她们/他们 + 概括副词"),
    (re.compile(r"^用户们[一-鿿]"), "用户们 作主语"),
    (re.compile(r"^大家普遍[一-鿿]"), "大家普遍"),
]
Y1_GENERIC_RECIPIENTS = re.compile(r"^多数受访者")


def rule_y_generic(doc: Doc) -> list[Finding]:
    findings = []
    # 段首检查
    for para_start, para_text in doc.paragraphs:
        # 取段第一句（句号/感叹号/问号前的部分）
        first_chunk = re.split(r"[。！？\n]", para_text, maxsplit=1)[0]
        for pat, label in Y1_PATTERNS:
            m = pat.match(first_chunk)
            if m:
                findings.append(Finding(
                    rule_id="Y_GENERIC",
                    rule_name=f"抽象主语（{label}）",
                    line=para_start,
                    matched=m.group(0),
                    excerpt=first_chunk[:60],
                    hint="抽象主语：『她们/用户们/大家普遍』把具体人压成均质团块。改用『22 人中 X 人』或案例编号",
                    severity="yellow",
                ))
        # 多数受访者 + 不紧跟数字
        m = Y1_GENERIC_RECIPIENTS.match(first_chunk)
        if m:
            after = first_chunk[m.end(): m.end() + 6]
            if not re.match(r"\s*\d", after):
                findings.append(Finding(
                    rule_id="Y_GENERIC",
                    rule_name="抽象主语（多数受访者，无具体计数）",
                    line=para_start,
                    matched=m.group(0),
                    excerpt=first_chunk[:60],
                    hint="抽象主语：改用具体计数或案例编号",
                    severity="yellow",
                ))
    return findings


# R_BUREAU 公文化连接词（黑名单可查 → 升红）
# 注：原 Y_BUREAU 里的 signposting 词（综上所述/值得注意的是 等）已迁到 R_HEDGE_SIGNPOST，
#    此规则只保留"通过 X 旨在 Y / 借由 / 进而推导"这类公文学术腔。
R_BUREAU_PATTERNS = [
    re.compile(r"通过[^。\n]{1,30}旨在"),
    re.compile(r"借由[^，。\n]{2,30}"),
    re.compile(r"进而推导"),
    re.compile(r"从而揭示"),
    re.compile(r"旨在揭示"),
]


def rule_r_bureau(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        for pat in R_BUREAU_PATTERNS:
            for m in pat.finditer(line):
                findings.append(Finding(
                    rule_id="R_BUREAU",
                    rule_name="公文化连接词",
                    line=li,
                    matched=m.group(0),
                    excerpt=excerpt_for(doc, li, m.start(), len(m.group(0))),
                    hint="公文连接词：『通过 X 旨在 Y / 借由 / 进而推导』是 AI 模仿学术腔。直接陈述，不用语气词预告论证",
                ))
    return findings


# Y4 章末金句
Y4_CLOSING_PHRASES = [
    "这是好消息",
    "值得深思",
    "不容忽视",
    "至关重要",
    "意义深远",
    "影响深远",
]
Y4_PRESCRIPTIVE_PATTERN = re.compile(
    r"^(应当|应该|必须|需要|应赋能|应重构|应底层重塑)[^。\n]{2,}[。!？]?$"
)


def rule_y_closing(doc: Doc) -> list[Finding]:
    findings = []
    # 章节最后一段 = 在两个 header 之间的最后一个段落
    if not doc.headers:
        return findings
    headers_with_end = []
    for i, (line_no, level, title) in enumerate(doc.headers):
        if i + 1 < len(doc.headers):
            end_line = doc.headers[i + 1][0] - 1
        else:
            end_line = len(doc.lines)
        headers_with_end.append((line_no, level, title, end_line))

    for sec_start, level, title, sec_end in headers_with_end:
        # 找该 section 内最后一个段落
        last_para = None
        for para_start, para_text in doc.paragraphs:
            para_end = para_start + para_text.count("\n")
            if para_start >= sec_start and para_end <= sec_end:
                last_para = (para_start, para_text)
        if not last_para:
            continue
        para_start, para_text = last_para
        # 取最后一句（最后的句号/感叹号/问号前的部分；若以这些结尾则取倒数第二个分割）
        sentences = [s.strip() for s in re.split(r"[。！？]", para_text) if s.strip()]
        if not sentences:
            continue
        last_sentence = sentences[-1]
        # 命中关闭性短语
        for phrase in Y4_CLOSING_PHRASES:
            if phrase in last_sentence and last_sentence.endswith(phrase) or last_sentence.startswith(phrase):
                findings.append(Finding(
                    rule_id="Y_CLOSING",
                    rule_name=f"章末金句（{phrase}）",
                    line=para_start + para_text.count("\n"),
                    matched=phrase,
                    excerpt=last_sentence[:80],
                    hint="章末金句：『值得深思 / 不容忽视』每章都来一遍 = 模板套路。改用过渡句或留白",
                    severity="yellow",
                ))
                break
        # 命中规范性祈使句
        if Y4_PRESCRIPTIVE_PATTERN.match(last_sentence):
            findings.append(Finding(
                rule_id="Y_CLOSING",
                rule_name="章末规范性祈使句（应当/应该/必须...）",
                line=para_start + para_text.count("\n"),
                matched=last_sentence[:30],
                excerpt=last_sentence[:80],
                hint="章末规范性祈使（『应该/必须/应赋能』）：报告里金句最多 1-2 句，且必须挂证据 + 边界（参考红线 6）",
                severity="yellow",
            ))
    return findings


# Y_DASH_DENSITY 段内破折号密度（启发式计数 → 黄线）
# 与 R_DASH_TAIL 拆开：R_DASH_TAIL 抓确定性短语，Y_DASH_DENSITY 抓段内 ≥2 个 ——
# 段内 ≥2 个 —— = 用同一修辞模板做"金句感分句"，但单段 1 个 —— 可能是合法插入语
def rule_y_dash_density(doc: Doc) -> list[Finding]:
    findings = []
    for para_start, para_text in doc.paragraphs:
        cnt = para_text.count("——")
        if cnt >= 2:
            first_offset = para_text.find("——")
            line_offset = para_text[:first_offset].count("\n")
            findings.append(Finding(
                rule_id="Y_DASH_DENSITY",
                rule_name=f"段内破折号 \"——\" 重复（{cnt} 次）",
                line=para_start + line_offset,
                matched="——",
                excerpt=para_text[:120] + ("..." if len(para_text) > 120 else ""),
                hint="段内多破折号（≥2 处）：能用句号的地方优先用句号。『——』留给真正的插入语，不做金句感分句",
                severity="yellow",
            ))
    return findings


# Y_BOLD 单行加粗滥用（参考 humanizer #15 Boldface overuse）
# 单行内 **xxx** 出现 ≥ 3 次 = 一句话堆加粗，加粗失效
# 不按段统计——markdown 列表里每行一个加粗关键词是合法用法（工具文档/要点列表常见）
Y_BOLD_PATTERN = re.compile(r"\*\*[^*\n]{1,40}\*\*")
Y_BOLD_LABEL_PATTERN = re.compile(r"^\s*\*\*[^*\n]{1,20}\*\*\s*[:：]")


def rule_y_bold(doc: Doc) -> list[Finding]:
    findings = []
    for li, line in enumerate(doc.lines, start=1):
        if is_skipped(doc, li):
            continue
        # "**标签**: 值  **标签2**: 值" 元信息行：跳过（首个加粗紧跟冒号）
        if Y_BOLD_LABEL_PATTERN.match(line):
            continue
        bold_matches = Y_BOLD_PATTERN.findall(line)
        if len(bold_matches) >= 3:
            findings.append(Finding(
                rule_id="Y_BOLD",
                rule_name=f"单行加粗滥用（{len(bold_matches)} 处 **）",
                line=li,
                matched=f"{len(bold_matches)} 处加粗",
                excerpt=line[:120] + ("..." if len(line) > 120 else ""),
                hint="单行加粗滥用（≥3 处）：一句话堆 3 个加粗 = 加粗失效。最多保留 1-2 个，或改写成列表项每行一个",
                severity="yellow",
            ))
    return findings


# Y_HEDGE_PASSIVE 假被动密度（春秋笔法的启发式补充）
# 单段内 "被认为/被视为/被看作/被普遍认为/被广泛认为" 合计 ≥3 次
# = 隐藏施动者"谁认为？"，是 AI 默认输出的春秋笔法形态。
# 与 R_HEDGE_BUFFER/TIME/SIGNPOST 同属春秋笔法层；前 3 个是黑名单红线，本条是启发式黄线。
#
# 阈值 3 是经验值，未经真实报告 dogfood 校准（fixture 是合成的）。
# 如果在真实场景下出现误判（学术报告描述实验过程偶发被动），
# 考虑：(a) 收紧词表；(b) 阈值放宽到 4；(c) 排除"§方法论"章节。
# 调整前先收 5+ 份真实报告样本，看分布再决定。
Y_HEDGE_PASSIVE_PATTERNS = [
    re.compile(r"被认为"),
    re.compile(r"被视为"),
    re.compile(r"被看作"),
    re.compile(r"被普遍认为"),
    re.compile(r"被广泛认为"),
]


def rule_y_hedge_passive(doc: Doc) -> list[Finding]:
    findings = []
    for para_start, para_text in doc.paragraphs:
        cnt = sum(len(p.findall(para_text)) for p in Y_HEDGE_PASSIVE_PATTERNS)
        if cnt >= 3:
            # 找首次出现位置
            first_idx = min(
                (m.start() for p in Y_HEDGE_PASSIVE_PATTERNS for m in p.finditer(para_text)),
                default=0,
            )
            line_offset = para_text[:first_idx].count("\n")
            findings.append(Finding(
                rule_id="Y_HEDGE_PASSIVE",
                rule_name=f"春秋笔法 · 假被动密度（{cnt} 处「被认为/被视为/被看作」）",
                line=para_start + line_offset,
                matched=f"{cnt} 处假被动",
                excerpt=para_text[:120] + ("..." if len(para_text) > 120 else ""),
                hint="假被动密度（单段 ≥3 处）：连续『被认为/被视为』隐藏施动者。给出具体来源（『S3/S7 等 4 位店主表示...』）或改主动语态",
                severity="yellow",
            ))
    return findings


# Y_TITLE 同级标题同构（启发式）
def rule_y_title_isomorphic(doc: Doc) -> list[Finding]:
    findings = []
    if len(doc.headers) < 3:
        return findings

    # 按 level 分组
    by_level: dict[int, list[tuple[int, str]]] = {}
    for line_no, level, title in doc.headers:
        by_level.setdefault(level, []).append((line_no, title))

    # 编号前缀：剥离后再算骨架，避免把 "1.1 / 1.2" 或 "一、X / 二、X" 当成修辞同构
    NUMBER_PREFIX_RE = re.compile(
        r"^\s*("
        r"\d+(\.\d+)*\.?"          # 1 / 1.1 / 1.1.1 / 1.
        r"|[一二三四五六七八九十]+[、.]"  # 一、 / 二.
        r"|[A-Z]\."                   # A. B.
        r"|[（(]\d+[）)]"              # (1) （1）
        r"|\d+[)）]"                   # 1) 1）
        r")\s*"
    )

    for level, items in by_level.items():
        if len(items) < 3:
            continue
        # 标题骨架：先剥离编号前缀，再把中文/字母/数字替换为 X，剩余"标点 + 空格"序列
        skeletons = []
        for line_no, title in items:
            stripped = NUMBER_PREFIX_RE.sub("", title)
            skel = re.sub(r"[一-鿿A-Za-z0-9]+", "X", stripped)
            skel = re.sub(r"\s+", "", skel)
            skeletons.append((line_no, title, skel))

        # 计数骨架出现次数；若同骨架 ≥ 3 → 触发
        from collections import Counter
        skel_count = Counter(s[2] for s in skeletons)
        for skel_str, cnt in skel_count.items():
            # 跳过空骨架/裸 X（剥离编号后剩纯文本）—— 普通标题不算同构
            # 触发条件：剩余有非平凡的标点结构（如 X——X / X：X / X的Y / 复杂连接）
            if cnt < 3:
                continue
            if not skel_str.strip():
                continue
            if skel_str == "X":
                continue
            # 仅当骨架包含修辞性符号（破折号/冒号/中文标点）时才报
            if not re.search(r"[——：:，,；;的与和]", skel_str):
                continue
            affected = [(ln, t) for ln, t, sk in skeletons if sk == skel_str]
            first_line = affected[0][0]
            findings.append(Finding(
                rule_id="Y_TITLE",
                rule_name=f"H{level} 同级标题骨架同构（{cnt} 个）",
                line=first_line,
                matched=skel_str,
                excerpt=" / ".join(t for _, t in affected[:3]),
                hint="同级标题骨架同构（启发式）：5 个二级标题长得一样 = AI 按模板填空。回炉重写让标题各自反映真发现（启发式，请人工复核）",
                severity="yellow",
            ))
    return findings


# ---------- 主 lint ----------

# 17 条规则按 5 层组织（详见 writing_style.md 第七节对照总表）：
# - 词法层：R_VOCAB / R_FILLER_NUM / R_BUREAU
# - 句法层：R_PARALLEL / R_ABSTRACT / R_DASH_TAIL
# - 春秋笔法层：R_HEDGE_BUFFER / R_HEDGE_TIME / R_HEDGE_SIGNPOST / Y_HEDGE_PASSIVE
# - 定量纪律层：R_SMALL_N / R_FOOTNOTE
# - 结构/视觉层（启发式）：Y_DASH_DENSITY / Y_BOLD / Y_TITLE / Y_GENERIC / Y_CLOSING
#
# 命名约定：R_* = 黑名单/正则零误判（触线即拒），Y_* = 启发式（可能误判，人工复核）
ALL_RULES = [
    # 红线（11 条，黑名单可查）
    rule_r_vocab,
    rule_r_filler_num,
    rule_r_bureau,
    rule_r_parallel,
    rule_r_abstract,
    rule_r_dash_tail,
    rule_r_hedge_buffer,
    rule_r_hedge_time,
    rule_r_hedge_signpost,
    rule_r_small_n,
    rule_r_footnote,
    # 黄线（6 条，启发式或可保留）
    rule_y_hedge_passive,
    rule_y_dash_density,
    rule_y_bold,
    rule_y_title_isomorphic,
    rule_y_generic,
    rule_y_closing,
]


def lint(path: Path) -> tuple[list[Finding], list[Finding]]:
    raw = path.read_text(encoding="utf-8")
    doc = preprocess(raw)
    red, yellow = [], []
    for rule in ALL_RULES:
        for f in rule(doc):
            if f.severity == "red":
                red.append(f)
            else:
                yellow.append(f)
    # 同 line 同 rule_id 同 matched 去重
    def dedupe(fs):
        seen = set()
        out = []
        for f in fs:
            key = (f.rule_id, f.line, f.matched)
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


# ---------- 输出 ----------

def format_text(path: Path, red: list[Finding], yellow: list[Finding], show_warn: bool) -> str:
    lines = []
    lines.append(f"=== Lint: {path} ===")
    if not red and (not yellow or not show_warn):
        lines.append("✅ PASS — 无红线" + ("" if not yellow else f"（{len(yellow)} 处黄线已抑制）"))
    else:
        status = "❌ FAIL" if red else "⚠ WARN"
        parts = [f"红线 {len(red)} 处"]
        if show_warn:
            parts.append(f"黄线 {len(yellow)} 处")
        lines.append(f"{status} — {' / '.join(parts)}")
    lines.append("")

    for f in red:
        lines.append(f"[{f.rule_id} · {f.rule_name}] L{f.line}")
        lines.append(f"  > {f.excerpt}")
        if f.matched and f.matched not in f.excerpt:
            lines.append(f"  命中: {f.matched}")
        lines.append(f"  改: {f.hint}")
        lines.append("")

    if show_warn:
        for f in yellow:
            lines.append(f"[{f.rule_id} · {f.rule_name} (warn)] L{f.line}")
            lines.append(f"  > {f.excerpt}")
            if f.matched and f.matched not in f.excerpt:
                lines.append(f"  命中: {f.matched}")
            lines.append(f"  改: {f.hint}")
            lines.append("")

    lines.append(f"Exit {1 if red else 0}.")
    return "\n".join(lines)


def format_md(path: Path, red: list[Finding], yellow: list[Finding], show_warn: bool) -> str:
    lines = []
    lines.append(f"# Lint: `{path}`")
    lines.append("")
    if not red and (not yellow or not show_warn):
        lines.append("**PASS** — 无红线" + ("" if not yellow else f"（{len(yellow)} 处黄线已抑制）"))
    else:
        status = "**FAIL**" if red else "**WARN**"
        parts = [f"红线 {len(red)} 处"]
        if show_warn:
            parts.append(f"黄线 {len(yellow)} 处")
        lines.append(f"{status} — {' / '.join(parts)}")
    lines.append("")

    def emit(f: Finding, kind: str):
        lines.append(f"### {kind} `{f.rule_id}` · {f.rule_name} — L{f.line}")
        lines.append("")
        lines.append(f"> {f.excerpt}")
        lines.append("")
        if f.matched and f.matched not in f.excerpt:
            lines.append(f"- 命中：`{f.matched}`")
        lines.append(f"- 改：{f.hint}")
        lines.append("")

    if red:
        lines.append("## 红线（hard fail）")
        lines.append("")
        for f in red:
            emit(f, "🔴")
    if show_warn and yellow:
        lines.append("## 黄线（warning）")
        lines.append("")
        for f in yellow:
            emit(f, "🟡")
    return "\n".join(lines)


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="研究报告写作风格 lint（writing_style.md 红线/黄线机器可识别部分）",
    )
    parser.add_argument("path", help="要检查的 markdown 报告路径")
    parser.add_argument("--format", choices=["text", "md"], default="text",
                        help="输出格式：text（默认）/ md")
    parser.add_argument("--quiet", action="store_true", help="只返回 exit code，不打印")
    parser.add_argument("--no-warn", action="store_true", help="不显示黄线警告")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        if not args.quiet:
            print(f"lint: 文件不存在: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        if not args.quiet:
            print(f"lint: 不是文件: {path}", file=sys.stderr)
        return 2

    try:
        red, yellow = lint(path)
    except Exception as e:
        if not args.quiet:
            print(f"lint: 读取/分析失败: {e}", file=sys.stderr)
        return 2

    show_warn = not args.no_warn
    if not args.quiet:
        if args.format == "md":
            out = format_md(path, red, yellow, show_warn)
        else:
            out = format_text(path, red, yellow, show_warn)
        print(out)

    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
