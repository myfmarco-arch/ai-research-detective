# AI Research Detective 🔍

[English](README_en.md) · **中文**

基于**侦探方法论（Detective Method）**的 AI 研究分析工具。利用 LLM 的完美记忆和无偏差全局扫描能力，在定性定量分析的基础上做人类研究员做不到的元分析。

A research analysis toolkit powered by the **Detective Method** — a meta-analysis paradigm that leverages LLM's perfect memory and unbiased global scanning to complement human researchers' cognitive limitations.

本仓库是一个 [**Claude Code plugin**](https://docs.claude.com/en/docs/claude-code/plugins)（Claude Code 的扩展机制，把多个协作的 skill 打包成可一键安装的工具集）。

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

## 实测效果

在一个 250 份级别用户访谈 + 问卷的真实项目中验证过。**案例已脱敏，原始数据未发布**——下列是说明性发现，不是可独立复现的 benchmark：

- **语境修正**：某项功能被高频提及，但绝大多数提及出现在隐私恐惧语境下——只看频率会得出错误结论
- **矛盾审计**：自称"没有底线"的用户与同时表达隐私顾虑的用户高度重叠，真正无顾虑的人极少——直觉的人群划分与证据交叉后并不成立

这两类发现正是侦探方法论想解决的问题（语境塌陷、矛盾选择性忽略）。

## 它做什么

三个 skill 协作：

```text
原始资料
   │
   ▼
[research-archivist 入库] ──► wiki 知识库
                                 │
                                 ▼
                       [research-detective 侦探分析]
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
     ① 简报形态(针对具体问题)            ② 完整研究报告
        A1 一页摘要                        + 侦探备忘录
        A2 证据链图谱                          │
        B1 信息包(可选,给下游 AI)                 ▼
                                  [research-reviewer 对抗审查](按需)
                                                  │
                                                  ▼
                                  review.md → [detective 修正] → 最终交付
```

- **research-archivist**：把原始资料增量入库为结构化 wiki 知识库（**LLM_wiki** 方法论：让分析直接在"编译好的知识"上工作，而不是每次重读原文；wiki 随每次分析持续生长）。资料量 ≤50 份可跳过。
- **research-detective**：在 wiki（或 `data/`）上执行五个侦探动作——全量记忆编码、盲区扫描、全局关联发现、矛盾审计、证据链追溯。产出二选一：① 简报（A1+A2，可选 B1）；② 完整报告 + 侦探备忘录。
- **research-reviewer**：对完整报告做对抗性验证，按"推翻则报告失效"的标准筛核心结论，判定 confirmed / weakened / challenged，detective 据此修订。

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

安装后，三个 skill 会被 Claude Code 自动发现，通过描述匹配触发——"帮我把访谈入库"激活 archivist、"分析一下用户访谈"激活 detective、"审查这份报告"激活 reviewer。也可显式说 `加载 research-detective skill` 强制加载。

> 项目级 `CLAUDE.md`（研究产出质量底线）由各 skill 在冷启动时**自动从 plugin 内 `shared/CLAUDE.md` 复制到你的研究项目根**——不需要手动操作。

## 使用

### 第一步：入库

```bash
cd ~/my-research
claude
```

把资料放在当前目录或 `data/` 子目录，然后说：

```text
帮我把访谈资料入库到 wiki
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

资料量 ≤50 份时可以跳过入库：`帮我分析 data/ 里的用户访谈`——detective 会自己做证据采集和分析。wiki 模式的优势在大数据量、增量更新场景。

## 支持的资料类型

| 类型 | 格式 | 处理方式 |
| --- | --- | --- |
| 定性访谈 | .md / .txt / .json | LLM 逐份阅读 |
| 定量问卷 | .csv / .xlsx | Python 统计 + LLM 解读 |
| 文献 | .md / .pdf | LLM 提取理论框架 |
| 竞品资料 | .md | LLM 提取能力矩阵 |

## 深入特性

下面四节按价值优先级排列，描述本工具的核心设计选择。

### 1. LLM_wiki：可持续生长的知识库

> 本节实现了 Andrej Karpathy 提出的 [LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 在研究分析场景的特化——把 LLM 当成"编译器"，把原始资料编译成结构化、可持续维护的 markdown 知识库，而非每次重读原文。本工具基于这个模式做了研究方法论层的延伸（侦探动作 + 对抗审查回写 + 资料/解读分栏）。

archivist 入库阶段让 LLM 逐份读完资料，把原始内容**编译成结构化的 markdown wiki**——主题页、矛盾记录、用户原声、统计、文献框架等。后续 detective 分析直接在这份"已编译知识"上工作，不需要回到原文。

**核心特性是"持续生长"**——wiki 不是一次性入库的死产物：

- 每次 detective 分析中**涌现的新主题、新矛盾、新关联、新盲区**自动回写 wiki，标 `#analysis_YYYYMMDD` 来源
- 每次 reviewer 审查中**找到的反例、被反驳的理论、覆盖盲区**自动回写 wiki，标 `#review_YYYYMMDD` 来源
- 一手资料引用（`#interview_xx`）和分析涌现（`#analysis_xx`）严格分栏，**事实和解读永远可区分**
- 第二次分析站在第一次的肩膀上，不是从零开始；半年后接手项目的研究员看 wiki 能复盘所有判断的演化

设计选择：

- **编译产物是 markdown 而非 embedding 向量**——研究员可读、可审、可手工编辑修正
- **回写只追加不覆盖**——即使发现原结论错了，也是另开一条 `#analysis_xx 修正:...`，保留旧条目让判断演化轨迹可见

资料/分析格式契约见 [contracts/wiki_format.md](contracts/wiki_format.md)，回写规则见 [contracts/analysis_writeback.md](contracts/analysis_writeback.md)。

### 2. 侦探工具箱（26 个分析工具）

按需加载的专业分析工具，按四层组织：

- **采集层**：线索提取、证据分级、三角验证、采集纪律
- **结构层**：模式扫描、因果机制、JTBD、Kano、用户旅程、心智模型等
- **判断层**：ACH 竞争性假设、红队、Linchpin 检查、预验尸等
- **综合层**：证据综合

每个工具都带使用场景和操作步骤——detective 不是"通用分析助手"，而是"按方法论选工具、按证据强度下判断"。详见 [detective_toolkit.md](skills/research-detective/guides/detective_toolkit.md) 末尾速查表。

### 3. 质量保障：对抗审查 + 写作风格约束

研究产出的质量靠两层独立机制保障——论证层和写作层。

**对抗性审查**（论证层 · 由 research-reviewer 独立执行）

针对完整研究报告，扮演"事实核查员"角色：

- 按"**推翻则报告失效**"的标准筛核心结论（每批 ≤3 条做深审，多课题报告分批审）
- 不只是读现有报告，**主动搜反面证据**——读 wiki 的矛盾页、未归类页、quotes，回到原始资料抽查
- 判定每条结论：**confirmed**（经得起对抗）/ **weakened**（需加限定条件）/ **challenged**（可能是错的）
- detective 据此修订结论，被弱化或推翻的判断回写到 wiki 的「分析增量」栏，标 `#review_YYYYMMDD`，**保留判断演化轨迹**

简报形态（A1+A2）目前不进入 reviewer。报告形态在对外发布、决策依据、证据强度有疑时强烈推荐跑。

**写作风格约束**（写作层 · 落笔前后自检）

研究员落笔前后对照 [writing_style.md](skills/research-detective/guides/writing_style.md) + [report_principles.md](skills/research-detective/guides/report_principles.md) 自检，堵 AI 写作的典型套路（概念癌、稻草人、春秋笔法、章末金句等）以及定量纪律。机器可查的部分由脚本自动跑兜底，结构性问题仍需人工对照清单。

### 4. B1 信息包：AI-to-AI 决策上下文交付

研究产出会被下游 AI 工作流消费——产品 AI 写 PRD、设计 AI 出方案、战略 AI 做规划。B1 信息包是为这个交付环节设计的结构化封包：

- 不是原始素材，而是研究员把素材提取成**决策切片**——用户分群 / 痛点清单 / 设计约束 / 场景成功状态。下游 AI 直接拿去用，不用自己再做"原始证据→行动种子"的转换
- 带**负面清单**和**未解决问题**做护栏——明确告诉下游 AI 哪些结论不能外推、哪些领域研究没覆盖
- 带 **AI 操作协议**——所有引用要带 ID、跨 ID 完整性可机器校验

简报或报告完成后按需触发，研究员通过对话指令打包。生成时**自动跑 B1 结构 lint** 兜底（占位符无残留 / 跨 ID 引用都对得上 / 必填章节非空）。完整契约见 [contracts/information_pack.md](contracts/information_pack.md)。

## 运维与排错

**日常运维**：

- **新增素材**：把新文件丢进 `data/`，说"更新 wiki"，archivist 走增量更新（只处理新增，不动旧结论）
- **入库回检**：每次入库后自动跑——抽 3 份原始资料对照 wiki，检查覆盖、可追溯、矛盾完整。也可手动触发：`对当前 wiki 做一次入库回检`
- **空项目启动**：`帮我初始化研究项目` → archivist 跑冷启动生成 CONTEXT.md + wiki 骨架

**常见问题**：

- 首次使用建议先显式 `加载 research-archivist skill` 或 `加载 research-detective skill`，确保 skill 在分析开始前被加载
- 如果 Claude 没有停下来问研究问题就直接开始分析，提醒它："先问我研究问题是什么"
- 分析完成后检查 `process/` 下五个侦探动作产物齐备:`3a_coding.md` / `3b_blind_spots.md` / `3c_associations.md` / `3d_contradictions_audit.md` / `3e_evidence_chains.md`（wiki 模式 3a 可省）。也可以直接跑 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/research-detective/scripts/lint_process.py process/` 让脚本一次性检查

## 项目结构

```text
ai-research-detective/                   # 仓库根 = plugin 根
├── .claude-plugin/                      # plugin 元信息（plugin.json + marketplace.json）
├── README.md / README_en.md / LICENSE
├── contracts/                           # 跨 skill / 跨边界共享契约
│   ├── wiki_format.md                   # wiki 页面格式
│   ├── analysis_writeback.md            # 分析回写规则
│   └── information_pack.md              # B1 信息包契约
├── shared/                              # 三个 skill 共用资源（不是 skill）
│   ├── CLAUDE.md                        # 项目级硬约束
│   ├── cold_start.md                    # 冷启动流程
│   ├── templates/                       # CONTEXT.md / README.md 模板
│   └── scripts/                         # 跨 skill lint(lint_context.py) + tests
└── skills/                              # Claude Code 自动发现的 skill
    ├── research-archivist/
    │   ├── SKILL.md
    │   └── scripts/                     # verify_quotes.py（wiki 引用全量校验）+ tests
    ├── research-detective/
    │   ├── SKILL.md                     # 通用流程 + 步骤 4 路由到 workflow
    │   ├── workflows/                   # brief / report 两条产出工作流
    │   ├── guides/                      # 侦探方法论 + 26 工具箱 + 写作规范
    │   ├── templates/                   # 报告 / A1 / A2 / B1 模板
    │   └── scripts/                     # lint_report / lint_information_pack / lint_process + tests
    └── research-reviewer/
        ├── SKILL.md
        └── scripts/                     # lint_review.py（搜索记录 + 证据强度复核 + 采样模式）+ tests
```

> **shared/ vs contracts/**：`shared/` 是流程资源（模板、起手式），用户复制后会改；`contracts/` 是接口规范（跨 skill / 跨边界的协议），所有 skill 共同遵守不能各自改。
>
> SKILL.md 内用 `../../shared/...` 或 `../../contracts/...` 上溯两级访问。

## Roadmap

**跨项目知识图谱**：当前架构是单项目闭环。多个项目间反复出现的底层机制（掌控感、确定性、身份认同等）每次都要重新发现。下一步：自动提取底层机制关键词到全局索引，让新项目站在历史项目的肩膀上启动。

<!-- 远期：基于跨项目索引做组织遗忘检测——当前发现与历史结论不一致时自动提醒 -->

## 反馈与贡献

欢迎在 [GitHub Issues](https://github.com/myfmarco-arch/ai-research-detective/issues) 反馈问题、提建议、贡献代码。贡献流程、测试方法、版本规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。当前版本见 `.claude-plugin/plugin.json`。

## Acknowledgements

- **LLM Wiki 模式**——本工具的入库 + 分析架构基于 Andrej Karpathy 的 [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)：把 LLM 当成"编译器"、维护可持续生长的 markdown 知识库。本工具在此基础上做了研究方法论层的特化（侦探动作、对抗审查、B1 信息包、资料/解读严格分栏）。
- **写作风格 lint** 中的英文 AI 套路检测部分参考了 [blader/humanizer](https://github.com/blader/humanizer) 的 patterns（基于 Wikipedia "Signs of AI writing"），中文研究报告专用规则为本项目原创。

## License

MIT
