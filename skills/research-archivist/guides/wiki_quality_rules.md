# Wiki 质量规则与跨 Skill 契约

创建或编辑 wiki 页面、接收 detective/reviewer 回写之前，加载本文件。

## 跨 skill 契约

archivist 与 detective、reviewer 的接口规范统一收在 `contracts/`：

- **wiki 页面格式**:[../../../contracts/wiki_format.md](../../../contracts/wiki_format.md) — 主题页 / 矛盾记录的结构模板,以及"资料栏 vs 分析增量栏"的硬约束
- **分析回写规则**:[../../../contracts/analysis_writeback.md](../../../contracts/analysis_writeback.md) — 来源编号约定、detective/reviewer 的回写通道、回写边界、不篡改资料栏、回写后必做

archivist 入库时按 wiki 页面格式契约建页;detective/reviewer 回写时按分析回写契约操作。这两份契约是三个 skill 共同遵守的接口,不是 archivist 私有规则。

## 质量规则

> 通用方法学红线(证据可追溯、概念诚实、定量纪律等)见 [../../../shared/CLAUDE.md](../../../shared/CLAUDE.md) 的"研究产出的质量底线"。本节只列入库专属规则。

1. **每份资料必须由 LLM 直接阅读**,不能用 Python 提取内容后再处理
2. **Python 只用于辅助统计**(计算频次、生成交叉表),不用于内容理解
3. **原始引用必须准确**,标注来源编号,不要改写原话
4. **矛盾不要调和**——记录双方证据,留给侦探判断
5. **未归类观察不要丢弃**——它们可能是侦探最有价值的发现
6. **每批处理后更新索引**——wiki 的可用性依赖索引的准确性
7. **资料栏与分析增量栏严格分离**——主题页的「证据」栏只放一手资料;侦探分析、审查反例等二手涌现一律写入「分析增量」栏。读者必须能一眼区分"事实"和"解读"
8. **回写不覆盖**——回写到 wiki 时,新内容只能追加,不能修改原入库时写下的证据条目(即使发现原来理解错了,也是另开一条标 `#analysis_xx 修正:...`,保留旧条目)
9. **主题命名诚实**——主题名、矛盾描述对照 [../../research-detective/guides/writing_style.md](../../research-detective/guides/writing_style.md) 红线检查,不允许概念癌词组("结构性 X""X 悖论")或稻草人否定("不是 X 而是 Y")。wiki 措辞会被后续所有分析继承,落字前自查
