# 阶段 A：鉴权（后端自学清单 / Agent 交接）

> 更新时间：2026-10-01  
> 协作规则（仍有效）：**前端**由 Agent 改、用户审；**后端**由用户自己敲代码，Agent 只教契约/为什么/验收，不代写完整实现。  
> 前端登录门禁与 Bearer 拦截已就绪，契约如下。你负责把后端按可上线标准实现。

---

## 当前进度（交接用）

### 总览

| 天 | 内容 | 状态 |
|---|---|---|
| Day1 | 依赖 + `.env` + `app/config.py` | **已完成** |
| Day2 | User 模型 + `security.py` + 种子用户 + `main` 挂载 | **基本完成，有 1 处契约偏差** |
| Day3 | `schemas` + `POST /api/auth/login` + `/docs` 测通 | **未开始**（文件空） |
| Day4 | `get_current_user` + 业务路由强制 Bearer | **未开始** |
| Day5 | README + 前后端联调 | **未开始** |

### 已完成（磁盘已核实）

- [x] `requirements.txt` 已含：`python-jose[cryptography]`、`passlib[bcrypt]`、`bcrypt==4.0.1`、`pydantic-settings`
- [x] 虚拟环境已能 `import jose, passlib, pydantic_settings`
- [x] 项目根 `.env` 已配置真实 `SECRET_KEY`、`ALGORITHM=HS256`、`ACCESS_TOKEN_EXPIRE_MINUTES=480`（已在 `.gitignore`，**交接文档不要粘贴密钥**）
- [x] `app/config.py` 用 pydantic-settings 读取上述三项；验收：`settings.ALGORITHM` / `480` 正常
- [x] `app/security.py`：`hash_password` / `verify_password` / `create_access_token`；验收：`verify_password('admin123', hash_password('admin123'))` → `True`
- [x] `app/models.py` 已有 `User`：`id`、`username`(unique+index)、`hashed_password`、`is_active`、`created_at`
- [x] `app/seed.py` 已有 `seed_users_if_empty()`，`main.py` 已 `import User` 并调用该种子函数

### 未完成 / 空文件

- [ ] `app/schemas.py`（空）
- [ ] `app/deps.py`（空）
- [ ] `app/routers/auth.py`（空）
- [ ] `app/routers/__init__.py`（**缺失**，需要空文件，否则包导入失败）
- [ ] `main.py` 尚未 `include_router` 登录路由
- [ ] 业务 `/api/*` 尚未加 `Depends(get_current_user)`
- [ ] README 演示账号与 curl 说明

### 必须立刻纠正的偏差

种子密码与前端契约不一致：

- 契约 / 前端登录页演示账号：`admin` / **`admin123`**
- 当前 `seed_users_if_empty` 写入的是：`admin` / **`123456`**

下一位（或本人继续写 Day3 前）应把种子明文改成 `admin123`。若库里已有旧用户行，改代码后不会自动更新（函数是 if empty）；需要删 `users` 表记录或删库重建后再 seed。

### 下一步（Day3，用户自己敲）

1. 新建空文件 `app/routers/__init__.py`
2. 写 `app/schemas.py`：`LoginIn(username, password)`、`TokenOut(access_token, token_type="bearer", username?)`
3. 写 `app/routers/auth.py`：`POST /login`（router 的 `prefix` 与 `main` 挂载后完整路径必须是 `/api/auth/login`）
4. `main.py`：`app.include_router(...)`
5. `/docs` 或 curl 验收登录成功/失败

然后再做 Day4 保护业务接口。

### 前端现状（勿回退）

鉴权前端已还原并等待后端登录：

- `src/utils/conventionAuth.js`、`src/store/modules/auth.js`、`src/api/http.js`、`src/api/convention.js`
- `src/components/commonVue/LoginGate.vue`、`App.vue`、`comheader.vue` 退出
- Token 键名：`convention_access_token` / `convention_username`（不要用 ICC 的 `src/utils/auth.js`）
- 未登录时门禁会挡住大屏，属预期，直到后端 login 可用

### 工程注意

- Python：本机 `.venv` 指向 Python 3.12；`start.bat` 可双击启动
- 端口 8000 若 WinError 10013/10048：先查占用进程，不是权限问题
- Vite 代理 `/api` → `http://127.0.0.1:8000`（不 strip `/api`）
- **不要**把响应改成统一 `{code,msg,data}` 信封，会破坏现有前端解析
- Agent **不要**代写完整后端鉴权实现，除非用户明确改口

---

## 接口契约（必须对齐，前端已按此调用）

### POST `/api/auth/login`
- 请求 JSON：`{ "username": "admin", "password": "admin123" }`
- 成功 200：`{ "access_token": "<jwt>", "token_type": "bearer", "username": "admin" }`
- 失败 401：`{ "detail": "用户名或密码错误" }`（FastAPI 默认即可）

### 受保护接口
- 除 `GET /health`、`POST /api/auth/login` 外，现有 `/api/*` 业务接口均需：
  - Header：`Authorization: Bearer <access_token>`
  - 无/坏/过期 token → **401**

## 你要学什么 / 为什么

1. **密码哈希（bcrypt）**：库泄露也不能直接登录；永远不存明文。
2. **JWT**：无状态通行证，适合 API；用 `SECRET_KEY` 签名防篡改，设 `exp` 过期。
3. **Depends(get_current_user)**：每个受保护路由先验票再办事，避免复制粘贴校验代码。
4. **配置与密钥外置**：`SECRET_KEY` 放 `.env`（已在 `.gitignore`），上线可换环境变量。
5. **User 表 + 种子管理员**：演示账号可重置，符合真实项目习惯。

## 建议你自己敲的文件（可按此拆）

```text
app/config.py          # ✅ 已完成：读 SECRET_KEY、过期分钟、算法
app/security.py        # ✅ 已完成：hash / verify / create_access_token（decode 可放 Day4）
app/schemas.py         # ⬜ LoginIn / TokenOut
app/deps.py            # ⬜ get_current_user（get_db 已在 database.py）
app/routers/__init__.py# ⬜ 空文件（缺失）
app/routers/auth.py    # ⬜ POST /api/auth/login
app/models.py          # ✅ 已有 User
app/seed.py            # ⚠️ 有 seed_users_if_empty，但密码需改为 admin123
requirements.txt       # ✅ 鉴权依赖已加
README.md              # ⬜ 演示账号、登录示例 curl
```

## 按天自学节奏（代码必须你自己写）

- Day1：✅ 装依赖；写 config；理解 JWT 三部分与 SECRET_KEY
- Day2：✅ User 模型 + 哈希工具 + 种子 admin（⚠️ 密码改成 admin123）
- Day3：⬜ 登录接口；`/docs` 测通
- Day4：⬜ `get_current_user`；给业务路由加 Depends；无 token 必须 401
- Day5：⬜ README；与前端联调（登录门禁 → 五页有数；退出 → 再登录）

## 可上线底线检查

- [x] 密码非明文（哈希工具已通；种子写入的是哈希）
- [x] `.env` 不进 Git
- [ ] 登录失败 401，不返回 200
- [ ] 业务接口强制 Bearer
- [x] token 有过期时间（create_access_token 已写 exp）
- [ ] README 有演示账号与启动说明
- [ ] 前端登录后大屏数据正常
- [ ] 种子账号密码与契约一致：`admin` / `admin123`

## 联调命令（后端写完后自测）

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"

curl http://127.0.0.1:8000/api/halls ^
  -H "Authorization: Bearer <粘贴token>"
```
