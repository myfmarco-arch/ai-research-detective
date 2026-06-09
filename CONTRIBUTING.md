# 贡献指南

欢迎贡献。本项目是一个 [Claude Code plugin](https://docs.claude.com/en/docs/claude-code/plugins)，由三个协作的 skill 组成，核心质量保障靠一组 Python lint 脚本 + fixture 测试。

## 项目结构速览

```text
ai-research-detective/          # 仓库根 = plugin 根
├── .claude-plugin/             # plugin.json + marketplace.json（元信息）
├── contracts/                  # 跨 skill 接口规范（所有 skill 共同遵守，不能各自改）
├── shared/                     # 三个 skill 共用资源（模板、冷启动、跨 skill lint）
└── skills/                     # Claude Code 自动发现的三个 skill
    ├── research-archivist/     # 入库
    ├── research-detective/     # 分析
    └── research-reviewer/      # 对抗审查
```

详细说明见 [README.md](README.md) 的「项目结构」一节。

## 本地开发

把仓库软链接到 Claude Code 的 plugin 目录，改动即时生效：

```bash
ln -s "$(pwd)" ~/.claude/plugins/ai-research-detective
```

## 跑测试

每个 lint 脚本都配了 good/bad fixture 和一个 bash runner。改动任何脚本或 fixture 后，把四个 runner 全跑一遍，必须全绿：

```bash
bash shared/scripts/tests/run_tests.sh
bash skills/research-archivist/scripts/tests/run_tests.sh
bash skills/research-detective/scripts/tests/run_tests.sh
bash skills/research-reviewer/scripts/tests/run_tests.sh
```

当前基线共 108 项测试，全部通过。新增 lint 规则时，请同步：

1. 在对应 `fixture_*_bad` 里加一处会触发新规则的污染
2. 在 `run_tests.sh` 里加一条 `assert_contains` 断言新规则被抓到
3. 确认 good fixture 仍然干净通过（不要误伤）

只依赖 Python 3 标准库，无需安装额外依赖。

## 提交规范

- commit message 用一句话讲清「改了什么 + 为什么」，可中可英
- 改动 lint 红线语义、删 skill 动作、改 skill 名 → 属于破坏性变更，需在 PR 描述里显式说明
- 涉及版本发布的改动，遵循 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)

## 提 PR

1. 从 `main` 切新分支
2. 改动 + 跑全部测试通过
3. 在 `CHANGELOG.md` 顶部加本次改动条目（增 / 改 / 删三栏）
4. 推分支并开 PR，描述里写清动机、改了哪些文件、跑过哪些测试

## 版本号

遵循 [SemVer](https://semver.org/lang/zh-CN/)：

- 加新 skill / 新动作 → MINOR
- 改 skill 名 / 删动作 / 改 lint 红线语义 → MAJOR
- 修 bug、改文案、改非红线规则 → PATCH

版本号在 `.claude-plugin/plugin.json` 的 `version` 字段，发版前确保它与 `CHANGELOG.md` 最新条目一致。

## 反馈

不确定要不要动手实现的想法，先开 [Issue](https://github.com/myfmarco-arch/ai-research-detective/issues) 讨论。方法论层面的探讨也欢迎。
