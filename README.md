# api-convention

会展大屏后端（FastAPI + SQLite）

## 启动

1. 双击 `start.bat`，或：
   `.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
2. 前端：`cd ../convention-3d` → `npm run dev`（默认 http://localhost:3000）
3. 健康检查：`GET http://127.0.0.1:8000/health`

## 演示账号

- 用户名：`admin`
- 密码：`admin123`

## 统一响应信封

所有业务接口（含登录、错误）返回：

```json
{ "code": 0, "msg": "ok", "data": ... }
```

| 场景 | HTTP | code | data |
|---|---|---|---|
| 成功 | 200 | 0 | 业务数据（列表/对象） |
| 未登录/密码错误 | 401 | 401 | null |
| 未找到 | 404 | 404 | null |
| 参数错误 | 422 | 422 | 校验细节（可选） |

`GET /health` 同样返回信封：`{"code":0,"msg":"ok","data":{"status":"ok"}}`。

## 登录与鉴权

- `POST /api/auth/login`，JSON：`{"username":"admin","password":"admin123"}`
- 成功示例：

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "username": "admin"
  }
}
```

- 业务接口需 Header：`Authorization: Bearer <token>`
- 公开：`GET /health`、`POST /api/auth/login`
- 签名密钥只放项目根 `.env` 的 `SECRET_KEY`（已在 `.gitignore`，不进 Git）。换密钥会使已发出的 token 全部失效。
- token 有效期：`.env` 里 `ACCESS_TOKEN_EXPIRE_MINUTES=1440`（24 小时）。过期后业务接口返回 401，前端会清掉本地 token 并弹出登录层。

## PowerShell 自测示例

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/auth/login `
  -ContentType 'application/json' `
  -Body '{"username":"admin","password":"admin123"}'

# 信封：token 在 data 里
$login.data.access_token

Invoke-RestMethod -Uri http://127.0.0.1:8000/api/halls `
  -Headers @{ Authorization = "Bearer $($login.data.access_token)" }
```

## 常用业务接口

- GET /api/halls
- GET /api/devices
- GET /api/alarms
- GET /api/work-orders
- GET /api/energy
- GET /api/parking
- GET /api/crowd
- GET /api/emergency
- GET /api/heatmap?hall=1号馆

## Docker启动
开发仍用 start.bat 和前端的 npm run dev（页面在 http://localhost:3000）。要按上线方式跑时，先在 convention-3d 执行 npm run build，再回到上一级 convention 目录执行：docker compose up -d --build
页面改为 http://localhost:8080，接口由 Nginx 转发到后端。停掉这一组用 docker compose down。.env 由 docker-compose.yml 的 env_file 传进容器，不要打进镜像。

## 环境变量
SECRET_KEY 签发登陆token
ALGORITHM  签名算法，保持 HS256
ACCESS_TOKEN_EXPIRE_MINUTES  token 有效分钟数，1440 就是 24 小时
DEEPSEEK_API_KEY  对话用的密钥。空着时对话接口不能调用模型
DEEPSEEK_BASE_URL  模型地址，默认 https://api.deepseek.com

## AI
能做的是：查告警、用电用水、设备在线/离线/故障、某个场馆的面积和介绍；切换综合态势、安防态势、设备运行、能源管理、会展信息；回到总览、显示场馆标签、定位到 1–16 号馆或三个登录厅、展开或收起楼层、开关人流热力图、打开设备分类、显示某类设备的三维标签。
不能做的是：改天气、切换昼夜、漫游；编造数字、时间、面积、容量；改数据库里的数据；开关真实设备；生成或修改三维代码。画面类工具只负责校验指令，场景变化由浏览器里的前端执行。
