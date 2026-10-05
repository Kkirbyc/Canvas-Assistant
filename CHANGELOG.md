# 更新记录

## 1.0.0-preview.1 — 2026-10-05

首次公开预览版，项目名“Canvas 小助手 / Canvas Assistant”，作者 Kkirbyc。

- 提供标准技能入口、Windows 初始化脚本和 Codex / Claude Code / OpenClaw 适配指引。
- 优先复用 API；加入 GET-only Reader、安全分页与无凭据日志错误处理。
- 提供隔离 Playwright MCP 配置及工具过滤，支持大体积页面响应。
- 默认核心讲义/公告，补充活动预览后确认；输出有来源的离线图文 HTML。
- 提供 PDF 原图提取、HTML 搜索/放大/打印、合成演示，以及确认后考后清理流程。
- 14 项本地测试通过；实际 Windows 依赖安装、MCP 和离线界面冒烟测试通过。
- 添加原创横幅、中文项目主页、Apache-2.0、NOTICE 与第三方声明。

已知范围：Claude Code 真实课程端到端、OpenClaw 实机、ARM64 与全新系统的全部下载分支尚未完整验证。OAuth 需要机构批准的连接器，本包不是多用户 OAuth 服务。
