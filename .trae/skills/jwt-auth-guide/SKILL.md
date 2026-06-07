---
name: "jwt-auth-guide"
description: "JWT 认证系统实战指南。包含签名验证、token 刷新、前端拦截器、安全加固的全链路实现。适用于 FastAPI + Supabase + React 项目。Invoke when user asks about JWT auth, token refresh, or auth security fixes."
---

# JWT 认证系统实战指南

> 🎯 目标：从零搞懂 JWT 完整链路，边写代码边学
> 🧩 前置知识：Python 基础 + React 基础
> ⏱ 预估时间：2-3 小时
> 📁 项目：Signal（FastAPI + React + Supabase）

---

## 目录

1. [JWT 是什么？为什么需要它？](#1-jwt-是什么为什么需要它)
2. [项目当前 JWT 状态评估](#2-项目当前-jwt-状态评估)
3. [P0 修复：UUID 直通验证漏洞](#3-p0-修复uuid-直通验证漏洞)
4. [P1 修复：前端 401 拦截器 + Token 自动刷新](#4-p1-修复前端-401-拦截器--token-自动刷新)
5. [P2 修复：前端 Token 过期预判](#5-p2-修复前端-token-过期预判)
6. [P3 修复：登录接口单独限流](#6-p3-修复登录接口单独限流)
7. [完整链路验证清单](#7-完整链路验证清单)

---

## 1. JWT 是什么？为什么需要它？

### 1.1 一句话说清

> JWT = JSON Web Token，是一张**带签名的身份证**。
> 用户登录后服务器发一张"身份证"（token），用户后续请求带着它，服务器验一下签名就知道是谁，不用每次查数据库。

### 1.2 JWT 长什么样？

看一眼实际数据。打开浏览器 DevTools → Application → Local Storage → `signal_auth_token`，你会看到一串东西：

```
eyJhbGciOiJSUzI1NiIsImtpZCI6InR0dUR...（超级长）
```

把它复制到 [jwt.io](https://jwt.io) 粘贴，就能看到它的三段结构：

```
header.payload.signature
```

| 段 | 内容 | 例子 |
|----|------|------|
| **header** | 算法类型、key ID | `{"alg":"RS256","kid":"ttud..."}` |
| **payload** | 用户信息、过期时间 | `{"sub":"用户UUID","exp":1687000000,"aud":"authenticated"}` |
| **signature** | 签名（防篡改） | 乱码，但服务器能验 |

**关键字段：**
- `sub` (subject) — 用户唯一 ID
- `exp` (expiration) — 过期时间戳（秒），Supabase 默认 1 小时
- `aud` (audience) — 受众，固定 `"authenticated"`
- `iat` (issued at) — 签发时间

### 1.3 为什么不能只传 user_id？

```
❌ 错误做法：
  前端 localStorage = "user-123"
  请求 header = Authorization: Bearer user-123
  后端直接拿 "user-123" 当用户ID

  问题：任何人都能伪造 user_id，冒充别人。

✅ 正确做法：
  前端 localStorage = eyJhbGciOiJSUzI1NiIs...
  请求 header = Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
  后端用公钥验证签名 → 只有 Supabase 签发的才有效
```

**我们项目之前的坑**：`jwt.decode(token, options={"verify_signature": False})` — 跳过签名验证，等于 ‍♂️ 的身份证不防伪。

### 1.4 RS256 vs HS256 区别

| | RS256（我们用的） | HS256 |
|--|------------------|-------|
| 密钥 | 公钥 + 私钥（一对） | 一个密钥 |
| 签名 | 私钥签名，公钥验证 | 同一个密钥签名+验证 |
| 安全风险 | 私钥泄露才危险 | 任何能验证的人也能伪造 |
| 多服务 | 公钥可以公开，安全 | 所有服务共享密钥 |
| 本项目 | ✅ Supabase 自动管理 | ❌ 不适用 |

---

## 2. 项目当前 JWT 状态评估

### 2.1 完整链路鸟瞰

```
┌─────────────────────────────────────────────────────────────────┐
│                   登录流程                                        │
│                                                                   │
│ 用户输入邮箱密码                                                   │
│     │                                                             │
│     ▼                                                             │
│ supabase.auth.signInWithPassword()                                 │
│     │                                                             │
│     ▼                                                             │
│ Supabase 返回：{ access_token, refresh_token, user }                │
│     │                                                             │
│     ▼                                                             │
│ onAuthStateChange 触发 → setToken(access_token) → localStorage      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   请求流程                                        │
│                                                                   │
│ request() → getAuthHeader() → localStorage 读 token               │
│     │                                                             │
│     ▼                                                             │
│ fetch(/api/xxx, { headers: { Authorization: Bearer <token> } })   │
│     │                                                             │
│     ▼                                                             │
│ FastAPI → verify_token() → JWKS 公钥验签 → 返回 user_id            │
│     │                                                             │
│     ▼                                                             │
│ 路由处理 → 返回数据                                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 当前代码架构

```
前端：
  token.js          ← 统一读写 localStorage
  AuthContext.jsx    ← 监听 Supabase auth 状态变化，写 token
  client.js          ← 每次请求读 token，拼 Authorization header
  api/               ← 各个 API 调用

后端：
  jwt_verify.py      ← JWKS 公钥验证签名
  auth.py            ← get_user_id() 依赖注入
  kb.py              ← get_current_user()（支持 ?token= 参数）
  main.py            ← 限流中间件
```

### 2.3 已做到的（✅）

| 环节 | 状态 | 关键代码 |
|------|------|---------|
| 签名验证 | ✅ RS256 + JWKS 公钥 | `jwt_verify.py` L59-76 |
| 过期检查 | ✅ `verify_exp=True` | `jwt_verify.py` L67 |
| 公钥缓存 | ✅ 1 小时 TTL | `jwt_verify.py` L25-33 |
| Header+Query 双通道 | ✅ 知识库下载场景 | `kb.py` L28-38 |
| 未登录兜底 | ✅ demo UUID 看公开内容 | `kb.py` L32 |

### 2.4 没做到的（❌）

| P0 | UUID 直通验证 | 任何人传一个合法 UUID 就能冒充 | `jwt_verify.py` L52-55 |
| P1 | 前端无 401 拦截 | token 过期直接报错，不自动刷新 | `client.js` |
| P2 | 前端无到期预判 | 不提前知道 token 快过期了 | `token.js` |
| P3 | 登录接口无限流 | 登录失败次数不限 | `main.py` |

---

## 3. P0 修复：UUID 直通验证漏洞

### 3.1 问题代码

`api/services/jwt_verify.py` L50-55：

```python
# 情况 1：demo 用户
if token == DEMO_USER_ID:
    return DEMO_USER_UUID

# 情况 2：已经是 UUID
if re.match(UUID_PATTERN, token.lower()):
    return token  # ← 漏洞：只要传一个合法 UUID 就放行
```

**原理**：任何人如果知道了任意一个 `user_id`（比如从 API 返回数据里看到了别人的 UUID），直接把这个 UUID 当 token 传，后端就认为他是那个人。

### 3.2 修复方案

```python
def verify_token(token: str) -> Optional[str]:
    """验证 JWT token 并返回 user_id (sub)
    
    验证链路（严格模式）：
      1. demo-user → 返回 demo UUID（仅用于未登录浏览）
      2. JWT → 从 Supabase JWKS 获取公钥验证签名 → 返回 sub
      3. 全部失败 → 返回 None
      
    不再接受裸 UUID 作为认证凭证。
    """
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    # 1. demo 用户（仅限未登录浏览公开内容）
    if token == DEMO_USER_ID:
        return DEMO_USER_UUID
    
    # 2. JWT 验证 — 唯一入口
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        user_id = decoded.get("sub")
        if user_id:
            return user_id
    except jwt.ExpiredSignatureError:
        pass  # token 过期
    except jwt.InvalidAudienceError:
        pass  # audience 不对
    except Exception:
        pass  # 签名不对或其他
    
    return None
```

**改动要点：**
1. 删掉 `UUID_PATTERN` 的正则匹配
2. 所有非 demo-user 的 token 都必须经过 JWT 验证
3. 捕获更具体的异常类型

**为什么保留 demo-user？** 未登录用户需要能浏览公开文档和日报，这个通过固定 UUID 实现，是设计意图不是漏洞。

### 3.3 动手验证

改完代码后验证：

```bash
# 启动测试
python -m pytest tests/ -v

# 验证 fake UUID 被拒
python -c "
from api.services.jwt_verify import verify_token
# 裸 UUID 应该返回 None
assert verify_token('00000000-0000-0000-0000-000000000002') is None
print('✅ 裸 UUID 被拒绝')
# demo 用户仍可通行
assert verify_token('demo-user') == '00000000-0000-0000-0000-000000000001'
print('✅ demo 用户正常')
"
```

### 3.4 你学到了什么

| 知识点 | 说明 |
|--------|------|
| JWT 签名验证 | 不是所有看起来像 token 的东西都能当凭证 |
| 白名单 vs 黑名单 | UUID 是公开信息，不该用来认证——这是设计层面的漏洞 |
| 防御深度 | 认证链路每一步都要问"能不能绕过" |

---

## 4. P1 修复：前端 401 拦截器 + Token 自动刷新

### 4.1 问题代码

`frontend/src/api/client.js`：

```javascript
async function request(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, { headers, ...options });
    // ← 没有任何 401 处理！
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '请求失败');
    }
    return res.json();
}
```

**现状**：token 过期 → 后端返回 401 → `!res.ok` 进入 → 抛错 → 前端页面报错，用户要刷新页面重新登录。

**理想行为**：
```
token 过期 → 请求返回 401
         ↓
  尝试用 refresh_token 换新 token
         ↓
   成功 → 重试原请求 → 用户无感知
         ↓
   失败 → 跳登录页
```

### 4.2 Supabase 的 refresh_token 机制

Supabase 返回的 session 结构：
```json
{
  "access_token": "eyJ...",       // 1 小时有效
  "refresh_token": "RyJ...",       // 长期有效（默认 30 天）
  "expires_in": 3600,
  "token_type": "bearer"
}
```

Supabase SDK 提供了刷新接口：
```javascript
const { data, error } = await supabase.auth.refreshSession();
// 如果 refresh_token 有效，返回新的 access_token
```

### 4.3 修复方案

改造 `request()` 函数，加入 401 拦截 + 自动刷新：

```javascript
// frontend/src/api/client.js

const API_BASE = import.meta.env.VITE_API_URL || '/api';
import { getToken, DEMO_TOKEN, getAuthHeader, setToken, clearToken, isLoggedIn } from '../lib/token';
import { supabase } from '../lib/supabase';

/** 用 refresh_token 换取新的 access_token */
async function refreshAccessToken() {
    try {
        const { data, error } = await supabase.auth.refreshSession();
        if (error) throw error;
        if (data?.session?.access_token) {
            setToken(data.session.access_token);
            return data.session.access_token;
        }
    } catch (e) {
        console.warn('Token 刷新失败:', e.message);
    }
    return null;  // 刷新失败
}

async function request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    const auth = getAuthHeader();
    if (auth) {
        headers['Authorization'] = auth;
    }
    
    // 第一次请求
    let res = await fetch(`${API_BASE}${path}`, { headers, ...options });
    
    // 401 且是已登录用户 → 尝试刷新 token
    if (res.status === 401 && isLoggedIn()) {
        console.log('Token 过期，尝试刷新...');
        const newToken = await refreshAccessToken();
        
        if (newToken) {
            // 刷新成功 → 重试原请求
            headers['Authorization'] = `Bearer ${newToken}`;
            res = await fetch(`${API_BASE}${path}`, { headers, ...options });
            console.log('Token 刷新成功，请求重试完成');
        } else {
            // 刷新失败 → 清除 token，跳登录
            console.warn('Token 刷新失败，跳转登录页');
            clearToken();
            window.location.href = '/login';
            throw new Error('登录已过期，请重新登录');
        }
    }
    
    // 非 401 或已处理完毕
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '请求失败');
    }
    
    return res.json();
}
```

### 4.4 图解：请求链路变化

```
改动前：
  请求 → 401 → 抛错 → 用户看到错误提示
  
改动后：
  请求 → 401 → 检查是否已登录
                  ├─ 已登录 → supabase.auth.refreshSession()
                  │            ├─ 成功 → 重试请求 → 200 ✅
                  │            └─ 失败 → clearToken → 跳登录
                  └─ 未登录 → 抛错（正常行为）
```

### 4.5 动手验证

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 手动测试刷新流程（浏览器控制台）
// 在浏览器 DevTools Console 中执行
import { supabase } from './lib/supabase';
const { data } = await supabase.auth.refreshSession();
console.log(data?.session?.access_token ? '✅ 刷新成功' : '❌ 失败');
```

### 4.6 你学到了什么

| 知识点 | 说明 |
|--------|------|
| 401 语义 | 不是"请求失败"，是"身份过期，请重新认证" |
| 拦截器模式 | 在请求/响应之间插入通用逻辑，避免每个 API 调用都写一遍 |
| refresh token | access_token 短期有效 + refresh_token 长期有效，平衡安全性和用户体验 |
| 静默刷新 | 用户无感知地完成 token 续期，不打断操作 |

---

## 5. P2 修复：前端 Token 过期预判

### 5.1 为什么需要？

当前的 401 拦截是**被动**的——请求发出去，服务器说 401 了才知道过期了。更好的是**主动**预判：

```
被动：请求 → 等待网络 → 401 返回 → 刷新 → 重试
主动：发请求前检查 → 如果快过期了 → 先刷新 → 用新 token 请求
```

### 5.2 修复方案

在 `token.js` 里加一个预判函数：

```javascript
// frontend/src/lib/token.js

// ... 现有代码不变 ...

/**
 * 检查 token 是否即将过期（提前 5 分钟算"即将"）
 * @returns {boolean} true = 需要刷新
 */
export function isTokenExpiringSoon() {
    const token = getToken();
    if (!token || token === DEMO_TOKEN) return false;
    
    try {
        // JWT 的第二段 payload 是 base64 编码的 JSON
        const payloadBase64 = token.split('.')[1];
        const payload = JSON.parse(atob(payloadBase64));
        const exp = payload.exp * 1000;  // 转成毫秒
        const now = Date.now();
        const fiveMinutes = 5 * 60 * 1000;
        
        return (exp - now) < fiveMinutes;
    } catch {
        return false;  // 解析失败就当没过期
    }
}

/**
 * 获取 token 剩余有效时间（分钟）
 */
export function getTokenRemainingMinutes() {
    const token = getToken();
    if (!token || token === DEMO_TOKEN) return -1;
    
    try {
        const payloadBase64 = token.split('.')[1];
        const payload = JSON.parse(atob(payloadBase64));
        const remaining = (payload.exp * 1000 - Date.now()) / 60000;
        return Math.round(remaining);
    } catch {
        return -1;
    }
}
```

### 5.3 JWT 解析原理

JWT 三段结构：
```
eyJhbGciOiJSUzI1NiIsImtpZCI6InR0dUR...   ← header (base64)
.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDEiLCJleHAiOjE...   ← payload (base64)
.签名...   ← signature
```

每段是 base64 编码，可以用 `atob()`（浏览器内置）解码：

```javascript
const payloadBase64 = token.split('.')[1];  // 取第二段
const payload = JSON.parse(atob(payloadBase64));
// payload.exp 就是过期时间戳（秒）
```

### 5.4 可选：在请求前自动刷新

在 `client.js` 的 `request()` 函数开头加预判：

```javascript
async function request(path, options = {}) {
    // ★ 新增：请求前检查 token 是否即将过期
    if (isLoggedIn() && isTokenExpiringSoon()) {
        console.log('Token 即将过期，提前刷新...');
        const newToken = await refreshAccessToken();
        if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`;
        }
    }
    
    // ... 后续请求代码 ...
}
```

这样绝大部分请求都能用"新鲜"的 token 发出去，不会触发 401。

### 5.5 你学到了什么

| 知识点 | 说明 |
|--------|------|
| JWT 解析 | 前端可以解码 payload（因为只是 base64 不是加密），但**不能验证签名**（因为没有私钥） |
| 被动 vs 主动 | 等待错误发生再处理 ↔ 预判错误提前避免 |
| atob/btoa | 浏览器的 base64 编解码函数 |

---

## 6. P3 修复：登录接口单独限流

### 6.1 问题分析

当前所有 API 共用同一个限流策略（每分钟 120 次），登录接口 `/api/auth/login` 没有特殊保护。攻击者可以对登录接口暴力破解密码。

### 6.2 修复方案

在 `main.py` 中，对 `/api/auth/login` 做单独的、更严格的限流：

```python
# api/main.py

