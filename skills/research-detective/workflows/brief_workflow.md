# 简报工作流(brief workflow)

适用场景:用户问了一个**具体问题**,没有说"写报告""出报告""生成报告"。

产出形态:**A1 + A2**(主线),按需追加 **B1 信息包**(扩展)。

> 这是 detective 两条产出工作流之一,另一条是 [report_workflow.md](report_workflow.md)。SKILL.md 步骤 4 根据用户意图路由到这里。

## 1. 主线产出:A1 + A2

### 1.1 A1 一页摘要

- 直接在对话中回答,按 [../templates/answer_summary.md](../templates/answer_summary.md) 结构。
- **控制在 300 字以内,最多不超过 500 字**。
- 建议部分必须结合 CONTEXT.md 给出针对性建议——不允许通用建议表。
- A1 **只在对话中输出,不保存文件**(简报形态下,A1 是对话级产物)。

### 1.2 A2 证据链图谱

- **必须严格按** [../templates/evidence_chain.md](../templates/evidence_chain.md) **的表格格式**(证据节点表 + 关系表 + 强度摘要)。不要用自由格式替代。
- 保存到 CONTEXT 速读卡声明的"产出位置"下的 `evidence_chain.md`(默认 `outputs/evidence_chain.md`)。

### 1.3 写作约束(简报形态共用)

- **写作风格底线**:落笔前读 [../guides/writing_style.md](../guides/writing_style.md) 的红线 5 条 + 心法 5 条;落笔后跑 lint(见 §1.4)。报告级的结构清单(report_principles.md 13 项)简报不必逐条对照,但底线层(声明清晰、证据可追溯)同样适用。
- **大胆假设小心求证**:研究员要敢给观点和建议,但每条建议必须挂证据锚 + 边界 + 可证伪的下一步——详见 writing_style.md 心法 5、红线 6。
- **对照 CONTEXT**:身份(专业视角)、底线(产出前自检)、范围(引用限定)。

### 1.4 lint(写完跑)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/research-detective/scripts/lint_report.py outputs/evidence_chain.md
```

A1 因为只在对话输出,不进 lint 体检——但 A1 用词同样要遵守红线(尤其禁词组、N<30 用百分比、概念癌)。

## 2. 扩展产出:B1 信息包(按需)

### 2.1 何时启动

简报完成后,用户**明确说**"打个包""给下游 AI 用""做信息包""给产品/设计/战略 AI"时启动。或者步骤 6 反馈环节,detective 主动建议、用户确认。

**不要默认生成**——A1+A2 在团队内消化是常态,真要给下游 AI 的是少数。

### 2.2 前置条件

A1+A2 已完成。没有结论就没有包可打。

### 2.3 完整契约见

[../../../contracts/information_pack.md](../../../contracts/information_pack.md)

包含:设计立场、特化方向识别(`general` / `prd` / `design` / `strategy`)、AI 友好产物清理、§3 全证据素材库、§4 决策切片必填要求、§5 成功状态、隐私与时效、跨 ID 完整性 lint、与其他产物的关系。

**生成 B1 前必读这份契约**。模板在 [../templates/information_pack.md](../templates/information_pack.md)。

### 2.4 lint(生成完跑)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/research-detective/scripts/lint_information_pack.py outputs/information_pack_<slug>.md
```

红线 0 处才能交付。详见契约 §7。

### 2.5 交付告知

生成完毕后告诉用户:包文件名(`information_pack_<slug>.md`)+ 有效期(默认 3 个月)+ 提醒"过期前研究员可重新生成;下游 AI 引用时请保留 `generated_at`"。

## 3. 简报形态的边界

简报形态**不产出**:

- 完整研究报告(走 [report_workflow.md](report_workflow.md))
- 侦探备忘录(独立报告章节;简报里如有关键盲区/隐藏关联,直接写进 A1 的"侦探备忘录亮点"一条)
- 长篇论证、多章节结构

简报形态**目前不进** research-reviewer 对抗审查(reviewer 当前只支持完整报告形态)。简报对外发布或作为决策依据时,如需对抗验证,可手动让 reviewer 审 A1+A2 文件,但流程是非标的。
