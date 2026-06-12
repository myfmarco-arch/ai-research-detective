# Wiki 回写工作流

仅在 wiki 模式下加载本文件：当侦探分析产生新主题、矛盾、关联、理论验证状态变化或沉默信号，需要追加回写到 wiki 时使用。

#### 3f. 回写 wiki（仅 wiki 模式）

侦探分析结束后，把本次分析中**新涌现**的发现回写到 wiki，让 wiki 随每次分析变厚。回写边界和格式遵循 [../../../contracts/analysis_writeback.md](../../../contracts/analysis_writeback.md)（wiki 页面结构见 [../../../contracts/wiki_format.md](../../../contracts/wiki_format.md)）。

回写来源编号统一用 `#analysis_YYYYMMDD`（YYYYMMDD 为今天日期）。具体执行：

1. **新涌现主题**（入库时没浮现、分析才看出的模式） → 在 `wiki/themes/` 创建 `theme_xxx.md`，头部标注「来源类型：分析涌现」。证据栏列原本散落在 `#interview_xx` 中、被分析重新连起来的一手引用；分析增量栏标 `#analysis_YYYYMMDD` 说明"为什么这些归为同一主题"。**无一手资料支撑的纯推断不立主题页，进 `wiki/uncategorized.md` 标「类型：分析推测 / 待资料验证」**
2. **新发现矛盾**（跨主题或跨资料的矛盾，入库时未标记） → 追加到 `wiki/contradictions.md`，类型标「分析 vs 反例」或「文献预测 vs 数据」，发现来源标 `#analysis_YYYYMMDD`
3. **新发现的全局关联**（如"提到 A 的用户 80% 同时有 B 行为"） → 在两个相关主题页的「关联主题」栏新增条目，标 `#analysis_YYYYMMDD`
4. **理论验证状态变化**（数据验证/反驳了文献预测） → 更新 `wiki/frameworks.md` 中对应理论的「验证状态」字段为 `已验证 / 待验证 / 被反驳`，追加 `#analysis_YYYYMMDD`
5. **沉默信号**（预期出现但实际缺失的主题） → 追加到 `wiki/uncategorized.md`，标「类型：沉默信号 / 来源：#analysis_YYYYMMDD」

**不回写**：报告的措辞、章节排列、优先级矩阵——这些是产出形态，不是知识。

回写后更新 `wiki/_log.md`，追加一条：`[YYYY-MM-DD] 分析回写 #analysis_YYYYMMDD：新增主题 N / 新增矛盾 K / 验证理论 M`。
