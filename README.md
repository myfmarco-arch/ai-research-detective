# AI Research Detective 🔍

[English](README_en.md) · **中文**

AI Research Detective 是一套面向研究材料的 Claude Code skills：把访谈、问卷、用户反馈、舆情、文献和竞品资料转成可追溯的研究结论、证据链和报告。

它的核心不是“总结材料”，而是用**侦探方法论（Detective Method）**系统寻找盲区、矛盾、低频高强度信号和反证，让研究判断既有洞察，也有证据边界。

本仓库是一个 [**Claude Code plugin**](https://docs.claude.com/en/docs/claude-code/plugins)：Claude Code 的扩展机制，把多个协作的 skill 打包成可安装的研究工具箱。

---

## 为什么需要它

研究员最大的瓶颈不是方法论——访谈分析、问卷统计、竞品对比这些方法已经很成熟。瓶颈是执行方法的人：

| 人的认知局限 | 后果 |
| --- | --- |
| 记忆衰退 | 读到第 15 份时已忘了第 3 份的细节 |
| 确认偏误 | 忽略不符合预期的异常信号 |
| 模式识别天花板 | 无法处理 20 份材料的 N×N 交叉关联 |
| 频率估计不准 | "感觉有几个人提到过"的直觉很不可靠 |

侦探方法论保留传统研究方法，在它们之上增加元分析层。五个"侦探动作"系统性地弥补这些盲区。


## 什么时候用它

适合用于：

- 有多源研究材料：访谈、问卷开放题、用户反馈、舆情、文献、竞品资料等。
- 需要形成可用于产品、设计、战略或对外汇报的研究结论。
- 担心普通 AI 总结漏掉少数派信号、矛盾证据、样本边界或反例。
- 资料会持续新增，需要后续复用、追溯和增量分析。

不适合用于：

- 只想快速读 1-3 份材料并随口聊聊。
- 没有研究问题，只想让 AI 自由发挥。
- 只需要润色已有报告，或只做格式调整。

## 核心创新

本工具不是把访谈、问卷、舆情、反馈、文献或竞品材料交给 AI 做通用总结，而是把研究过程拆成可检查的侦探机制：

| 创新点 | 解决什么问题 | 显性产物 / 机制 |
| --- | --- | --- |
| **侦探方法论** | 普通主题总结容易漏掉盲区、矛盾和异常值 | 五个侦探动作 + 侦探备忘录 |
| **26 个工具箱** | 不同课题需要不同分析框架，不能一套模板打天下 | 分析前先选工具，记录 `process/0_method_selection.md` |
| **LLM_wiki** | 大量资料无法每次重读，也难以追踪判断演化 | 可持续生长的 markdown wiki |
| **对抗审查闭环** | 结论听起来合理，但可能被反证推翻 | reviewer 找反证 → detective 修正 → wiki 回写 |
| **证据链图谱** | 结论和证据之间经常断裂 | 每个核心结论保留支持、反对、置信度和边界 |
| **AI 接力包** | 下游 AI 容易误用研究结论或越界外推 | 带 ID、负面清单、未解决问题的结构化交接包 |

五个侦探动作是正式分析的最小闭环：

| 侦探动作 | 作用 |
| --- | --- |
| **全量记忆编码** | 防止读到后面忘了前面，保留跨材料对照基础 |
| **盲区扫描** | 找没人提、低频但高风险、应出现却缺失的信号 |
| **全局关联发现** | 找跨材料、跨人群、跨数据源的隐藏联系 |
| **矛盾审计** | 找口头 vs 行为、来源之间、结论与证据之间的冲突 |
| **证据链追溯** | 给每个结论标支持证据、反面证据、置信度和边界 |

## 它能发现什么

在一个 250 份级别用户访谈 + 问卷的真实项目中验证过。**案例已脱敏，原始数据未发布**——下列是说明性发现，不是可独立复现的 benchmark：

- **语境修正**：某项功能被高频提及，但绝大多数提及出现在隐私恐惧语境下。只看频率会得出错误结论
- **矛盾审计**：自称"没有底线"的用户与同时表达隐私顾虑的用户高度重叠，真正无顾虑的人极少。直觉的人群划分与证据交叉后并不成立

这两类发现正是侦探方法论想解决的问题（语境塌陷、矛盾选择性忽略）。

## 它做什么

三个 skill 协作：

```text
原始资料
  ↓
research-archivist
  → wiki 知识库：主题、引用、矛盾、统计、未归类观察
  ↓
research-detective
  → 研究简报 / 深度分析报告 / 证据链图谱 / 侦探备忘录
  → 可选：AI 接力包（给下游 AI）
  ↓
research-reviewer（可选）
  → 反证审查与结论修正
```

- **research-archivist**：把原始资料增量入库为结构化 wiki 知识库（**LLM_wiki** 方法论：让分析直接在"编译好的知识"上工作，而不是每次重读原文；wiki 随每次分析持续生长）。少量一次性材料可跳过 wiki；资料会持续新增、需要复用或需要严格追溯时，建议先入库。
- **research-detective**：在 wiki（或 `data/`）上执行五个侦探动作——全量记忆编码、盲区扫描、全局关联发现、矛盾审计、证据链追溯。产出二选一：① 研究简报 + 证据链图谱（可选 AI 接力包）；② 深度分析报告 + 侦探备忘录 + 证据链图谱（可选 AI 接力包）。
- **research-reviewer**：对深度分析报告做对抗性验证，按"推翻则报告失效"的标准筛核心结论，判定 confirmed / weakened / challenged，detective 据此修订。

## 安装

在 Claude Code 里把本仓库添加为 marketplace，再从该 marketplace 安装 plugin（本仓库同时充当 marketplace 和 plugin）：

```text
/plugin marketplace add myfmarco-arch/ai-research-detective
/plugin install ai-research-detective@ai-research-detective
```

> `@ai-research-detective` 是 marketplace 名，格式 `<plugin>@<marketplace>`。
>
> 也支持本地路径：`/plugin marketplace add /path/to/ai-research-detective`。
>
> 后续更新：`/plugin marketplace update ai-research-detective`。

本地开发可直接软链接：

```bash
ln -s "$(pwd)" ~/.claude/plugins/ai-research-detective
```

安装后，三个 skill 会被 Claude Code 自动发现，通过描述匹配触发——"帮我把访谈/问卷/舆情入库"激活 archivist、"分析一下用户反馈和问卷"激活 detective、"审查这份报告"激活 reviewer。也可显式说 `加载 research-detective skill` 强制加载。

> 项目级 `CLAUDE.md`（简洁操作原则与研究规则）由各 skill 在冷启动时引导配置：Claude 会先说明将从 plugin 内 `shared/CLAUDE.md` 复制或追加到研究项目根，得到用户确认后再写入。

## 使用

### 第一步：入库

```bash
cd ~/my-research
claude
```

把资料放在当前目录或 `data/` 子目录，然后说：

```text
帮我把访谈、问卷和舆情资料入库到 wiki
```

archivist 会自动激活，逐份阅读资料，建出 `wiki/`。后续新资料：`有新的问卷数据，帮我更新 wiki`——走增量更新。

### 第二步：侦探分析

入库完成后：

```text
用 research-detective 分析 wiki 里的数据
```

或者带具体问题：

```text
加载 research-detective skill，分析用户对隐私的真实态度
```

detective 检测到 `wiki/` 后跳过证据采集，直接做侦探分析。

### 第三步：对抗审查（可选但推荐）

报告产出后：

```text
用 research-reviewer 审查这份报告
```

reviewer 主动搜反面证据，产出 `outputs/review.md`，然后让 detective 修正：`根据 review.md 的审查结果修改报告`。

### 不用 wiki 也能跑

少量一次性材料可以跳过入库：`帮我分析 data/ 里的访谈、问卷和用户反馈`——detective 会自己做证据采集和分析。资料会持续新增、需要复用或需要严格追溯时，建议先走 wiki 模式。

## 支持的资料类型

| 资料类型 | 示例 | 处理方式 |
| --- | --- | --- |
| 定性材料 | 访谈、可用性测试、开放题、客服记录 | 逐份阅读，提取观察、引用、痛点、矛盾和情绪强度 |
| 定量材料 | 问卷、评分、行为 CSV | 统计分布、分群差异、交叉验证 |
| 公开信号 | 舆情、评论、社媒、论坛 | 聚合模式，标注来源、时效和样本边界 |
| 文献与理论 | 论文、行业报告、理论文章 | 提取解释框架和可验证预测 |
| 竞品资料 | 功能对比、竞品反馈、市场资料 | 提取能力矩阵、行业基线和差异化 |

## 深入特性

下面四节按价值优先级排列，描述本工具的核心设计选择。

### 1. LLM_wiki：可持续生长的知识库

archivist 会把原始资料编译成 markdown wiki：主题页、引用库、矛盾记录、统计、未归类观察、文献框架和竞品基准。后续分析直接在这份“已编译知识”上工作，不需要每次从头重读原文。

关键设计：

- **持续生长**：每次 detective 分析和 reviewer 审查产生的新主题、新矛盾、新关联、新反例都会追加回 wiki。
- **事实 / 解读分栏**：一手资料引用和 AI 分析增量严格分开，读者能看清哪些是原始证据，哪些是后续判断。
- **只追加不覆盖**：即使发现旧判断错了，也保留原记录并追加修正，方便复盘判断如何演化。
- **覆盖深度可查**：入库后用 `verify_quotes.py` 查引用真实性，用 `lint_source_coverage.py` 查逐份资料是否只浅摘了几个亮点。

格式契约见 [contracts/wiki_format.md](contracts/wiki_format.md)，回写规则见 [contracts/analysis_writeback.md](contracts/analysis_writeback.md)。

### 2. 侦探工具箱（26 个分析工具）

正式分析前，detective 会先判断课题类型，再从工具箱选择方法组合，并记录到 `process/0_method_selection.md`。这让“用了什么方法、为什么不用其他方法”可检查，而不是只靠一句“我做了深度分析”。

工具按四层组织：

- **采集层**：线索提取、证据分级、三角验证、采集纪律
- **结构层**：模式扫描、因果机制、JTBD、Kano、用户旅程、心智模型等
- **判断层**：ACH 竞争性假设、红队、Linchpin 检查、预验尸等
- **综合层**：证据综合

常见组合示例：

| 场景 | 可能选用的工具 |
| --- | --- |
| 用户需求探索 | 线索提取 + 证据分级 + JTBD + Kano + Linchpin |
| 体验优化 | 用户旅程 + 心智模型 + 5 Whys + 反证审查 |
| 竞品分析 | 模式扫描 + 知识图谱 + 拓扑直觉 + 价值主张画布 |
| 战略判断 | 知识图谱 + 拓扑直觉 + ACH + 情景规划 |

完整工具说明见 [detective_toolkit.md](skills/research-detective/guides/detective_toolkit.md)，方法入口见 [method_index.md](skills/research-detective/guides/method_index.md)。

### 3. 质量保障：对抗审查 + 写作风格约束

研究产出的质量靠两层独立机制保障——论证层和写作层。

**对抗性审查**（论证层 · 由 research-reviewer 独立执行）

针对深度分析报告，扮演"事实核查员"角色：

- 按"**推翻则报告失效**"的标准筛核心结论（每批 ≤3 条做深审，多课题报告分批审）
- 不只是读现有报告，**主动搜反面证据**——读 wiki 的矛盾页、未归类页、quotes，回到原始资料抽查
- 判定每条结论：confirmed（经得起对抗）/ weakened（需加限定条件）/ challenged（可能是错的）
- detective 据此修订结论。弱化或推翻判断时，在 wiki 的「分析增量」栏追加 `#review_YYYYMMDD`，**保留判断演化轨迹**

研究简报形态（研究简报 + 证据链图谱）目前不进入 reviewer。深度分析报告形态在对外发布、决策依据、证据强度有疑时强烈推荐跑。

**写作风格约束**（写作层 · 落笔前后自检）

研究员落笔前后对照 [writing_style.md](skills/research-detective/guides/writing_style.md) + [report_principles.md](skills/research-detective/guides/report_principles.md) 自检，堵 AI 写作的典型套路（概念癌、稻草人、春秋笔法、章末金句等）以及定量纪律。机器可查的部分由脚本自动跑兜底，论证和结构问题仍需人工对照清单。

### 4. AI 接力包：AI-to-AI 决策上下文交付

研究产出会被下游 AI 工作流消费——产品 AI 写 PRD、设计 AI 出方案、战略 AI 做规划。AI 接力包是为这个交付环节设计的结构化封包：

- 研究员把素材提取成**决策切片**：用户分群 / 痛点清单 / 设计约束 / 场景成功状态。下游 AI 直接拿去用，不用自己再做"原始证据→行动种子"的转换
- 带**负面清单**和**未解决问题**做护栏：明确告诉下游 AI 哪些结论不能外推、哪些领域研究没覆盖
- 带 AI 操作协议：所有引用要带 ID、跨 ID 完整性可机器校验

研究简报或深度分析报告完成后按需触发，研究员通过对话指令打包。生成时**自动跑 AI 接力包结构 lint** 兜底（占位符无残留 / 跨 ID 引用都对得上 / 必填章节非空）。完整契约见 [contracts/information_pack.md](contracts/information_pack.md)。

## 质量检查与排错

日常使用只需要知道三件事：

- **入库后会检查材料是否读深**：引用必须能回到原文，逐份资料也要有覆盖台账，避免只摘几个亮点。
- **分析后会检查侦探动作是否完成**：方法选择、盲区扫描、全局关联、矛盾审计和证据链都要留下中间产物。
- **报告前会检查写作和证据链**：机器先扫明显问题，研究员再判断结论是否越界。

需要手动排查时：

- **新增素材**：把新文件丢进 `data/`，说“更新 wiki”，archivist 走增量更新（只处理新增，不动旧结论）。
- **入库回检**：可手动说“对当前 wiki 做一次入库回检”。它会运行 `verify_quotes.py` 和 `lint_source_coverage.py`，并抽查原始资料。
- **分析过程检查**：查看 `process/0_method_selection.md` 和 `process/3a-3e` 是否齐备；也可运行 `python3 ${CLAUDE_SKILL_DIR}/scripts/lint_process.py process/`。
- **首次使用异常**：如果 Claude 没有停下来问研究问题就直接开始分析，提醒它：“先问我研究问题是什么”。
- **空项目启动**：说“帮我初始化研究项目”，archivist 会跑冷启动生成 `CONTEXT.md` 和基础目录。

## 项目结构

```text
ai-research-detective/                   # 仓库根 = plugin 根
├── .claude-plugin/                      # plugin 元信息（plugin.json + marketplace.json）
├── README.md / README_en.md / LICENSE
├── contracts/                           # 跨 skill / 跨边界共享契约
│   ├── wiki_format.md                   # wiki 页面格式
│   ├── analysis_writeback.md            # 分析回写规则
│   └── information_pack.md              # AI 接力包契约
├── shared/                              # 三个 skill 共用资源（不是 skill）
│   ├── CLAUDE.md                        # 项目级硬约束
│   ├── cold_start.md                    # 冷启动流程
│   ├── templates/                       # CONTEXT.md / README.md 模板
│   └── scripts/                         # 跨 skill lint(lint_context.py) + tests
└── skills/                              # Claude Code 自动发现的 skill
    ├── research-archivist/
    │   ├── SKILL.md
    │   └── scripts/                     # verify_quotes.py（引用校验）/ lint_source_coverage.py（覆盖深度）+ tests
    ├── research-detective/
    │   ├── SKILL.md                     # 通用流程 + 步骤 4 路由到 workflow
    │   ├── workflows/                   # brief / report 两条产出工作流
    │   ├── guides/                      # 方法入口 + 侦探方法论 + 26 工具箱 + 写作规范
    │   ├── templates/                   # 报告 / 研究简报 / 证据链图谱 / AI 接力包模板
    │   └── scripts/                     # lint_report / lint_information_pack / lint_process + tests
    └── research-reviewer/
        ├── SKILL.md
        └── scripts/                     # lint_review.py（搜索记录 + 证据强度复核 + 采样模式）+ tests
```

> **shared/ vs contracts/**：`shared/` 是流程资源（模板、起手式），用户复制后会改；`contracts/` 是接口规范（跨 skill / 跨边界的协议），所有 skill 共同遵守不能各自改。
>
> SKILL.md 内用 `../../shared/...` 或 `../../contracts/...` 上溯两级访问。

## Roadmap

**跨项目知识图谱**：当前架构是单项目闭环。掌控感、确定性、身份认同等跨项目反复出现，但每个新项目仍要重新发现。下一步：自动提取这些机制关键词到全局索引，让新项目站在历史项目的肩膀上启动。

<!-- 远期：基于跨项目索引做组织遗忘检测——当前发现与历史结论不一致时自动提醒 -->

## 反馈与贡献

欢迎在 [GitHub Issues](https://github.com/myfmarco-arch/ai-research-detective/issues) 反馈问题、提建议、贡献代码。贡献流程、测试方法、版本规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。当前版本见 `.claude-plugin/plugin.json`。

## Acknowledgements

- **LLM Wiki 模式**——本工具的入库 + 分析架构基于 Andrej Karpathy 的 [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：把 LLM 当成"编译器"、维护可持续生长的 markdown 知识库。本工具在此基础上做了研究方法论层的特化（侦探动作、对抗审查、AI 接力包、资料/解读严格分栏）。
- **写作风格 lint** 中的英文 AI 套路检测部分参考了 [blader/humanizer](https://github.com/blader/humanizer) 的 patterns（基于 Wikipedia "Signs of AI writing"），中文研究报告专用规则为本项目原创。

## License

MIT
