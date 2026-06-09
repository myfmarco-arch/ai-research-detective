# 冷启动:从空目录到 CONTEXT 就位

> 三个 skill(`research-archivist` / `research-detective` / `research-reviewer`)在没有 `CONTEXT.md` 的项目里启动时,共用本流程。
> 单一真源:本文件被各 SKILL.md 引用,改这里所有 skill 同步生效。

## 触发条件

- 当前目录没有 `CONTEXT.md`
- 或 `CONTEXT.md` 存在但速读卡 / 我的身份 / 研究问题任一字段空白或带 `<!-- 待用户补充 -->` 标记

## 原则:先扫再问,不问空白题

不要扔空模板让用户从零填。先扫项目,把能推断的字段填好,再请用户**一次性**补齐空白字段。

## 流程

### 步骤 1: 扫描项目,提取能推断的信息

- 列出根目录、`data/`(如有)、其他可见目录的所有文件
- 阅读这些文件(不只是文件名),提取:
  - **研究对象**: 文档里反复出现的产品名、品牌、人群标签
  - **资料类型与规模**: 访谈 N 份 / 问卷 N 份 / 文献 / 竞品分析
  - **可能的研究问题**: 从需求文档、过往报告、邮件中浮出的问题
  - **参考资料**: 现有的方法论文档、行业报告、历史项目

### 步骤 2: 生成 CONTEXT/README 初稿

基于 [shared/templates/CONTEXT.md](templates/CONTEXT.md) 和 [shared/templates/README.md](templates/README.md):

- 推断到的字段直接填好
- 推断不到的字段保留空白,紧接其后插入 `<!-- 待用户补充 -->` 注释
- 不要删模板里的章节结构

### 步骤 3: 一次性请用户补齐

把生成的初稿展示给用户,列出**所有标了"待用户补充"的字段**,请其一次性回答:

- 研究问题(核心 + 辅助)
- 汇报给谁
- 产出形式(报告 / 纪要 / 演示稿,大概长度)
- 产出位置(默认 `outputs/`,可覆盖)
- 1-3 条项目专属红线(不写通用方法学)
- 你在这个项目里的身份(专业训练 + 承担的角色)
- 项目特有的分析流程偏好(可选)

同时**请用户检查 AI 已填好的字段有没有错**——AI 推断可能错,用户校对一遍才安全。

### 步骤 4: 合并写入

用户回复后:

1. 把回答合并进初稿,写出最终 `CONTEXT.md` 和 `README.md`
2. **跑 `lint_context.py` 校验最终 CONTEXT.md**(红线 0 才算 cold_start 通过):

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/shared/scripts/lint_context.py CONTEXT.md
   ```

   红线非 0(占位符残留 / 必填字段空 / 核心问题 < 20 字)→ 回到步骤 3 让用户继续补;黄线(底线套话 / 填充式动词)人工复核
3. 创建 `data/`(如不存在)、`process/`、`outputs/`
4. 如果根目录有未归类的研究资料,询问用户是否移入 `data/`(不要擅自移动)
5. **自动配置项目级硬约束(CLAUDE.md)**:
   - 检查项目根是否已有 `CLAUDE.md`
   - **没有**:告知用户"将从 skill 包复制 `CLAUDE.md` 到项目根(项目级硬约束的单一真源,各 SKILL.md 引用)",得到确认后执行 `cp <skill包路径>/CLAUDE.md <项目根>/CLAUDE.md`
   - **已有**(用户自己的项目级配置):**不要覆盖**。展示 skill 包 `CLAUDE.md` 的内容,询问用户:① 追加到现有 `CLAUDE.md` 末尾,② 不动,我自己手动整合,③ 仍然覆盖(警告:会丢失现有内容)。默认推荐 ①
   - skill 包 `CLAUDE.md` 路径:本 plugin 内的 `shared/CLAUDE.md`,即从当前 SKILL.md 文件位置上溯两级(`skills/research-detective/SKILL.md` → `skills/` → plugin 根)再进入 `shared/`

### 步骤 5: 进入各 skill 的常规流程

- `research-archivist` 进入资料评估和入库
- `research-detective` 进入证据采集和分析
- `research-reviewer` 进入对抗性审查

## 增量场景的处理

当 `CONTEXT.md` 已存在但部分字段缺失:

- 不重新扫项目,只针对缺失字段问用户
- 不动用户已填的字段,即使 AI 觉得不准

## 不做的事

- **不做的事 1**: 不读 CONTEXT 直接开始分析。这等于默认违反视角约束
- **不做的事 2**: 不一字段一问。一次性把空白字段列全,用户一次回答
- **不做的事 3**: 不擅自把根目录文件移入 `data/`。问过用户再动
