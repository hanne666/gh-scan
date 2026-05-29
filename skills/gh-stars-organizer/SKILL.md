---
name: gh-stars-organizer
description: 自动整理 GitHub starred repositories。用于用户要求整理 GitHub stars、GitHub 收藏仓库、星标仓库、自动分类 GitHub Lists、识别过时/重复/fork/低价值仓库、放入待复核 Review Later、生成 Markdown 清单，或希望把 GitHub stars 按中文分类长期维护。默认不取消 star，不删除 GitHub Lists，不覆盖非本 skill 管理的旧 Lists。
---

# GitHub Stars 整理

批量整理 GitHub starred repositories，自动分类到 GitHub Lists，生成 Markdown 清单，并把过时、重复、fork、低 star 或用途不明项目放入 `待复核 Review Later`。

除必要技术名词外，默认全部用中文输出。

## 必读参考

开始前按需读取本 skill 的参考文件：

- `references/categories.md`
- `references/freshness.md`
- `references/repo-scan-criteria.md`

如果是在套件真源目录中维护，也可以对照 `skills/gh-scan/shared/`。

## 核心边界

默认可以自动执行：

- 读取 GitHub stars
- 自动分类
- 创建缺失的 GitHub Lists
- 更新仓库所属 Lists
- 保留非本 skill 管理的旧 Lists
- 将待复核项目放入 `待复核 Review Later`
- 生成 Markdown 清单和整理报告

默认禁止，除非用户明确确认：

- 取消 star
- 删除 GitHub List
- 清空已有 List
- 改名已有 List
- 覆盖非本 skill 管理的旧 Lists
- 把私有整理结果公开

## 权限要求

需要本机 `gh` 已登录 GitHub。

读取 stars：

```bash
gh api -H 'Accept: application/vnd.github.star+json' --paginate /user/starred
```

创建或更新 GitHub Lists 需要 `user` scope。缺失时提示用户执行：

```bash
gh auth refresh -h github.com -s user
```

## 脚本优先

这个 skill 已内置自动化脚本。默认优先使用脚本，不要临时重写 GitHub API 和分类逻辑。

一键整理，默认只生成 GitHub Lists 同步计划，不写 GitHub：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py
```

分步执行：

```bash
python3 skills/gh-stars-organizer/scripts/fetch_stars.py --output output/github-stars/YYYY-MM-DD/stars_raw.json
python3 skills/gh-stars-organizer/scripts/classify_stars.py output/github-stars/YYYY-MM-DD/stars_raw.json
python3 skills/gh-stars-organizer/scripts/render_markdown.py output/github-stars/YYYY-MM-DD/stars_classified.json
python3 skills/gh-stars-organizer/scripts/sync_github_lists.py output/github-stars/YYYY-MM-DD/stars_classified.json --dry-run
```

只有用户明确确认写入 GitHub Lists 时，才使用：

```bash
python3 skills/gh-stars-organizer/scripts/sync_github_lists.py output/github-stars/YYYY-MM-DD/stars_classified.json --apply
```

## 默认分类

使用 `categories.md` 的 10 个中文 Lists：

1. `AI 编程与 Agent IDE`
2. `Agent 框架与多 Agent`
3. `MCP 与 Skills`
4. `RAG 与文档处理`
5. `Prompt 与 LLM 工具`
6. `自动化与爬虫`
7. `UI 与应用模板`
8. `开发基础设施与 CLI`
9. `内容与媒体 AI`
10. `待复核 Review Later`

## 更新时间评判

使用 `freshness.md` 的量化标准。

简化规则：

- 0-6 个月内更新：活跃。
- 超过半年未更新：降级观察。
- 超过 1 年未更新：默认 `P2 待复核`。
- 超过 3 年未更新：默认 `P3 清理候选`。
- archived / disabled：`P3 清理候选`。
- 无更新时间：`P2 待复核`，标 `待确认`。

以 `pushed_at` 为主，`updated_at` 为辅。

## 保留级别

| 等级 | 名称 | 默认动作 |
|---|---|---|
| `P0` | 核心保留 | 放入对应主题 List |
| `P1` | 普通保留 | 放入对应主题 List |
| `P2` | 待复核 | 放入 `待复核 Review Later` |
| `P3` | 清理候选 | 放入 `待复核 Review Later`，报告标注，不取消收藏 |

## 工作流

1. 读取 stars：
   - 保存 `starred_at`
   - 保存仓库名、链接、stars、语言、topics、description、license、fork、archived、disabled、`pushed_at`、`updated_at`

2. 读取现有 Lists：
   - 识别本 skill 管理的 10 个 Lists
   - 保留用户已有其他 Lists

3. 自动分类：
   - 用仓库名、description、topics、语言和已知关键词判断分类
   - 低置信度进入 `待复核 Review Later`
   - 需要深度判断时，使用 `gh-repo-scan` 的评估标准做轻量判断

4. 评估保留级别：
   - 结合更新时间、stars、fork、重复、archived、disabled、用途清晰度
   - 只给建议，不自动取消 star

5. 同步 GitHub Lists：
   - 创建缺失 Lists
   - 更新仓库 List 关系
   - 使用 `updateUserListsForItem` 前必须读取当前 List 关系
   - 保留非本 skill 管理的旧 Lists

6. 生成 Markdown：
   - 项目名带 GitHub 链接
   - star 数
   - 150 字以内中文简介
   - 分类
   - 保留级别
   - 清理建议

7. 验收：
   - stars 数量一致
   - 新 Lists 成员数量合计一致
   - 待复核数量明确
   - 没有取消 star

脚本职责：

- `fetch_stars.py`：读取 GitHub stars，保存 `stars_raw.json`。
- `classify_stars.py`：按分类和更新时间标准生成 `stars_classified.json`。
- `render_markdown.py`：生成 `github_stars_inventory.md` 和 `lists_summary.md`。
- `sync_github_lists.py`：生成同步计划；`--apply` 时创建缺失 Lists 并更新仓库所属 Lists。
- `organize_stars.py`：串联以上步骤，默认 dry-run。

## 输出文件

默认输出到：

```text
output/github-stars/YYYY-MM-DD/
├── stars_raw.json
├── stars_classified.json
├── lists_summary.md
└── github_stars_inventory.md
```

如果用户指定路径，例如 `raw/笔记/GitHub收藏仓库分类清单.md`，按用户路径写入。

## 最终报告

按以下结构输出：

1. `结论`
2. `修改文件`
3. `关键改动`
4. `验证结果`
5. `风险与未完成事项`

如果有建议取消 star 的项目，只能列为“待确认动作”。
