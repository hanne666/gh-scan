# gh-scan

`gh-scan` 是一个面向 Codex、Claude Code 等 Agent 工作流的 GitHub 研究与整理 skill 套件。它把两类高频任务拆成两个独立 skill：单个仓库只读评估，以及当前账号 GitHub stars 的批量分类整理。

这个项目不是通用 GitHub 客户端，也不默认替用户安装仓库、运行代码或修改账号数据。它的目标是把“先评估，再决定是否行动”的工作流固化成清晰、可复用、可验证的 Agent 执行规范。

## 核心能力

- `gh-repo-scan`：对单个 GitHub 仓库、浏览器扩展、CLI 工具、插件或开源项目做只读评估。
- `gh-stars-organizer`：读取当前 GitHub 账号的 starred repositories，根据收藏列表里的仓库内容动态分类，生成 Markdown 清单，并在明确确认后同步到 GitHub Lists。
- 统一输出仓库用途、适用场景、技术栈、运行条件、最小空间占用、安装难点、风险、二开价值和建议下一步。
- 对证据不足的信息使用 `待确认`，不把猜测、伪数据或默认值冒充事实。
- 对账号、抓取、自动化、代理、平台风控、license 和隐私相关风险做显式提示。

## 适用场景

### 研究单个仓库或工具

适合用 `gh-repo-scan` 处理：

- 这个仓库是什么，解决什么问题，适合谁使用。
- 技术栈、运行环境、依赖、模型或数据要求是什么。
- 本地安装至少需要多少空间，哪些部分仍需实测确认。
- 是否适合 Codex、Claude Code、Trae 或其他 Agent 工作流。
- 是否值得安装、试用、二次开发，或用 clean-room 方式重做。
- 浏览器扩展、自动化工具、爬虫、插件是否存在账号、隐私、平台政策或合规风险。

默认行为是只读评估：不 clone、不安装、不运行、不修改本地文件、不操作账号。只有用户明确确认进入安装、试运行或二开阶段，才继续下一步。

### 整理 GitHub stars

适合用 `gh-stars-organizer` 处理：

- 拉取当前 GitHub 账号的 starred repositories。
- 根据当前收藏列表里的 topics 和语言动态生成 GitHub Lists 分类。
- 识别过时、重复、fork、低 star、用途不明、archived 或 disabled 项目。
- 生成 Markdown 分类清单、整理摘要和 GitHub Lists 同步计划。
- 在用户明确确认后创建缺失的 GitHub Lists，并更新仓库所属 Lists。

默认不取消 star，不删除 List，不清空 List，不改名已有 List，不覆盖非本 skill 管理的旧 List 关系。

## 套件结构

```text
gh-scan/
├── README.md
├── scripts/
│   ├── sync_skills.py
│   └── validate.py
├── shared/
│   ├── categories.md
│   ├── freshness.md
│   └── repo-scan-criteria.md
└── skills/
    ├── gh-repo-scan/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   └── references/
    │       └── criteria.md
    └── gh-stars-organizer/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   ├── categories.md
        │   ├── freshness.md
        │   └── repo-scan-criteria.md
        └── scripts/
            ├── classify_stars.py
            ├── common.py
            ├── fetch_stars.py
            ├── organize_stars.py
            ├── render_markdown.py
            └── sync_github_lists.py
```

## 子 skill 说明

### gh-repo-scan

路径：

```text
skills/gh-repo-scan/
```

用于对单个仓库、插件、扩展或工具做证据驱动的只读分析。典型输出包含：

1. 结论
2. 它是做什么的
3. 适合谁 / 适用场景
4. 技术栈
5. 最小空间占用
6. 怎么用 / 运行条件
7. 安装或接入难点
8. 二开价值
9. 风险
10. 建议下一步
11. 证据来源

触发示例：

```text
用 gh-repo-scan 研究这个仓库：https://github.com/example/project
```

```text
这个项目能不能本地安装？技术栈是什么？依赖和模型至少占多少空间？
```

```text
扫描这个 Chrome 插件，告诉我能不能 clean-room 做一个类似工具。先只读评估，不要安装。
```

### gh-stars-organizer

路径：

```text
skills/gh-stars-organizer/
```

