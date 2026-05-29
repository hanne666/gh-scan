# GitHub 仓库评估标准

本标准供 `gh-repo-scan` 和 `gh-stars-organizer` 共用。

## 评估维度

| 维度 | 判断内容 |
|---|---|
| 用途清晰度 | README、description、topics 是否能说明项目做什么、给谁用、输入输出是什么 |
| 技术栈 | 语言、runtime、框架、核心依赖、部署方式、外部接口 |
| 安装成本 | 项目本体、依赖、模型/数据、Docker image、首次安装缓存 |
| 维护状态 | `pushed_at`、`updated_at`、release、issue、archive/disabled 状态 |
| 二开价值 | license、架构清晰度、活跃度、可替代性、用户工作流匹配度 |
| 风险 | 账号、抓取、隐私、license、平台政策、全局环境污染 |
| 下一步 | `install`、`pilot`、`adapt`、`clean-room rebuild`、`skip` |

## 事实与推断

- 有证据的内容写成事实。
- 只有名称、description 或 topics 支撑的内容写成“推断”。
- 证据不足时写 `待确认`，不要编造精确结论。

## 默认安全边界

- 默认只读，不 clone、不安装、不运行、不修改本地文件、不操作账号。
- 用户明确要求安装或接入时，先确认目标目录、联网下载、磁盘空间、凭证、全局环境影响和回滚方式。
- 涉及抓取、下载、账号自动化、代理、平台风控时，必须说明合规风险和账号安全风险。
