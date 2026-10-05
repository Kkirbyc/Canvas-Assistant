# 验证记录

公开首版：`1.0.0-preview.1`。验证环境为 Windows x64；使用合成数据，不向发布包加入个人账号或课程材料。

## 已完成

- 14 项行为测试：GET-only API、认证头、分页、跨域拒绝、循环拒绝、非法 origin、重定向拒绝、工具过滤、100 KB 代理响应、ZIP 路径保护、Windows CLI shim 安全处理、HTML 内容转义、答案隔离和链接验证。
- 独立目录的实际安装：Python 文档环境、固定版本 Playwright MCP；使用已有 Node/Edge。
- 实际 MCP：初始化、过滤 tools/list、拒绝 evaluate、隔离 headless 浏览器打开 about:blank、snapshot、关闭。
- 合成 PDF 文本提取、原图渲染与离线 HTML 生成。
- 离线页面：图片放大/Escape、搜索、375/768/1440 布局；无远程运行依赖。
- Codex 与 Claude Code 的 MCP 配置参数通过本机 CLI help 核对。
- 独立只读代码审阅及问题修正；发布包检查本地链接、私人路径标记、ZIP 完整性和 SHA-256。

## 不代表已经验证

- 没有用其他同学账号跑过 API、OAuth 或所有宿主的真实课程端到端流程。
- OpenClaw 本机未安装，只核对官方文档与接入边界。
- 缺 Python、缺 Node、缺 Edge 的全部组合未在完全空白 Windows 上逐一测试；ARM64 未测试。
- 学校 MFA、禁止 Token、外部 LTI/视频平台、组织网络策略可能改变实际流程。

本记录不替代首次使用的现场连接检查。每次升级应注明验证版本及新变化，不能把之前的结果无限外推。
