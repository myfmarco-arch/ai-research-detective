# Claude Code 版本

## 安装

```bash
cp -r research-wiki ~/.claude/skills/research-wiki
cp -r research-expert ~/.claude/skills/research-expert
cp -r research-reviewer ~/.claude/skills/research-reviewer
```

可选但推荐——在你的研究项目根目录放一份 `CLAUDE.md`，确保 Claude 在修改报告等操作时自动加载对应 skill：

```bash
cp CLAUDE.md ~/my-research/CLAUDE.md
```

## 使用

### 第一步：入库

在研究项目目录下启动 Claude Code：

```bash
cd ~/my-research
claude
```

把资料放在当前目录（或 `data/` 子目录），然后说：

```
帮我把访谈资料入库到 wiki
```

research-wiki skill 会自动激活，逐份阅读资料，建出 `wiki/` 知识库。

增量更新——有新资料时：

```
有新的问卷数据，帮我更新 wiki
```

### 第二步：侦探分析

入库完成后：

```
用 research-expert 分析 wiki 里的数据
```

或者带具体问题：

```
加载 research-expert skill，分析用户对隐私的真实态度
```

research-expert 会检测到 `wiki/` 目录，跳过证据采集，直接在 wiki 上执行侦探分析。

### 第三步：对抗审查（可选但推荐）

分析报告产出后：

```
用 research-reviewer 审查这份报告
```

reviewer 会提取核心结论，主动搜索反面证据，产出 `outputs/review.md`。

然后让 expert 根据审查结果修正：

```
根据 review.md 的审查结果修改报告
```

### 不用 wiki 也能跑

如果资料量小（≤50 份），可以跳过入库，直接用 research-expert：

```
帮我分析 data/ 里的用户访谈
```

research-expert 会自己做证据采集和分析。wiki 模式的优势在大数据量和增量更新场景。

## 文件结构

```
research-wiki/
└── SKILL.md              # 入库工作流

research-expert/
├── SKILL.md              # 侦探分析工作流
├── guides/
│   ├── research_methodology.md   # 置信度标准、备忘录格式
│   └── detective_toolkit.md      # 26 个分析工具（按需加载）
├── templates/
│   ├── simple_report.md          # 研究报告模板
│   ├── answer_summary.md        # A1 回答/摘要模板
│   └── evidence_chain.md        # A2 证据链图谱模板
└── config/
    ├── default.json              # 默认配置
    └── advanced.json             # 高级配置

research-reviewer/
└── SKILL.md              # 对抗性审查工作流
```

## 支持的资料类型

| 类型 | 格式 | 处理方式 |
|------|------|---------|
| 定性访谈 | .md / .txt / .json | LLM 逐份阅读 |
| 定量问卷 | .csv / .xlsx | Python 统计 + LLM 解读 |
| 文献 | .md / .pdf | LLM 提取理论框架 |
| 竞品资料 | .md | LLM 提取能力矩阵 |

## 提示

- 首次使用建议先说 `加载 research-wiki skill` 或 `加载 research-expert skill`，确保 skill 在分析开始前就被加载
- 如果 Claude 没有停下来问你研究问题就直接开始分析，提醒它："先问我研究问题是什么"
- 分析完成后检查 `work/` 目录是否有中间产物（evidence_extraction.md、detective_analysis.md）