# 登录接口单独限流（更严格）
LOGIN_RATE_LIMIT = {
    "max_attempts": 5,        # 每分钟最多 5 次
    "window": 60,             # 1 分钟窗口
    "max_ips": 500,           # 最多追踪 500 个 IP
}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    
    # 放行静态文件
    if path.startswith("/test/") or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/api/proxy"):
        return await call_next(request)
    
    now = time.time()
    
    # 定期清理
    if int(now) % RATE_LIMIT_WINDOW == 0:
        _cleanup_rate_limit_store()
    if len(rate_limit_store) > RATE_LIMIT_MAX_IPS:
        _cleanup_rate_limit_store()
    
    # ★ 新增：登录接口单独限流
    if path == "/api/auth/login":
        login_store[client_ip] = [
            t for t in login_store.get(client_ip, [])
            if now - t < LOGIN_RATE_LIMIT["window"]
        ]
        if len(login_store[client_ip]) >= LOGIN_RATE_LIMIT["max_attempts"]:
            return JSONResponse(
                status_code=429,
                content={"detail": "登录尝试过于频繁，请 1 分钟后再试", "retry_after": 60}
            )
        login_store[client_ip].append(now)
    else:
        # 普通 API 限流（逻辑不变）
        rate_limit_store[client_ip] = [
            t for t in rate_limit_store.get(client_ip, [])
            if now - t < RATE_LIMIT_WINDOW
        ]
        if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQS:
            return JSONResponse(status_code=429, ...)
        rate_limit_store[client_ip].append(now)
    
    return await call_next(request)
