# AI Research Detective 🔍

基于**侦探方法论（Detective Method）**的 AI 研究分析工具。利用 LLM 的完美记忆和无偏差全局扫描能力，在定性定量分析的基础上做人类研究员做不到的元分析。

A research analysis toolkit powered by the **Detective Method** — a meta-analysis paradigm that leverages LLM's perfect memory and unbiased global scanning to complement human researchers' cognitive limitations.

本仓库本身就是一个 **Claude Code plugin**，包含三个协作的 skill（archivist 入库 / detective 分析 / reviewer 审查）和它们共用的 `shared/` 资源——冷启动流程（驱动 skill 在空项目里自动生成 `CONTEXT.md`、`README.md` 并把项目级 `CLAUDE.md` 复制到研究项目根）、模板、项目级硬约束。

---

## 为什么需要它

研究员最大的瓶颈不是方法论——访谈分析、问卷统计、竞品对比这些方法已经很成熟。瓶颈是执行方法的人：

| 人的认知局限 | 后果 |
| --- | --- |
| 记忆衰退 | 读到第 15 份时已忘了第 3 份的细节 |
| 确认偏误 | 忽略不符合预期的异常信号 |
| 模式识别天花板 | 无法处理 20 份材料的 N×N 交叉关联 |
| 频率估计不准 | "感觉有几个人提到过"的直觉很不可靠 |

侦探方法论不是替代传统研究方法，而是在它们之上增加元分析层——五个"侦探动作"系统性地弥补这些盲区。

## 它做什么

三个 skill 协作：

```text
原始资料 → [research-archivist 入库] → wiki 知识库 → [research-detective 侦探分析] → 报告 + 侦探备忘录 → [research-reviewer 对抗审查] → review.md → [detective 修正] → 最终报告
```

### research-archivist（知识入库）

将原始研究资料增量入库为结构化 wiki 知识库（**LLM-as-Wiki** 方法论——把原始资料编译成 LLM 友好的结构化知识库，让分析直接在"编译好的知识"上工作，而不是每次重读原文）：

