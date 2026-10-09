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
