# gh-scan

`gh-scan` 是 GitHub 仓库研究与 GitHub stars 整理套件。

包含两个子 skill：

- `gh-repo-scan`：单个 GitHub 仓库、插件、CLI、开源工具的只读扫描与评估。
- `gh-stars-organizer`：批量整理 GitHub starred repositories，自动归类到 GitHub Lists，并生成 Markdown 清单。

维护原则：

- `skills/gh-scan/` 是真源。
- `~/.claude/skills/` 和 `~/.codex/skills/` 是安装副本。
- 修改真源后，再同步到 Claude Code 和 Codex。