- LLM 逐份阅读原始资料（不是 Python 关键词匹配）
- 支持四种资料类型：定性访谈、定量问卷、文献、竞品（详见下文[支持的资料类型](#支持的资料类型)）
- 增量更新：新资料只处理新增，与已有 wiki 对照整合
- 入库时即时标记矛盾和异常

> **何时跳过 wiki**：资料量 ≤50 份时，可以不入库，直接让 detective 在 `data/` 上做证据采集。wiki 模式的优势在大数据量、多轮次、增量更新场景。

### research-detective（侦探分析）

在 wiki 知识库上执行五个侦探动作：

| 侦探动作 | 弥补的人类局限 |
| --- | --- |
| **全量记忆编码** | 人读到第 15 份时已忘了第 3 份的细节 |
| **盲区扫描** | 确认偏误让人忽略不符合预期的异常信号 |
| **全局关联发现** | 人脑无法处理 N×N 交叉比对 |
| **矛盾审计** | 人容易选择性忽略矛盾证据 |
| **证据链追溯** | 人对频率估计很不准 |

独有产出：**侦探备忘录**——专门呈现 AI 发现的、人类可能忽略的盲区信号、隐藏关联和矛盾。

### research-reviewer（对抗性审查）

对 detective 产出的报告做对抗性验证：

- 按"推翻则报告失效"的标准筛核心结论，每批 ≤ 3 条做深审；多课题/战略级报告分批审，不为覆盖广度牺牲对抗深度
- 判定每个结论：**confirmed**（经得起对抗）/ **weakened**（需加限定）/ **challenged**（可能是错的）
- 产出 `review.md`，detective 读取后修改被 weakened/challenged 的结论

### 侦探工具箱（26 个分析工具）

按需加载的专业分析工具，按四层组织：

- **采集层**（工具 1-4）：线索提取、证据分级、三角验证、采集纪律
- **结构层**（工具 5-19）：模式扫描、因果机制、JTBD、Kano、用户旅程、心智模型等
- **判断层**（工具 20-25）：ACH 竞争性假设、红队、Linchpin 检查、预验尸等
- **综合层**（工具 26）：证据综合

末尾有速查表，按课题类型（用户需求探索/竞品分析/设计验证/战略判断等）选择工具组合。

## 实测效果

在一个 250 份级别用户访谈 + 问卷规模的真实项目中验证过这套方法论。下列数字来自该项目，**案例已脱敏，原始数据未随仓库发布**，所以这些数字是说明性的，不是可独立复现的 benchmark：

- wiki 入库阶段在十分钟量级内处理完所有访谈，涌现出十几个主题、若干矛盾和未归类观察
- 侦探分析阶段在五分钟量级内产出战略对齐报告
- 一个典型的"语境修正"发现：某项功能被高频提及，但绝大多数提及是出现在隐私恐惧语境下——只看频率会得出错误结论，必须把语境读进去
- 一个典型的"矛盾审计"发现：自称"没有底线"的用户与同时表达隐私顾虑的用户高度重叠，真正无顾虑的人其实极少——直觉的人群划分与证据交叉后并不成立

这两类发现是侦探方法论本身想解决的问题（语境塌陷、矛盾选择性忽略），可以作为方法论价值的示例，而不应被读作"这个工具一定能稳定复现这些数字"。

## 安装

在 Claude Code 里把本仓库添加为 marketplace，再从该 marketplace 安装 plugin（本仓库同时充当 marketplace 和 plugin）：

```text
/plugin marketplace add myfmarco-arch/ai-research-detective
/plugin install ai-research-detective@ai-research-detective
```

> `@ai-research-detective` 是 marketplace 名,格式为 `<plugin>@<marketplace>`,不是写错。
>
> 也支持本地路径:`/plugin marketplace add /path/to/ai-research-detective`。
>
> marketplace 后续有更新时:`/plugin marketplace update ai-research-detective`。

本地开发/测试时，也可以直接把本目录链接到 Claude Code 的 plugin 目录：

```bash
ln -s "$(pwd)" ~/.claude/plugins/ai-research-detective
```

安装后，三个 skill（`research-archivist`、`research-detective`、`research-reviewer`）会自动被发现。Claude Code 用每个 skill 的 `description` 字段（写在各 SKILL.md 顶部 frontmatter）做触发匹配——所以"帮我把访谈入库"会激活 archivist、"分析一下用户访谈"会激活 detective、"审查这份报告"会激活 reviewer。也可以显式说 `加载 research-detective skill` 强制加载。

> 项目级 `CLAUDE.md`（研究产出质量底线）由各 skill 在冷启动时**自动从 plugin 内 `shared/CLAUDE.md` 复制到你的研究项目根**——不需要手动操作。

## 使用

### 第一步：入库

在研究项目目录下启动 Claude Code：

```bash
cd ~/my-research
claude
```

把资料放在当前目录（或 `data/` 子目录），然后说：

```text
帮我把访谈资料入库到 wiki
```

research-archivist skill 会自动激活，逐份阅读资料，建出 `wiki/` 知识库。

增量更新——有新资料时：

```text
有新的问卷数据，帮我更新 wiki
```

### 第二步：侦探分析

入库完成后：

```text
用 research-detective 分析 wiki 里的数据
```

或者带具体问题：

```text
加载 research-detective skill，分析用户对隐私的真实态度
```

research-detective 会检测到 `wiki/` 目录，跳过证据采集，直接在 wiki 上执行侦探分析。

### 第三步：对抗审查（可选但推荐）

分析报告产出后：

```text
用 research-reviewer 审查这份报告
```

reviewer 会按"推翻则报告失效"的标准筛核心结论（每批 ≤ 3 条，多课题报告分批审），主动搜索反面证据，产出 `outputs/review.md`。

然后让 detective 根据审查结果修正：

```text
根据 review.md 的审查结果修改报告
```

### 不用 wiki 也能跑

如果资料量小（≤50 份），可以跳过入库，直接用 research-detective：

```text
帮我分析 data/ 里的用户访谈
```

research-detective 会自己做证据采集和分析。wiki 模式的优势在大数据量和增量更新场景。

## 更新与维护

- **新增素材**：把新文件丢进 `data/`，说"更新 wiki"，archivist 走增量更新——只处理新增文件，与已有 wiki 对照（支持/矛盾/涌现/沉默信号四种处理），不动旧结论
- **健全性检查（入库回检）**：每次入库 / 增量更新后自动跑——抽 3 份原始资料对照 wiki，检查覆盖、来源可追溯、矛盾完整、未归类是否偷懒、统计与定性自洽。也可手动触发：`对当前 wiki 做一次入库回检`
- **空项目启动**：在空目录里说"帮我初始化研究项目"，archivist 跑冷启动生成 CONTEXT.md + wiki 骨架，然后提示你把资料放进 `data/`
- **wiki 持续生长**：detective 分析和 reviewer 审查产生的新涌现（新主题、新矛盾、新关联、被反驳的理论、被发现的盲区）会自动回写到 wiki，标注 `#analysis_YYYYMMDD` / `#review_YYYYMMDD` 来源——wiki 不是只在入库时变化

详细规则见 [skills/research-archivist/SKILL.md](skills/research-archivist/SKILL.md) 的步骤 5（入库回检）和「分析回写」一节。

## 支持的资料类型

| 类型 | 格式 | 处理方式 |
| --- | --- | --- |
| 定性访谈 | .md / .txt / .json | LLM 逐份阅读 |
| 定量问卷 | .csv / .xlsx | Python 统计 + LLM 解读 |
| 文献 | .md / .pdf | LLM 提取理论框架 |
| 竞品资料 | .md | LLM 提取能力矩阵 |

## 项目结构

```text
ai-research-detective/                   # 仓库根 = plugin 根
├── .claude-plugin/
│   ├── plugin.json                      # plugin 元信息（name / version / description）
│   └── marketplace.json                 # marketplace 清单（让仓库可被 /plugin marketplace add 识别）
├── README.md                            # 本文档
├── LICENSE
├── shared/                              # 三个 skill 共用资源（不是 skill）
│   ├── CLAUDE.md                        # 项目级硬约束（冷启动时由 skill 自动复制到研究项目根）
│   ├── cold_start.md                    # 冷启动流程（生成 CONTEXT/README + 配置 CLAUDE.md）
│   └── templates/
│       ├── CONTEXT.md                   # 项目语境模板（speed card + 输出契约）
│       └── README.md                    # 项目档案模板（材料地图 + 方法档案）
└── skills/                              # Claude Code 自动发现的 skill 目录
    ├── research-archivist/
    │   └── SKILL.md                     # 入库工作流
    ├── research-detective/
    │   ├── SKILL.md                     # 侦探分析工作流
    │   ├── guides/
    │   │   ├── research_methodology.md  # 五个侦探动作的执行细节、置信度标准、备忘录格式
    │   │   ├── detective_toolkit.md     # 26 个分析工具（按需加载，末尾有速查表）
    │   │   ├── report_principles.md     # 报告结构与论证质量规范 + 13 项自检清单
    │   │   └── writing_style.md         # 写作风格红线/黄线（去 AI 味、堵套路句式）
    │   └── templates/
    │       ├── simple_report.md         # 研究报告模板
    │       ├── answer_summary.md        # A1 回答/摘要模板
    │       └── evidence_chain.md        # A2 证据链图谱模板
    └── research-reviewer/
        └── SKILL.md                     # 对抗性审查工作流
```

> SKILL.md 内用 `../../shared/...` 从 `skills/<skill-name>/SKILL.md` 上溯两级（先到 `skills/`，再到 plugin 根）后进入 `shared/`，访问共用资源。

## 提示

- 首次使用建议先说 `加载 research-archivist skill` 或 `加载 research-detective skill`，确保 skill 在分析开始前就被加载
- 如果 Claude 没有停下来问你研究问题就直接开始分析，提醒它："先问我研究问题是什么"
- 分析完成后检查 `process/` 目录是否有中间产物（evidence_extraction.md、detective_analysis.md）

## License

MIT
