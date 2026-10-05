# Windows 首次安装与更新

适用于已安装、可调用本地工具的 Codex、Claude Code、OpenClaw。普通网页聊天不等于本地代理环境。本包不安装 AI 宿主，不处理订阅或模型 API Key。

## 给同学的最短使用方式

1. 解压完整 ZIP，保留 `canvas-study` 文件夹结构。先打开包内 `开始使用.html`。
2. 在自己的 AI 工具中说：“请阅读这个目录的 SKILL.md，安装 Windows Canvas 学习技能；使用我的工具类型进行配置。”也可手动运行下面命令。
3. 首次允许所需安装；如果没有 Python，需要官方 winget 用户级安装后重新打开终端。不要为了运行脚本修改整机执行策略。
4. 重新加载 AI 工具，使 skill/MCP 生效。验证连接工具存在，再本人登录 Canvas/MFA。
5. 说：“帮我准备 XX 课 XX 日的考试，先看讲义和公告。”按照预览结果选择是否纳入 Lab/PA。

## 命令

在解压的 `canvas-study` 目录中，用 PowerShell 执行；HostName 选 `codex`、`claude`、`openclaw` 或 `generic`：

```powershell
# 仅预览，不安装、不写宿主配置
.\setup.ps1 -HostName claude
# 安装技能和用户级依赖；自动选择 API 环境变量或浏览器路径
.\setup.ps1 -HostName claude -Apply
# 已有可用的 Canvas API，不安装浏览器 MCP
.\setup.ps1 -HostName codex -Mode api -Apply
# 没有 API，显式走浏览器
.\setup.ps1 -HostName codex -Mode browser -Apply
```

若 PowerShell 阻止下载的脚本，先核对来源和 `SHA256SUMS.txt`；可以由本人通过文件“属性→解除锁定”处理下载标记。组织执行策略禁止时请遵从管理员规则，不自动设为 Bypass/Unrestricted。Python 已安装时，也可直接用 `python scripts/setup.py --host claude --apply`。

默认课程根目录是 `%USERPROFILE%\CanvasStudy`；可用 `-DataRoot` 指定其他**用户可写**目录。不会要求管理员权限或写入 Program Files。安装会创建：

- 宿主用户级 `skills/canvas-study`（现有不同内容不覆盖）。
- `runtime/python/`：隔离的文档工具环境。
- 非 OpenClaw 浏览器模式下的 `runtime/browser/`、Playwright 配置及 MCP 片段。
- 若缺少合格 Node，下载固定版官方 Windows portable ZIP并核对官方 SHA-256；不更改系统 PATH。
- 优先用已有 Edge；没有 Edge 才下载 Playwright Chromium 至该 runtime。
- `installation.json`：安装路径和模式，不含账号凭据。

安装脚本不修改 sandbox、allow-all 或执行审批设置。普通任务无需每步再问；网络、受保护目录、浏览器启动等可能仍被宿主要求批准。这些审批不能由 skill 取消。

`auto` 只能检测当前进程已有 `CANVAS_TOKEN`；它不会搜寻凭据，也不会发现所有宿主连接器。若代理已确认可用连接器，应选择 `api` 并复用连接器，而非创建新 Token。Token 无效时报告身份验证失败，再转浏览器；不能反复尝试登录。

安装后 PDF/HTML 等脚本应使用隔离环境的 Python，不是系统 Python：

```powershell
$studyInstall=Get-Content "$env:USERPROFILE\CanvasStudy\installation.json" -Raw | ConvertFrom-Json
& $studyInstall.python "$($studyInstall.skill)\scripts\render.py" --input "$env:USERPROFILE\CanvasStudy\courses\123\notes" --output "$env:USERPROFILE\CanvasStudy\courses\123\site"
```

若使用自定义 DataRoot，相应替换 installation.json 的位置。输出目录需为空或不存在；更新时先生成新版本供核对，不悄悄覆盖正在使用的网页。

## 更新与撤销

重复运行相同版本可复用依赖，但不会悄悄覆盖不同 skill。若同名目录已有定制内容，先比较后决定升级或另行保留，不使用 `--force` 覆盖。已有 `canvas-study` MCP 条目保留并要求核对；“保留”不等于已验证其指向正确。

撤销时先查看 `installation.json`：只移除本次命名的 skill/MCP 注册；删除 runtime 或原材料需要具体清单和用户确认。`codex mcp remove canvas-study` / `claude mcp remove canvas-study` 应在用户明确要求卸载时执行。不要删除宿主整个配置，不要删除 `courses/` 复习资料。

## 验证顺序

环境依赖 → 宿主发现 skill → MCP/原生浏览器工具可见 → 公共学校登录页可打开 → 本人登录完成 → 指定课程可读 → 一份讲义可下载 → HTML 可离线打开。

这八个步骤分别记录，不要用“安装成功”代替全部连接验证。API 测试和浏览器登录测试需使用者自己的授权，分发包不包含测试账号。
