# Kiro 版本

## 安装

用 Kiro 打开 `kiro/` 目录作为工作区。`.kiro/steering/` 下的文件会自动被 Kiro 识别。

## 使用

### 第一步：入库

1. 把研究资料放在工作区根目录或 `data/` 子目录
2. 在聊天中通过 `#` 选择 `research-wiki` steering
3. 说：`帮我把访谈资料入库到 wiki`

增量更新——有新资料时：
1. 把新资料放进 `data/`
2. 选择 `research-wiki` steering
3. 说：`有新资料，帮我更新 wiki`

### 第二步：侦探分析

1. 在聊天中通过 `#` 选择 `research-expert` steering
2. 说：`分析 wiki 里的数据` 或带具体问题

### 第三步：对抗审查（可选但推荐）

1. 选择 `research-reviewer` steering
2. 说：`审查这份报告`
3. 审查完成后，切回 `research-expert`，说：`根据 review.md 修改报告`

### 不用 wiki 也能跑

资料量小时，直接选 `research-expert` steering，说 `帮我分析这些访谈`。

## 文件结构

```
kiro/
├── .kiro/steering/
│   ├── research-wiki.md      # 入库 steering（manual inclusion）
│   ├── research-expert.md    # 侦探分析 steering（manual inclusion）
│   └── research-reviewer.md  # 对抗审查 steering（manual inclusion）
└── skill/
    ├── SKILL.md              # 侦探分析工作流
    ├── wiki-SKILL.md         # 入库工作流
    ├── reviewer-SKILL.md     # 对抗审查工作流
    ├── guides/
    │   ├── research_methodology.md
    │   └── detective_toolkit.md
    └── templates/
        ├── simple_report.md
        ├── answer_summary.md
        └── evidence_chain.md
```

## 与 Claude Code 版的区别

| | Claude Code | Kiro |
|---|---|---|
| skill 加载 | 自动匹配 description | 手动通过 `#` 选择 steering |
| 入口文件 | SKILL.md（有 frontmatter） | steering .md → 引用 SKILL.md |
| 工具限制 | `allowed-tools` 字段 | 无此机制 |
| 其他 | 内容完全一致 | 内容完全一致 |

两个版本的分析逻辑、工具箱、模板、质量规则完全相同，只是加载方式不同。