用于批量整理当前账号的 GitHub stars，并根据这批仓库本身生成分类清单和同步计划。

默认使用动态分类：

1. 优先统计当前 stars 中的 GitHub topics。
2. 选择更常见的 topics 作为分类，例如 `主题：MCP`、`主题：browser automation`。
3. 如果仓库缺少可用 topic，则使用主要语言兜底，例如 `语言：Python`。
4. 分类低置信度、过时、重复、fork、archived 或 disabled 的项目进入 `待复核 Review Later`。
5. GitHub Lists 分类总数最多 8 类；超过上限时，低频分类会并入 `待复核 Review Later`。

如果你自己希望沿用内置固定分类，可以显式使用 `--category-mode preset`；固定分类模式同样受 8 类上限约束。

保留级别：

| 等级 | 含义 | 默认动作 |
|---|---|---|
| `P0` | 核心保留 | 放入对应主题 List |
| `P1` | 普通保留 | 放入对应主题 List |
| `P2` | 待复核 | 放入 `待复核 Review Later` |
| `P3` | 清理候选 | 放入 `待复核 Review Later`，只在报告中提示 |

`P3` 不是自动删除。这个 skill 只提出清理建议，不自动取消 star。

## 环境要求

基础验证只需要：

- Python 3

整理 GitHub stars 还需要：

- GitHub CLI：`gh`
- 当前机器已登录 GitHub：`gh auth status`
- 如需创建或更新 GitHub Lists，通常需要 `user` scope

刷新权限：

```bash
gh auth refresh -h github.com -s user
```

如果只使用 `gh-repo-scan` 做公开仓库只读评估，不一定需要 GitHub CLI 登录；但遇到 API rate limit、私有仓库、账号 stars 或 GitHub Lists 时需要认证。

## 使用方式

### 验证套件结构

在项目根目录运行：

```bash
python3 scripts/validate.py
```

默认校验：

- 两个子 skill 的 `SKILL.md` 是否存在。
- `agents/openai.yaml` 是否包含必要字段。
- 参考文档是否存在。
- stars 整理脚本是否存在。
- 本机安装副本是否与真源同步。

如果希望把安装副本不同步也视为失败：

```bash
python3 scripts/validate.py --strict
```

### 同步到本机 Agent skill 目录

默认 dry-run，不写入安装目录：

```bash
python3 scripts/sync_skills.py
```

确认后实际同步到：

- `~/.claude/skills/`
- `~/.codex/skills/`

执行：

```bash
python3 scripts/sync_skills.py --apply
```

注意：`~/.claude/skills/` 和 `~/.codex/skills/` 是本机安装副本，不是真源。发布、维护和改动应以当前仓库为准。

### 一键整理 GitHub stars

默认 dry-run，只生成文件和同步计划，不写 GitHub Lists：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py
```

默认分类模式是 `dynamic`。如果需要调整动态分类数量：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py \
  --max-categories 8 \
  --min-category-size 2
```

如果你自己要使用内置固定分类：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py --category-mode preset
```

指定输出目录：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py \
  --output-dir output/github-stars/2026-05-29
```

限制页数做 smoke test：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py \
  --output-dir /private/tmp/gh-scan-smoke \
  --max-pages 1
```

确认写入 GitHub Lists 时才使用：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py --apply-lists
```

如需把新建 Lists 设为公开：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py \
  --apply-lists \
  --public-lists
```

### 分步整理 GitHub stars

```bash
python3 skills/gh-stars-organizer/scripts/fetch_stars.py \
  --output output/github-stars/YYYY-MM-DD/stars_raw.json

python3 skills/gh-stars-organizer/scripts/classify_stars.py \
  output/github-stars/YYYY-MM-DD/stars_raw.json

python3 skills/gh-stars-organizer/scripts/render_markdown.py \
  output/github-stars/YYYY-MM-DD/stars_classified.json

python3 skills/gh-stars-organizer/scripts/sync_github_lists.py \
  output/github-stars/YYYY-MM-DD/stars_classified.json \
  --dry-run
```

只有明确确认写入 GitHub Lists 后，才把最后一步改为：

```bash
python3 skills/gh-stars-organizer/scripts/sync_github_lists.py \
  output/github-stars/YYYY-MM-DD/stars_classified.json \
  --apply
