# 发版清单

每次 tag 新版本（如 `v1.0.0`）前必跑。借鉴 Anthropic 官方 plugin-dev 的 `plugin-validator` + Appetals 的"干净环境冒烟测试"。

## 1. 版本与文档

- [ ] `.claude-plugin/plugin.json` 的 `version` 已按 SemVer 升级
  - 加新 skill / 新动作 / 新交付物 → MINOR
  - 改 skill 名 / 删动作 / 改 lint 红线语义 / 发布稳定版里程碑 → MAJOR
  - 修 bug、改文案、改非红线规则 → PATCH
- [ ] `CHANGELOG.md` 已添加本版本条目，列出"增 / 改 / 删"三栏
- [ ] `README.md` / `README_en.md` 安装命令、能力清单与 plugin.json / marketplace.json 一致

## 2. 跑一遍 Anthropic 官方 plugin-validator（结构兜底）

在 Claude Code 里：

```
/plugin marketplace add anthropics/claude-code
/plugin install plugin-dev@claude-code
```

然后让 plugin-validator subagent 审一次本仓库：

> Use the plugin-validator subagent to perform a final readiness check on this plugin. Cover: manifest schema, layout, discovery, paths, hook config, agent isolation, MCP/LSP setup. Block release on any blocker-severity finding.

- [ ] plugin-validator 报告 0 个 blocker
- [ ] 所有 warning 已评估（接受 / 修复 / 在 CHANGELOG 中说明）

## 3. 干净环境冒烟测试（避免"我的机器能跑"）

在**全新目录或干净 docker** 里：

```bash
# 模拟用户安装路径
/plugin marketplace add /absolute/path/to/ai-research-detective
/plugin install ai-research-detective@ai-research-detective
```

跑一次最小用例（每个 skill 跑一次冒烟）：

- [ ] `research-archivist`：放 2-3 份假访谈/反馈到 `data/`，跑一次入库 → `verify_quotes.py` 和 `lint_source_coverage.py` exit 0
- [ ] `research-detective`：在已就绪的 wiki 上跑一次分析 → 生成 `process/0_method_selection.md` 和 3a-3e，`lint_process.py --wiki-mode` exit 0、`lint_report.py` exit 0
- [ ] `research-reviewer`：对上一步的报告跑审查 → 产出 `outputs/review.md`，结构合规

## 4. 已知失败模式自查（Appetals 高频 bug）

- [ ] skill 内脚本路径使用 `${CLAUDE_SKILL_DIR}/...` 或从当前 skill 出发的明确相对路径，没有绝对家目录；全仓无 `${CLAUDE_PLUGIN_ROOT}`
- [ ] `.claude-plugin/` 目录只有 `plugin.json` + `marketplace.json`，components 都在仓库根
- [ ] 没有把 `.claude-plugin/CHANGELOG.md` 这种文档塞进 skill 目录（anti-pattern #11）
- [ ] 三个 SKILL.md 的 description 第一句包含动作触发词（动词前置）

## 5. Tag 与发布

- [ ] `git tag v1.0.0 && git push --tags`（按实际版本替换）
- [ ] 在 marketplace 入口（marketplace.json）的 description 与 plugin.json 主线一致
- [ ] 如使用 GitHub Releases，创建对应 release notes，摘要来自 CHANGELOG 最新条目

---

跑完上面 5 项才发版。漏跑哪项就在 CHANGELOG 里写清楚"本版本未跑 X，原因 Y"——别默默省略。
