# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

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
