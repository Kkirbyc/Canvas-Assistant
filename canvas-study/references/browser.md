# 无 API 时的浏览器流程

优先复用任务已有的独立、授权浏览器。Codex/Claude Code 使用安装器配置的官方 `@playwright/mcp@0.0.83`；无 Node 自动下载 portable Node，有 Edge 则复用，没有 Edge 才下载 Chromium。版本固定，安装保留 npm lock。不要随便改用第三方登录插件。

本包生成配置：可见窗口、isolated context、Chromium sandbox 开启、关闭 session 保存和 WebMCP、输出放在私有课程根目录。没有导入日常浏览器 profile。关闭/重启隔离会话可能丢失 Canvas 登录，因此完成阅读前不要随意关闭。

Codex/Claude 的自动注册经 `mcp_browser_proxy.py` 转发：只列出导航、snapshot、截图、查找、窗口/标签及基本点击选择等工具；拒绝工具名不在名单中的调用，包括 evaluate、上传和网络/console 工具。点击和导航仍可能产生网站操作，因此它是工具范围过滤，不是强制只读的网页防火墙。

1. 重载宿主，确认 MCP tools/list 可用。若只配置了文件而工具未出现，报告“配置完成，等待重载”。
2. 打开使用者确认的学校官方 Canvas 登录页。
3. 告知学生亲自输入账号、密码和 MFA；此时暂停 snapshot/screenshot/network inspection。收到“已登录”后再读取页面。
4. 验证课程身份，使用正常导航、课程 Modules、Announcements 和文件下载。分页完整检查，锁定资料不绕过。
5. 外部录播平台用页面内授权跳转，读取可用字幕，明确缺失；不读取浏览器 cookie 数据库，不导出 storageState。
6. 下载后把确属当前课程的文件登记到 inventory/manifest，必要副本放在该课程目录。不要混入其他课程下载或账户配置。

浏览器工具不是强制只读的 API：click 可提交表单，也可能触发“完成”。只进行阅读必需交互，禁止提交测验、发帖、签到/完成或更改课程设置；访问页面本身可能记录访问日志。

OpenClaw 用其原生 managed browser，见 hosts.md 的 profile 与持久化区别。未经核对不要把 MCP JSON 粘到 OpenClaw Gateway 配置。

## 常见问题

| 问题 | 操作 |
|---|---|
| Node/npm 未找到 | 重用安装器提供的 portable Node；不要下载随机打包运行时 |
| 包下载被组织网络阻止 | 显示失败原因；按宿主流程申请本任务网络权限，不关闭 TLS 校验 |
| Edge 不存在 | 安装器下载任务目录内的 Chromium |
| 工具列表无浏览器 | 重载宿主，核对 CLI/MCP 注册；不要声称已连接 |
| MFA 或学校登录失败 | 由学生本人解决；不反复猜密码，不绕过验证 |
| GUI/浏览器启动被沙箱拦截 | 使用宿主正式审批；不得通过另一个工具绕过 |
| 只能看到课程目录 | 标记 listed，继续打开正文和授权下载；不要宣称已完整阅读 |
| PDF 无文本 | 需要 OCR 或视觉检查；工具缺失就明确缺口，不把空文本视为无内容 |
| 只有 PPTX | 通过已批准的 Office/PDF 导出读取，或使用者导出；不自动安装 Office |
| 浏览器更新后功能变化 | 验证 pinned MCP 与浏览器兼容后再升级；不要静默换最新版 |
