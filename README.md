# AI Research Detective 🔍

基于**侦探方法论（Detective Method）**的 AI 研究分析工具。利用 LLM 的完美记忆和无偏差全局扫描能力，在定性定量分析的基础上做人类研究员做不到的元分析。

A research analysis toolkit powered by the **Detective Method** — a meta-analysis paradigm that leverages LLM's perfect memory and unbiased global scanning to complement human researchers' cognitive limitations.

---

## 为什么需要它

研究员最大的瓶颈不是方法论——访谈分析、问卷统计、竞品对比这些方法已经很成熟。瓶颈是执行方法的人：

| 人的认知局限 | 后果 |
|-------------|------|
| 记忆衰退 | 读到第 15 份时已忘了第 3 份的细节 |
| 确认偏误 | 忽略不符合预期的异常信号 |
| 模式识别天花板 | 无法处理 20 份材料的 N×N 交叉关联 |
| 频率估计不准 | "感觉有几个人提到过"的直觉很不可靠 |

侦探方法论不是替代传统研究方法，而是在它们之上增加元分析层——五个"侦探动作"系统性地弥补这些盲区。

## 它做什么

三个 skill 协作：

```
原始资料 → [research-wiki 入库] → wiki 知识库 → [research-expert 侦探分析] → 报告 + 侦探备忘录 → [research-reviewer 对抗审查] → review.md → [expert 修正] → 最终报告
```

### research-wiki（知识入库）

将原始研究资料增量入库为结构化 wiki 知识库：
- LLM 逐份阅读原始资料（不是 Python 关键词匹配）
- 支持四种资料类型：定性访谈、定量问卷、文献、竞品
- 增量更新：新资料只处理新增，与已有 wiki 对照整合
- 入库时即时标记矛盾和异常

### research-expert（侦探分析）

在 wiki 知识库上执行五个侦探动作：

| 侦探动作 | 弥补的人类局限 |
|----------|---------------|
| **全量记忆编码** | 人读到第 15 份时已忘了第 3 份的细节 |
| **盲区扫描** | 确认偏误让人忽略不符合预期的异常信号 |
| **全局关联发现** | 人脑无法处理 N×N 交叉比对 |
| **矛盾审计** | 人容易选择性忽略矛盾证据 |
| **证据链追溯** | 人对频率估计很不准 |

独有产出：**侦探备忘录**——专门呈现 AI 发现的、人类可能忽略的盲区信号、隐藏关联和矛盾。

### research-reviewer（对抗性审查）

对 expert 产出的报告做对抗性验证：
- 提取 2-3 个核心结论，主动搜索反面证据尝试推翻
- 判定每个结论：**confirmed**（经得起对抗）/ **weakened**（需加限定）/ **challenged**（可能是错的）
- 产出 `review.md`，expert 读取后修改被 weakened/challenged 的结论

### 侦探工具箱（26 个分析工具）

按需加载的专业分析工具，按四层组织：
- **采集层**（工具 1-4）：线索提取、证据分级、三角验证、采集纪律
- **结构层**（工具 5-19）：模式扫描、因果机制、JTBD、Kano、用户旅程、心智模型等
- **判断层**（工具 20-25）：ACH 竞争性假设、红队、Linchpin 检查、预验尸等
- **综合层**（工具 26）：证据综合

末尾有速查表，按课题类型（用户需求探索/竞品分析/设计验证/战略判断等）选择工具组合。

## 实测效果

在 251 份用户访谈 + 188 份问卷的真实项目中验证：

- wiki 入库 10 分钟处理 251 份访谈，涌现 13 个主题、5 条矛盾、8 条未归类观察
- 侦探分析 5 分钟产出战略对齐报告
- 发现"来电识别 25.9% 提及率是假象，80%+ 出现在隐私恐惧语境"——只有理解语境才能做到
- 发现"没有底线的人其实都有底线"——108 人说没底线，但 33 人同时有隐私顾虑，仅 2 人真正无顾虑

## 支持平台

| 平台 | 目录 | 安装方式 |
|------|------|---------|
| Claude Code | `claude-code/` | 复制到 `~/.claude/skills/` |
| Kiro | `kiro/` | 用 Kiro 打开 `kiro/` 目录 |

## 快速开始

### Claude Code

```bash
# 安装 skills
cp -r claude-code/research-wiki ~/.claude/skills/research-wiki
cp -r claude-code/research-expert ~/.claude/skills/research-expert
cp -r claude-code/research-reviewer ~/.claude/skills/research-reviewer

# 在研究项目目录下
cd ~/my-research
# 把资料放进当前目录，然后：
claude
> 帮我把访谈资料入库到 wiki
# 入库完成后：
> 用 research-expert 分析 wiki 里的数据
```

### Kiro

用 Kiro 打开 `kiro/` 目录，在聊天中通过 `#` 选择 `research-expert` steering，然后放研究资料进去开始分析。

## 项目结构

```
ai-research-detective/
├── README.md
├── LICENSE
├── claude-code/
│   ├── research-wiki/
│   │   └── SKILL.md
│   ├── research-expert/
│   │   ├── SKILL.md
│   │   ├── guides/
│   │   │   ├── research_methodology.md
│   │   │   └── detective_toolkit.md
│   │   ├── templates/
│   │   │   ├── simple_report.md
│   │   │   ├── answer_summary.md
│   │   │   └── evidence_chain.md
│   │   └── config/
│   │       ├── default.json
│   │       └── advanced.json
│   └── research-reviewer/
│       └── SKILL.md
└── kiro/
    ├── .kiro/steering/
    │   ├── research-wiki.md
    │   ├── research-expert.md
    │   └── research-reviewer.md
    └── skill/
        ├── SKILL.md
        ├── wiki-SKILL.md
        ├── reviewer-SKILL.md
        ├── guides/
        │   ├── research_methodology.md
        │   └── detective_toolkit.md
        └── templates/
            ├── simple_report.md
            ├── answer_summary.md
            └── evidence_chain.md
```

## 方法论背景

侦探方法论融合了多个学科的分析技术：

- **情报分析**：ACH 竞争性假设、红队、结构化分析技术（Heuer）
- **科学哲学**：可证伪性（Popper）、溯因推理（Peirce）、强推理（Platt）
- **循证医学**：GRADE 证据分级
- **认知心理学**：预验尸（Klein）、心智模型（Norman）
- **定性研究**：扎根理论（Glaser & Strauss）、三角验证（Denzin）
- **创新管理**：JTBD（Christensen）、Kano 需求分类
- **服务设计**：用户旅程地图、峰终定律
- **商业模式**：价值主张画布（Osterwalder）

## License

MIT
