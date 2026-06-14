# Skill 触发与创新点验收用例

> 目的：验证本项目的创新点不仅写在 README 里，也能在 skill 触发、执行过程和交付产物中显性出现。本文是手动/半自动 eval 清单，不替代脚本 lint。

## A. research-detective should-trigger

### D1 深度侦探分析

输入：

```text
基于 wiki 做一轮深度侦探分析，重点找隐藏关联、矛盾和低频高强度信号。
```

预期：

- 触发 `research-detective`。
- 读取 `guides/method_index.md` 和 `guides/detective_toolkit.md`。
- 生成或要求生成 `process/0_method_selection.md`。
- 生成 3a-3e 侦探动作产物；wiki 模式可省 `3a_coding.md`。
- `0_method_selection.md` 写明研究类型、选用工具、未选工具及理由、方法风险。
- 不默认全跑 26 个工具。

### D2 用户需求探索

输入：

```text
分析这些访谈，帮我找用户真实需求、痛点优先级和产品机会。
```

预期：

- 触发 `research-detective`。
- `process/0_method_selection.md` 的研究类型应为“用户需求探索”或“产品定位/需求优先级”。
- 选用工具应覆盖线索提取、证据分级、模式扫描，并从 JTBD / Kano / 用户旅程 / 5 Whys 中选择适用工具。
- 输出结论必须有证据链和置信度。

### D3 研究简报

输入：

```text
基于 wiki 回答：用户为什么不愿意授权通讯录？给我研究简报。
```

预期：

- 触发 `research-detective`。
- 路由到 `brief_workflow.md`。
- 用户可见输出使用“研究简报”和“证据链图谱”。
- 不出现 `A1` / `A2` / `B1`。
- 用户未明确说“给下游 AI 用”时，不默认生成 AI 接力包。

### D4 深度分析报告

输入：

```text
请生成一份完整深度分析报告，用于产品方向评审。
```

预期：

- 触发 `research-detective`。
- 路由到 `report_workflow.md`。
- 先完成报告需求澄清门禁。
- 产出体系为：深度分析报告 + 侦探备忘录 + 证据链图谱，可选 AI 接力包。
- 报告将作为决策依据时，主动建议运行 `research-reviewer`。

## B. research-detective should-not-trigger

### N1 原始资料入库

输入：

```text
新增了 8 份访谈，帮我更新 wiki，不要写报告。
```

预期：

- 应触发 `research-archivist`，不是 `research-detective`。
- 目标是增量入库和引用校验，不形成结论。

### N2 纯对抗审查

输入：

```text
审查 outputs/report.md，专门找能推翻核心结论的证据，不要改写。
```

预期：

- 应触发 `research-reviewer`，不是 `research-detective`。
- reviewer 只指出 confirmed / weakened / challenged，不给改写方案。

### N3 研究方法规划

输入：

```text
我这个研究该用访谈还是问卷？帮我设计研究方案。
```

预期：

- 不触发 `research-detective`。
- 应转 planner / 普通研究规划流程。

### N4 少量材料快速初看

输入：

```text
这 5 份访谈先帮我快速看一下，不用正式报告。
```

预期：

- 不进入完整 detective 流程。
- 如果没有 scout，先说明这是轻量初看，不产出正式证据链图谱或侦探备忘录。

## C. near-miss

### M1 整理资料并给结论

输入：

```text
整理这批资料并告诉我有什么洞察。
```

预期：

- 如果资料未入库且后续会复用：先建议 `research-archivist` 入库，再 `research-detective` 分析。
- 如果已有 wiki：直接 `research-detective`。
- 如果用户只要快速初看：不要承诺正式结论。

### M2 看报告有没有问题并改好

输入：

```text
帮我看看报告有没有问题并顺手改好。
```

预期：

- 先区分意图：对抗审查交给 `research-reviewer`，修订交给 `research-detective`。
- 不让 reviewer 直接改写。

## D. 创新点验收

### I1 侦探方法论可见

预期：

- README 前半部分展示“核心创新”和“五个侦探动作”。
- `research-detective/SKILL.md` 有 `Detective Capabilities`。
- 正式分析产物包含 `process/0_method_selection.md` 和 3a-3e。

### I2 工具箱不是隐藏附录

预期：

- `guides/method_index.md` 是 guides 的方法入口。
- 正式分析前必须读取工具箱速查表。
- `process/0_method_selection.md` 记录选用和未选工具。

### I3 输出命名用户友好

预期：

- 用户可见文档和 workflow 使用“研究简报 / 深度分析报告 / 证据链图谱 / 侦探备忘录 / AI 接力包”。
- 不再对用户暴露 `A1` / `A2` / `B1`。
- 文件名 `answer_summary.md`、`evidence_chain.md`、`information_pack_<slug>.md` 可保留兼容。

### I4 AI 接力包边界清楚

输入：

```text
把这次研究结论打成给产品 AI 写 PRD 用的接力包。
```

预期：

- 触发 AI 接力包，而不是重新写报告。
- 读取 `contracts/information_pack.md`。
- `specialization` 识别为 `prd`。
- 生成后运行 `lint_information_pack.py`。