```

## 输出文件

`gh-stars-organizer` 默认输出到：

```text
output/github-stars/YYYY-MM-DD/
├── stars_raw.json
├── stars_classified.json
├── github_stars_inventory.md
├── lists_summary.md
└── lists_sync_plan.json
```

文件说明：

| 文件 | 说明 |
|---|---|
| `stars_raw.json` | 从 GitHub API 读取并归一化后的 starred repositories |
| `stars_classified.json` | 带分类、保留级别、更新时间判断和清理建议的结构化结果 |
| `github_stars_inventory.md` | 按中文分类整理的 Markdown 清单 |
| `lists_summary.md` | 分类数量、待复核数量和保留级别统计 |
| `lists_sync_plan.json` | GitHub Lists 同步计划，dry-run 时只生成计划，不写 GitHub |

## 安全边界

本项目默认遵守以下边界：

- 不用猜测、伪数据或默认值冒充真实结果。
- 证据不足的内容标为 `待确认`。
- 只读评估阶段不 clone、不安装、不运行、不修改文件、不操作账号。
- stars 整理默认不取消 star。
- 不删除、不清空、不改名用户已有 GitHub Lists。
- 同步 Lists 时只创建本次分类结果需要的 Lists，分类总数最多 8 类，并保留非本 skill 管理的旧 List 关系。
- 写入 GitHub Lists 必须由用户明确确认。

## 许可证

本项目使用 Apache License 2.0。完整条款见 `LICENSE`。

## 维护原则

- 当前仓库根目录是 `gh-scan` 套件真源。
- `skills/gh-repo-scan/` 和 `skills/gh-stars-organizer/` 是两个可安装子 skill。
- `shared/` 保存两个子 skill 共用的评估标准、分类和更新时间规则。
- 修改能力边界时，优先保证对应 `SKILL.md` 准确。
- 修改使用说明、维护方式和发布说明时，更新 `README.md`。
- 修改共享规则时，同步检查 `shared/` 和各子 skill `references/` 下的副本是否一致。

## 发布前检查

发布到 GitHub 前建议执行：

```bash
python3 scripts/validate.py
python3 scripts/validate.py --strict
python3 scripts/sync_skills.py
```

如果改动了 stars 整理脚本，建议再做一次不写 GitHub 的 smoke test：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py \
  --output-dir /private/tmp/gh-scan-smoke \
  --max-pages 1
```

通过标准：

- `validate.py` 输出 `gh-scan suite valid`。
- strict 模式没有结构错误。
- dry-run 同步只显示将要写入的安装路径。
- smoke test 能生成 `stars_raw.json`、`stars_classified.json`、`github_stars_inventory.md`、`lists_summary.md` 和 `lists_sync_plan.json`。
- 没有在未确认的情况下写入 GitHub Lists。

## 常见问题

### README 和 SKILL.md 的关系是什么？

`README.md` 面向人，解释这个仓库的定位、结构、用法和维护方式。`SKILL.md` 面向 Codex / Claude Code 等 Agent，定义触发后必须遵守的执行流程和安全边界。

### 为什么拆成两个 skill？

单仓库评估和 stars 批量整理的执行风险不同。`gh-repo-scan` 默认只读，强调证据和评估；`gh-stars-organizer` 会读取账号 stars，并可能在确认后写 GitHub Lists，所以需要更明确的权限、dry-run 和同步边界。

### 会自动取消 star 吗？

不会。即使某个项目被标为 `P3 清理候选`，脚本也只会把它放入 `待复核 Review Later` 并在报告中提示。取消 star 必须由用户另行明确确认，而且当前脚本没有提供自动取消 star 的默认流程。

### 会覆盖已有 GitHub Lists 吗？

默认不会。同步逻辑只创建本次分类结果需要的 Lists，并在更新仓库 List 关系时保留非本 skill 管理的旧 List 关系。

### 安装副本不同步怎么办？

先查看 dry-run：

```bash
python3 scripts/sync_skills.py
```

确认无误后同步：

```bash
python3 scripts/sync_skills.py --apply
```

同步后再运行：

```bash
python3 scripts/validate.py --strict
```

