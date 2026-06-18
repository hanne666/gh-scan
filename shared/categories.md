# GitHub Stars 分类策略

`gh-stars-organizer` 默认使用动态分类，而不是固定分类表。

## 默认动态分类

动态分类会先读取当前账号的 starred repositories，再根据这批仓库本身生成分类：

1. 优先统计仓库 `topics`。
2. 选择在当前收藏列表中更常见的 topics 作为分类。
3. 如果仓库没有可用 topic，则使用主要语言作为兜底分类。
4. 分类低置信度、过时、重复、fork、archived 或 disabled 的项目进入 `待复核 Review Later`。
5. 最终 GitHub Lists 分类总数不能超过 8 类；超过上限时，低频分类会并入 `待复核 Review Later`。

动态分类示例：

| 分类来源 | List 示例 |
|---|---|
| topic: `mcp` | `主题：MCP` |
| topic: `browser-automation` | `主题：browser automation` |
| language: `Python` | `语言：Python` |
| 低置信度或需人工判断 | `待复核 Review Later` |

默认参数：

- `--category-mode dynamic`
- `--max-categories 8`
- `--min-category-size 2`

## 固定分类模式

如果用户希望沿用个人固定分类，可以显式使用：

```bash
python3 skills/gh-stars-organizer/scripts/organize_stars.py --category-mode preset
```

固定分类包含：

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

即使使用固定分类模式，最终写入或计划写入 GitHub Lists 的分类总数仍不能超过 8 类。

## 管理边界

- 默认不取消 star。
- 默认不删除、清空或改名 GitHub Lists。
- 同步时只创建本次分类结果需要的 Lists。
- GitHub Lists 分类总数最多 8 类。
- 更新仓库 List 关系时，必须保留非 gh-scan 管理的旧 List 关系。
- `P2` 和 `P3` 项目进入 `待复核 Review Later`，仅作为待确认动作提示。
