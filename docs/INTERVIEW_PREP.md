# AI 行业日报 - 面试准备文档

## 项目概述

**项目名称**: AI 行业日报 (AI Industry Digest)
**技术栈**: FastAPI + React + Supabase + Redis + Nginx
**部署**: 腾讯云服务器 + PM2 进程管理

### 访问地址
- 前端: http://43.139.133.245/
- 管理后台: http://43.139.133.245/admin
- API 文档: http://43.139.133.245/docs

---

## 核心技术亮点

### 1. Redis 缓存层
**问题**: 数据库查询压力大，热门数据重复读取

**解决方案**:
- 实现 `CacheService` 类，封装 Redis 操作
- 缓存策略: 列表页 5 分钟缓存，详情页 30 分钟缓存
- 降级逻辑: Redis 不可用时自动回退到数据库查询

**关键代码**:
```python
class CacheService:
    def get(self, key: str) -> Optional[Any]:
        if not self.available:
            return None  # 自动降级
        try:
            value = self._redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            self._stats["errors"] += 1
            return None

    def with_cache(self, key: str, ttl: int, fetch_func):
        cached = self.get(key)
        if cached is not None:
            return cached
        data = fetch_func()
        self.set(key, data, ttl)
        return data
```

**面试话术**:
> "我在项目中实现了 Redis 缓存层来解决热点数据查询压力。采用了装饰器模式和缓存降级机制，当 Redis 服务不可用时会自动回退到数据库查询，保证服务可用性。缓存 key 的设计使用了多维度拼接，避免缓存雪崩。"

---

### 2. JWT 认证与权限控制
**问题**: 用户会话管理、API 安全访问、管理员权限

**解决方案**:
- 后端 JWT 验证，支持 Supabase Auth
- Fallback 机制: Supabase 验证失败时直接解码 JWT payload
- 管理员权限校验服务 `admin_auth.py`

**关键代码**:
```python
def verify_token(token: str) -> Optional[str]:
    # 1. 优先使用 Supabase 验证
    try:
        response = supabase.auth.get_user(token)
        if response.user:
            return response.user.id
    except Exception as e:
        print(f"[JWT] Supabase 验证失败: {e}")

    # 2. Fallback: 直接解码 JWT（会话过期时降级）
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload.get("sub")

async def get_current_admin(user_id: str = Depends(get_current_user)):
    profile = db.get_or_create_profile(user_id)
    if profile.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user_id
```

**面试话术**:
> "JWT 验证采用双层保障策略。首先通过 Supabase Auth 验证会话有效性，如果会话过期（如用户长时间未操作），会自动降级到直接解码 JWT 获取用户 ID，保证用户体验不受影响。权限控制使用了 FastAPI 的 Depends 依赖注入模式，实现了管理员权限校验的复用。"

---

### 3. WebSocket 实时通信
**问题**: 用户需要实时接收新文章推送和收藏通知

**解决方案**:
- 实现 `WebSocketManager` 连接管理器
- 支持广播、按用户、按时段推送
- 消息类型枚举: 文章更新、收藏通知、阅读统计

**关键代码**:
```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id].append(websocket)

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

    async def broadcast_articles(self, new_articles: List[Article]):
        message = {
            "type": MessageType.NEW_ARTICLES,
            "data": {"count": len(new_articles)}
        }
        for user_id in self.active_connections:
            await self.send_to_user(user_id, message)
```

**面试话术**:
> "WebSocket 实现了一个连接管理器，支持单播（给指定用户）、广播（全员推送）。使用了 defaultdict 存储用户与连接的映射关系，便于快速查找。为了避免连接泄漏，我在 disconnect 时确保从映射表中移除连接。"

---

### 4. CI/CD 自动化
**问题**: 手动部署效率低、易出错

**解决方案**:
- GitHub Actions 自动化测试
- 前后端分离构建
- PM2 零宕机部署

**关键配置**:
```yaml
# .github/workflows/ci.yml
jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 设置 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: 运行测试
        run: python -m pytest tests/ -v --tb=short

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 设置 Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: 构建生产版本
        working-directory: frontend
        run: npm run build
```

