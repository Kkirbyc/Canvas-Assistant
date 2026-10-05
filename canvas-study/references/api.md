# Canvas API：已有连接优先

## 选择认证方式

1. 宿主已有获授权的 Canvas connector：检查可读范围，直接复用，无需要求新 Token。
2. 学校提供 OAuth integration：使用学校批准的 developer key、回调地址和最小必要读取权限。OAuth 授权、回调验证、Token 刷新/撤销由受信连接器完成；本包不是多用户 OAuth 服务，不内置 client secret，也不承诺任意学校免配置登录。
3. 学校允许个人 access token：学生可在 Canvas 个人设置的 Approved Integrations 创建，仅供本人本地使用。学校禁用时直接走浏览器，不能绕过管理员限制。

学生不要把 Token 发到聊天、参数、共享文档或压缩包。`canvas_api.py` 默认用终端隐藏输入读取，进程结束即不保留；也可使用使用者已经自行配置的进程 `CANVAS_TOKEN`。持久化到凭据库/用户环境变量必须另行授权，本包不自动持久化。

## 验证与读取

`--origin` 必须是学校真实 Canvas HTTPS origin。例如 CSU 是 `https://colostate.instructure.com`，不是学校介绍页 `canvas.colostate.edu`。首次使用者确认学校入口，不将凭据发给搜索引擎。

```powershell
python scripts/canvas_api.py --origin https://SCHOOL.instructure.com --kind profile --out C:\Study\private\profile.json
python scripts/canvas_api.py --origin https://SCHOOL.instructure.com --kind courses --out C:\Study\private\courses.json
python scripts/canvas_api.py --origin https://SCHOOL.instructure.com --kind modules --course 123 --out C:\Study\private\modules.json
python scripts/canvas_api.py --origin https://SCHOOL.instructure.com --kind module-items --course 123 --resource 456 --out C:\Study\private\module-456.json
python scripts/canvas_api.py --origin https://SCHOOL.instructure.com --kind announcements --course 123 --out C:\Study\private\announcements.json
```

同样支持 course（syllabus）、pages/page、files/file、assignments/assignment、quizzes（仅已授权列表）。不提供 POST/PUT/DELETE、start attempt、submission 或任意 URL 执行入口。输出已有时拒绝覆盖，请使用新快照文件名。

Reader 跟随同 origin 的 API Link 分页，检测循环，拒绝带用户名密码、跨 origin 和非 HTTPS 分页；不跟随认证请求重定向，错误只显示 HTTP 状态，不输出响应中的凭据。401/403 是认证/授权失败，不等于课程没有资料；停止重试并解释 API 或浏览器替代路径。

**文件下载边界：**Reader 读取文件元数据，不是通用二进制下载器。对已授权 file 资源的下载链接，使用宿主获授权的下载工具或浏览器。跳到 CDN/对象存储时不能转发 Canvas Authorization header；signed URL 只在本机私有流程中使用，不写入来源报告、公共搜索或分发包。下载失败不能伪装成已读。

Announcements API 有默认日期范围；本 Reader 显式指定 1970-01-01 至当前 UTC 时间并分页，避免只取默认的近期公告。使用其他 connector 时也要检查日期窗口，不能把默认结果当成全量。New Quizzes、Echo360 等 LTI 可能需要独立网页登录，API 能读取 Canvas 元数据不等于读到了外部内容。

## 官方依据

- https://developerdocs.instructure.com/services/canvas/oauth2/file.oauth
- https://developerdocs.instructure.com/services/canvas/resources
- https://developerdocs.instructure.com/services/canvas/basics/file.pagination

原始 API JSON 可能包含私人资料和临时下载地址，只保存在课程私有目录。面向用户的来源索引只保留稳定资源 ID 和无凭据的 canonical URL。