```

需要新增一个 `login_store` 字典：

```python
# main.py 顶部
login_store: dict = {}
```

### 6.3 你学到了什么

| 知识点 | 说明 |
|--------|------|
| 限流粒度 | 不同接口应该有不同的限流策略 |
| 暴力破解防护 | 登录接口是攻击面，需要最严格的限制 |
| 限流 vs 封禁 | 限流是减缓，封禁是彻底阻止 |

---

## 7. 完整链路验证清单

### 7.1 写完每段代码后

```bash
# 后端语法检查
python -c "import ast; ast.parse(open('api/services/jwt_verify.py', encoding='utf-8').read())"
python -c "import ast; ast.parse(open('api/main.py', encoding='utf-8').read())"

# 运行测试
python -m pytest tests/ -v

# 前端构建
cd frontend && npm run build
```

### 7.2 浏览器手工测试

```
测试场景 1：正常登录
  1. 打开 http://43.139.133.245:8080
  2. 用邮箱密码登录
  3. F12 → Application → Local Storage → signal_auth_token 有值
  4. 首页数据正常加载

测试场景 2：token 过期刷新
  1. 登录后，把 localStorage.signal_auth_token 改成一个过期 token
     → 找一个旧 JWT（或者手动改 exp）
  2. 刷新页面，点击收藏
  3. 预期：自动刷新 token，操作成功，页面不跳转

