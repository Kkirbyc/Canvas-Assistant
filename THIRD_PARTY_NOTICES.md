# 第三方组件与出处

本仓库没有把第三方程序重新声明为 Apache-2.0。项目自己的 LICENSE/NOTICE 适用于原创部分；安装的第三方组件保留自身许可证与声明。

| 组件 | 用途 | 来源 / 授权说明 |
|---|---|---|
| Microsoft Playwright MCP / Playwright | 隔离浏览器访问；固定 MCP 版本及 npm lock | https://github.com/microsoft/playwright-mcp · Apache-2.0，实际依赖以对应版本 LICENSE 为准 |
| Python-Markdown | 本地 Markdown → HTML | https://github.com/Python-Markdown/markdown · BSD-3-Clause |
| PyMuPDF / MuPDF | PDF 文本与原始页面图片提取 | https://pymupdf.readthedocs.io/ · AGPL / 商业授权体系；安装、结合使用和再分发应遵守对应授权，项目 Apache-2.0 不替代这些义务 |
| Node.js | 缺少 Node 时下载官方 portable runtime | https://nodejs.org/ · Node.js 及所含组件的相应许可证 |
| Python | 本地辅助脚本运行时 | https://www.python.org/ · PSF 及所含组件的相应许可证 |
| GitHub Actions checkout / setup-python | 仓库持续集成 | GitHub 官方 actions 仓库及各自许可证 |

本仓库仅记录第三方版本/下载与配置方法，不在发布 ZIP 中捆绑上述运行时二进制或 node_modules。依赖下载后应保留随附 LICENSE/NOTICE。

README 使用 shields.io 徽章服务。原创横幅与合成演示图由本项目制作，按本项目许可证提供；它们不是老师讲义或 Canvas 官方 Logo。

学校的 PPT、PDF、视频、作业和试题不随本包发布，其版权与访问条件由原权利人决定。项目开源不授权传播课堂材料。
