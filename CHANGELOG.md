# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.7.0] — 2026-06-09

### 改

- `skills/research-detective/SKILL.md` 步骤 5 质量检查从冗长 checklist 精简为 4 道机器强制红线（CONTEXT / 五动作分文件 / 报告风格 / B1 信息包）+ 语义自检引用，可读性和可执行性提升
- 三个 SKILL.md 的 `description` 字段动词前置，触发词更直接（archivist / detective / reviewer）
- `.claude-plugin/marketplace.json` 描述重写，突出"分析资料、找隐藏洞察、写可证伪报告"

### 增

- `skills/research-detective/scripts/lint_process.py` 新增红线 `P_NO_ALT_3D`：3d 矛盾审计中每个核心结论至少写一条「替代解释 / 竞争性解释」，避免分析过早收敛（同步更新 fixture 与 `writing_style.md` 自查清单）
- `skills/research-detective/guides/delivery_checklist.md`：交付前语义层自检清单（A 流程产物 / B 报告规范 / C 侦探方法专属 / D wiki 回写 / E B1 信息包）
- `RELEASE_CHECKLIST.md`：发版前必跑清单（版本与文档 / plugin-validator / 干净环境冒烟 / 已知失败模式 / tag 发布）
- `CONTRIBUTING.md`：贡献指南

---

## [0.6.1] — 2026-06-09

### 分析深度三项微调

- **证据强度内联标签**：writing_style.md 新增要求 6——核心结论旁标注 `[N人提及 / M反例 / 跨K类来源]`，自查清单论据层同步加入
- **异常用户扫描（Anomaly Hunter）**：SKILL.md 步骤 3b 盲区扫描新增"反向找人"段落——完成异常信号识别后，找行为/态度组合与多数人偏差最大的 2-3 个个体，输出完整画像
- **竞争性解释（必做）**：SKILL.md 步骤 3d 矛盾审计新增硬性要求——每个核心结论至少列 1 条替代解释；`lint_process.py` 新增 `P_NO_ALT_3D` 规则机器校验（检测「替代解释/也可能是/竞争性解释」等关键词）

### 修改

- `skills/research-detective/SKILL.md`：步骤 3b 加 Anomaly Hunter 段落；步骤 3d 加竞争性解释要求；中间产物表 3d 行更新
- `skills/research-detective/guides/writing_style.md`：报告 prompt 硬约束 [要求] 加第 6 条；自查清单论据层加内联标签项
- `skills/research-detective/scripts/lint_process.py`：新增 `ALT_EXPLANATION_KEYWORDS` + `P_NO_ALT_3D` 规则
- `skills/research-detective/scripts/tests/fixture_process_good/3d_contradictions_audit.md`：每个结论补替代解释，适配新 lint
- `README.md`：新增"Roadmap 与已知局限"章节（跨项目知识图谱 + 组织遗忘检测作为未来方向）

### 测试

- 全部 61 项 detective 测试 + 18 项 shared 测试通过

## [0.6.0] — 2026-06-09

### 反幻觉加固层(本版主线)

把 LLM 在研究分析中的 4 类幻觉做成机器可验,从抽查兜底升级到全量拦截:

- **H3 引用改写** → 新增 `verify_quotes.py`,扫 wiki 所有「证据」栏的一手引用,逐条到 `data/<id>.*` 子串匹配。改一个字、加一个词、引用不存在的资料编号都会 fail。覆盖率从抽 3 份(~6%)拉到 100%
- **H10/H13 任务漂移 + 空话化** → 新增 `lint_context.py`,机器化拦截 CONTEXT 占位符残留 / 必填字段空 / 核心问题 < 20 字 / 底线套话。地基不稳后续所有产出都歪
- **H12 表面合规** → 新增 `lint_process.py`,强制 detective 把 5 个侦探动作产物分写入 `process/3a_coding.md` ~ `3e_evidence_chains.md` 五个独立文件且字段达标——LLM 不能糊在一份 detective_analysis.md 里写"已完成盲区扫描"
- **H12 留足迹 + H6 跨角色复核** → 新增 `lint_review.py`,验 review.md 每个核心结论必须有 `**搜索记录**` 段(confirmed 至少 3 轮 + 2 个一手编号)、weakened/challenged 必须有 `**反面证据**` 段、整文档必须有「证据强度复核」表(detective 标 vs reviewer 重标 + 重标依据)
- **H1 LLM 推理随机性** → reviewer 步骤 2 默认走 multi-agent 采样取交集(3 个独立 subagent → 取交集),token 约 3×。这是少数能从结构上对抗 H1 的手段。低 stake 可声明降级到单 LLM,但 review.md 必须显式声明筛选模式

### 新增产物

- `skills/research-archivist/scripts/verify_quotes.py` + fixture(good/bad)+ runner
- `skills/research-detective/scripts/lint_process.py` + fixture(good/bad)+ 集成到现有 runner
- `skills/research-reviewer/scripts/lint_review.py` + fixture(good/bad)+ runner
- `shared/scripts/lint_context.py` + fixture(good/bad)+ runner
- 4 个 runner 共 108 项测试 100% PASS;4 类故意污染均被对应 lint 抓到

### 修改

- `shared/cold_start.md` 步骤 4 合并写入后强制跑 `lint_context.py`
- `shared/CLAUDE.md` 新增「反幻觉检查链」章节,串起所有 lint 与对应防御目标
- `skills/research-archivist/SKILL.md` 步骤 5 入库回检拆成 5a 机器全量校验 + 5b 人工抽 3 份
- `skills/research-detective/SKILL.md` 步骤 3 强制 5 个分文件中间产物;步骤 5 检查清单加 `lint_process.py`
- `skills/research-detective/workflows/report_workflow.md` §3 lint 段并列加入 lint_process
- `skills/research-reviewer/SKILL.md` allowed-tools 加 `Agent`;步骤 2 重写为 multi-agent 采样;步骤 3 加搜索记录强制结构 + 跨角色证据强度复核表;步骤 4 加 `lint_review.py`
- 三个 SKILL.md 步骤 1 的 CONTEXT 完整性检查全部接入 `lint_context.py`

### 文档

- `README.md` 项目结构反映新增 scripts/ 目录;排错段更新中间产物文件名为五件套
- 新增 `CHANGELOG.md`(本文件)

### 预期效果

综合幻觉率从前一版的 30-45 区间预期降到 15-25 区间。剩余天花板是 LLM 推理本身的随机性,这是模型物理特性,prompt 改不动。

### 成本

- skill 体积 +15%
- token +30-50%(主要由 multi-agent 采样贡献,可通过「快速审」降级)
- 端到端时间 +25-40%

---

## [0.5.0] — 2026-06-08

### 新增

- 跨 skill 契约层(`contracts/wiki_format.md` / `analysis_writeback.md` / `information_pack.md`)
- detective 步骤 4 产出形态路由:简报(A1+A2)/ 完整报告 二选一,brief/report workflow 模块化
- B1 信息包(`information_pack_<slug>.md`)+ `lint_information_pack.py`,把研究产出打包成下游 AI 可消费的决策切片

---

## [0.2.1] — 历史版本

封堵增量入库的漏洞,显式暴露日常运维入口。

## [0.2.0] — 历史版本

研究员可以给大胆假设型建议,但每条建议必须挂证据锚 + 边界 + 可证伪的下一步。

## 早期版本

- 0.1 — 初版:三个 skill 协作的侦探方法论框架
