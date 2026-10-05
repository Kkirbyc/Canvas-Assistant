# 宿主适配与兼容边界

本包共用一份标准 `SKILL.md` 和本地脚本；配置入口不是跨平台通用的。首版范围是 Windows，不能承诺每个版本零配置。

| 宿主 | Skill 安装位置 | 访问路径 | 首版验证范围 |
|---|---|---|---|
| Codex | `CODEX_HOME/skills/canvas-study`，默认 `~/.codex/skills/canvas-study` | 已有 Canvas API；或官方 Playwright MCP stdio | CLI 配置语法已在本机核对；此前 Windows Canvas 浏览器路径已实用验证；本包脚本测试见验证报告 |
| Claude Code | `~/.claude/skills/canvas-study` | 已有 API；或官方 Playwright MCP stdio | 本机 `claude mcp add --help` 已核对；未使用同学账号做端到端课程读取 |
| OpenClaw 原生 Windows Gateway | 默认 `~/.openclaw/skills/canvas-study`，支持 `OPENCLAW_STATE_DIR` 覆盖 | 已有 API；或已启用的 managed browser | 官方路径/能力说明已核对；本机无 OpenClaw，需首次现场验证 |
| Windows Hub + WSL/远程 Gateway | Skill 应装在实际 Gateway 发现的位置 | Gateway 的浏览器，或已授权 Windows browser node | 本安装器不自动安装 WSL、配置远程 Gateway 或启用 node；不能用 Windows 本地目录冒充 Gateway 已安装 |
| 其他能读 Agent Skills 的工具 | 由宿主文档指定 | 支持 stdio MCP 则导入生成的片段；否则已有 API/浏览器工具 | 通用核心可复用，工具接入需核对 |

## Codex / Claude Code

浏览器模式安装器使用各自官方 CLI 注册 `canvas-study`，不会编辑全局权限文件；CLI 缺失时生成 `runtime/mcp-server.json` 供宿主导入。

```text
codex mcp add canvas-study -- <python.exe> <mcp_browser_proxy.py> <node.exe> <mcp/cli.js> --config <playwright.json> --no-webmcp
claude mcp add --transport stdio --scope user canvas-study -- <python.exe> <mcp_browser_proxy.py> <node.exe> <mcp/cli.js> --config <playwright.json> --no-webmcp
```

重新加载后检查工具列表，再访问学校登录页。浏览器 MCP 有可能提供写入/执行能力，配置名称不使它成为强制只读；只使用导航、snapshot、截图、下载和必要基本交互。宿主支持细粒度工具 allowlist 时，仅开放这些工具，不加 blanket shell/evaluate 权限。账号输入和 MFA 由学生在可见窗口手动完成。

Claude Code 与 Claude 网页聊天不同。Claude Desktop 可支持自己的 MCP/skills 机制，但不在本包自动安装适配的承诺范围内，不能把 Claude Code 路径直接写到 Desktop 配置。

## OpenClaw

先确认代理实际运行位置：Windows CLI/Gateway、Windows Hub 托管的 WSL Gateway、还是远程 Gateway。Windows 官方文档目前提供 Windows Hub 与原生 CLI/Gateway，WSL 也是受支持的路径；不要假设所有 OpenClaw 都是原生 Windows。

已有可用 API：使用相同 GET-only 流程。没有 API：优先使用宿主的 managed browser；它本身由 Playwright 等浏览器能力支撑，不需要另装一份 MCP 才能读取 Canvas。安装器因此不会对 OpenClaw 强行写入 Codex/Claude 的 MCP 配置。

浏览器必须是独立的 agent-managed profile，不能选择附着个人日常浏览器的 `user` profile。先通过本机 `openclaw browser --help` 和可用工具检查 profile 创建/选择方式，按当前版本的官方 Browser setup/profiles 指引操作；不要猜测旧 CLI 参数。如果启用插件、node、远程访问或 Gateway 重启会扩大权限，先展示具体改动再取得授权。

**持久化区别：**OpenClaw managed profile 可能保存登录状态。首次登录前说明是否会留存 cookie，并取得单独授权；用户不同意时，只使用该版本支持的临时隔离会话，否则明确停止并提供 API/本地课程导出替代，不能偷偷连接日常 Chrome。不要以 `noSandbox` 或关闭安全策略修复启动问题。

若 browser 工具未安装/未启用，本包将其标为待配置，不声称已连接。可复用已安装的宿主浏览器组件；宿主需要额外官方插件时，核对版本后由代理安装本任务所需组件。WSL/Windows Hub 的系统级安装不属于本包自动初始化范围。

## 文档依据

- Codex MCP：https://developers.openai.com/codex/mcp
- Claude Code MCP：https://code.claude.com/docs/en/mcp （本次网页访问返回 403，命令参数用本机 CLI help 交叉核对）
- Claude Code Skills：https://code.claude.com/docs/en/skills （不同宿主版本以实际发现结果为准）
- 官方 Playwright MCP 的 Claude/Codex 配置：https://github.com/microsoft/playwright-mcp
- OpenClaw Windows：https://github.com/openclaw/openclaw/blob/main/docs/platforms/windows.md
- OpenClaw Skills：https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md
- OpenClaw Browser：https://github.com/openclaw/openclaw/blob/main/docs/tools/browser.md

核对日期：2026-10-04。文档兼容与真实账户端到端验证分别标记，不以文档存在冒充实测。
