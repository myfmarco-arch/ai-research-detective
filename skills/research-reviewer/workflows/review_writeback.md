# 审查回写工作流

仅在 wiki 模式下加载本文件：当 reviewer 找到反例、盲区或被反驳的理论预测，需要追加回写到 wiki 时使用。

### 步骤 5：回写 wiki（仅 wiki 模式）

审查中发现的反例和盲区是**最高质量的知识**——它们经过了主动对抗才浮现。这些必须回写到 wiki，否则下一次分析会重蹈覆辙。

回写来源编号统一用 `#review_YYYYMMDD`（YYYYMMDD 为审查日期）。回写边界和格式遵循 [../../../contracts/analysis_writeback.md](../../../contracts/analysis_writeback.md)（wiki 页面结构见 [../../../contracts/wiki_format.md](../../../contracts/wiki_format.md)）。

具体执行：

1. **被推翻或弱化的结论** → 追加到 `wiki/contradictions.md`，类型标「分析 vs 反例」：
   - 正方：被审查的结论原文 + 来源 `#analysis_YYYYMMDD`
   - 反方：审查中找到的反面证据 + 原始资料编号
   - 类型/发现来源：`#review_YYYYMMDD`

2. **审查中找到的反例引用** → 追加到 `wiki/quotes.md` 对应主题分组下，类型标「反例」，标注 `#review_YYYYMMDD` + 原始资料编号（说明这条反例其实来自 #interview_xx，但是审查时才被发现）

3. **被发现的样本盲区**（如"轻度用户视角缺失""某年龄段未覆盖"） → 追加到 `wiki/uncategorized.md`，标「类型：覆盖盲区 / 来源：#review_YYYYMMDD」。盲区是 detective 下次做盲区扫描的输入，不需要再在 `_index.md` 重复

4. **被反驳的理论预测** → 更新 `wiki/frameworks.md` 中对应理论的「验证状态」为「被反驳」，追加 `#review_YYYYMMDD`

5. **不回写的内容**：
   - confirmed 的结论不需要回写——结论本身已经在报告里
   - 报告的措辞批评、风格问题——这些是产出形态，不是知识
   - 已经被报告自己标注"待验证"的弱结论——报告已经自我限定了

回写后更新 `wiki/_log.md`：`[YYYY-MM-DD] 审查回写 #review_YYYYMMDD：新增矛盾 K / 新增反例 N / 新增盲区 M / 反驳理论 J`。

**关键原则**：审查回写**只追加，不修改**。即使发现某条原始资料引用被 detective 误读，也不能修改主题页「证据」栏的原条目——而是在「分析增量」栏新增一条 `#review_YYYYMMDD 修正：原 #analysis_xxx 对 #interview_yy 的解读有误，原话其实是 [...]`。保留误读的痕迹，下次分析才能看到判断的演化。