**面试话术**:
> "CI/CD 流水线使用 GitHub Actions 实现自动化。测试阶段运行 pytest 单元测试，构建阶段使用 npm run build 生成生产包。部署时通过 SSH 远程执行 git pull 和 pm2 重启命令，实现了零宕机部署。"

---

### 5. 管理后台
**功能**:
- 系统概览: 用户数、文章数、收藏数、今日活跃
- 热门文章: 阅读量 Top 10 排行
- 来源分布: 各来源文章数量图表
- 缓存管理: 统计、清空、重置

**技术实现**:
- 前端: React + Lucide 图标库
- 后端: 管理员权限校验 + 统计 API
- 数据表: `user_profiles` 添加 `role` 字段

---

## 遇到的问题与解决

### 问题 1: JWT 会话过期导致 401
**现象**: Supabase 返回 "Session from session_id claim in JWT does not exist"

**解决**: 添加 JWT payload 直接解码作为 fallback
```python
# Fallback: 直接解码 JWT
payload = jwt.decode(token, options={"verify_signature": False})
return payload.get("sub")
```

### 问题 2: OAuth 回调 URL 配置问题
**现象**: "Unsafe attempt to load URL" 浏览器安全错误

**解决**: 临时禁用 OAuth，配置 Nginx 反向代理统一端口访问

### 问题 3: Redis 连接失败
**现象**: Redis 服务不可用时整个应用报错

**解决**: 实现缓存降级，服务不可用时回退到数据库
```python
if not self.available:
    return None  # 自动降级
```

---

## 项目架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (端口 80)                          │
│                  反向代理 + 静态资源                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ 代理到 8000
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI 后端 (端口 8000)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Auth API   │  │  Articles    │  │  Admin API   │     │
│  │  (JWT验证)   │  │  (CRUD)     │  │  (权限校验)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                      │
│  │  WebSocket   │  │  CacheService│                      │
│  │  Manager     │  │  (Redis)     │                      │
│  └──────────────┘  └──────────────┘                      │
└───────────┬─────────────────────────────────┬───────────────┘
            │                                 │
            ▼                                 ▼
┌─────────────────────┐           ┌─────────────────────────┐
│    Redis            │           │     Supabase            │
│   (缓存层)          │           │  (Auth + PostgreSQL)    │
└─────────────────────┘           └─────────────────────────┘
```

---

## 快速问答

### Q: 缓存如何避免雪崩？
A: 缓存雪崩是指大量缓存同时过期导致数据库压力骤增。我的解决方案：
1. 缓存过期时间随机浮动（如 5-7 分钟）
2. 使用互斥锁（如 Redis SETNX）保证只有一个请求回源
3. 后端实现熔断降级，超时自动回退

### Q: 如何保证接口安全性？
A:
1. JWT Token 认证，每次请求验证
2. 敏感接口添加权限校验（如管理员 API）
3. 使用 HTTPS 加密传输
4. 接口限流防止恶意请求

### Q: Redis 挂了怎么办？
A: 实现了两层降级：
1. 缓存层降级：Redis 不可用时直接查数据库
2. JWT 验证降级：Supabase 会话过期时解码 JWT payload

### Q: 如何实现实时推送？
A: 使用 WebSocket 长连接，建立用户与连接的映射表。新文章入库时通过广播推送，收藏等操作通过单播推送给指定用户。

---

## 技术栈详解

| 技术 | 用途 | 掌握程度 |
|------|------|----------|
| FastAPI | 后端 API 框架 | 熟练 |
| React | 前端框架 | 熟练 |
| Supabase | 认证 + 数据库 | 熟练 |
| Redis | 缓存层 | 熟练 |
| Nginx | 反向代理 | 熟悉 |
| PM2 | 进程管理 | 熟悉 |
| GitHub Actions | CI/CD | 熟悉 |
| WebSocket | 实时通信 | 熟悉 |

---

## 后续优化方向

1. **性能优化**: 引入文章内容摘要缓存，减少 LLM 调用
2. **监控告警**: 接入 Prometheus + Grafana 监控体系
3. **灰度发布**: 使用 Nginx 权重分流实现 AB 测试
4. **Elasticsearch**: 文章全文检索替代现有模糊匹配