测试场景 3：裸 UUID 被拒
  1. 在 Console 手动请求：
     fetch('/api/auth/me', { headers: { Authorization: 'Bearer 00000000-0000-0000-0000-000000000002' }})
     .then(r => r.json()).then(console.log)
  2. 预期：返回 401，不是 200
```

### 7.3 质量门禁

| 检查项 | 命令 | 预期结果 |
|--------|------|---------|
| Python 语法 | `ast.parse` | 无报错 |
| 全量测试 | `pytest tests/ -v` | 41 passed, 1 skipped |
| 前端构建 | `npm run build` | 0 errors |
| UUID 冒充 | 手动 curl | 返回 401 |

---

## 附录：JWT 调试工具箱

### 在浏览器解码 JWT

```javascript
// DevTools Console 中执行
function decodeJWT(token) {
    const parts = token.split('.');
    if (parts.length !== 3) return '不是有效 JWT';
    return {
        header: JSON.parse(atob(parts[0])),
        payload: JSON.parse(atob(parts[1])),
        signature: parts[2].slice(0, 20) + '...'
    };
}

const token = localStorage.getItem('signal_auth_token');
console.log(decodeJWT(token));
```

### 查看 token 过期时间

```javascript
function getExpiry(token) {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expDate = new Date(payload.exp * 1000);
    const remaining = Math.round((payload.exp * 1000 - Date.now()) / 60000);
    return {
        exp: expDate.toLocaleString(),
        remaining_minutes: remaining,
        expired: remaining <= 0
    };
}
```

### 用 curl 测试后端

```bash
# 拿一个真实 token（浏览器里复制）
TOKEN="eyJ..."

# 正常请求
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me

# 伪造 UUID（P0 修复前 vs 修复后）
curl -H "Authorization: Bearer 00000000-0000-0000-0000-000000000002" http://localhost:8000/api/auth/me
# 修复前 → 200（被冒充）
# 修复后 → 401（被拒）

# 过期 token
curl -H "Authorization: Bearer eyJleHAiOjB9.eyJleHAiOjB9.xxx" http://localhost:8000/api/auth/me
# 应该返回 401
```
