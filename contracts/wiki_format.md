# wiki 页面格式契约

跨 skill 共享的 wiki 页面结构规范。

- **producer**: research-archivist(入库时建/更新)
- **consumers**: research-archivist(自检与增量更新)、research-detective(读 + 回写「分析增量」栏)、research-reviewer(读 + 回写反例与盲区)
- **配套契约**:回写规则见 [analysis_writeback.md](analysis_writeback.md)

读者必须能一眼区分"用户原话"(证据栏)和"AI 推断"(分析增量栏)——前者是事实,后者是解读。任何 skill 写入 wiki 都不允许混淆这条边界。

## 主题页模板(`wiki/themes/theme_xxx.md`)

```markdown
# [主题名称]

> 来源类型:资料涌现 / 分析涌现(二选一,分析涌现的主题在头部明确标注)

## 一句话定义

[这个主题捕捉了什么]

## 证据(来自原始资料,不可篡改)

> 此栏只放 #interview_xx / #survey_xx / #feedback_xx 等一手资料引用。

- #interview_01: "[原始引用]" — [观察类型:行为/态度/痛点/积极]
- #interview_05: "[原始引用]" — [观察类型]
- ...

## 分析增量(来自侦探分析或对抗审查)

> 此栏放 #analysis_YYYYMMDD / #review_YYYYMMDD 的涌现内容,与原始证据明确分开。

- #analysis_20260527: 跨主题关联——[主题B] 中 80% 提到此现象的人也在本主题中出现
- #review_20260530: 反例——#interview_22 在追问中说了与本主题相反的内容(原入库时漏读)
- ...

## 频次

- 提及人数: N/总数
- 情感强度: 高/中/低(基于用词和描述详细程度)

## 关联主题

- 与 [主题B] 共现频率高(来源: #analysis_YYYYMMDD)
- 与 [主题C] 存在矛盾(详见 contradictions.md)

## 理论支撑(如适用)

- [理论名](来源: #framework_xx) 预测了此现象 — 验证状态: 已验证 / 待验证 / 被反驳

## 入库与生长历史

- [日期] 首次创建,基于 #interview_01-#interview_30
- [日期] 增量更新,新增 #interview_31-#interview_50 的证据
- [日期] 分析回写 #analysis_YYYYMMDD:发现与 [主题B] 的隐藏关联
- [日期] 审查回写 #review_YYYYMMDD:补入反例
```

## 矛盾记录模板(`wiki/contradictions.md`)

```markdown
# 矛盾记录

## 矛盾 1: [简要描述]

- **类型**: 资料内部矛盾 / 分析 vs 反例 / 文献预测 vs 数据
- **正方**: [观点A] — 来源: #interview_xx, #interview_yy
- **反方**: [观点B] — 来源: #interview_zz, #interview_ww
- **可能原因**: [用户分群差异?场景差异?口头 vs 行为?]
- **发现时间**: [日期]
- **发现来源**: 入库时 / #analysis_YYYYMMDD / #review_YYYYMMDD

## 矛盾 2: ...
```

## 硬约束(任何 skill 写入 wiki 都必须遵守)

1. **资料栏与分析增量栏严格分离**:主题页的"证据"栏只放一手资料(`#interview_*` / `#survey_*` / `#feedback_*`);侦探分析、审查反例等二手涌现一律写入"分析增量"栏(`#analysis_*` / `#review_*`)。
2. **回写不覆盖**:新内容只能追加,不能修改原入库时写下的证据条目。即使发现原来理解错了,也是另开一条标 `#analysis_xx 修正:...`,保留旧条目。
3. **无一手资料支撑的纯推断不立主题页**:放 `wiki/uncategorized.md`,标注"类型:分析推测 / 待资料验证"。
4. **主题命名诚实**:主题名、矛盾描述对照 [../skills/research-detective/guides/writing_style.md](../skills/research-detective/guides/writing_style.md) 红线检查,不允许概念癌词组("结构性 X""X 悖论")或稻草人否定("不是 X 而是 Y")。wiki 措辞会被后续所有分析继承,落字前自查。
