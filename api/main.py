"""
Signal - FastAPI 入口
"""

import time
import os
from pathlib import Path

# 优先加载环境变量
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes.content import router as content_router
from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.recommend import router as recommend_router
from api.routes.admin import router as admin_router
from api.routes.websocket import router as websocket_router
from api.routes.newsletter import router as newsletter_router
from api.routes.stories import router as stories_router
from api.routes.public_digest import router as public_digest_router
from api.routes.podcast import router as podcast_router
from api.routes.comments import router as comments_router

app = FastAPI(
    title="Signal API",
    description="AI 行业日报系统后端接口",
    version="2.0.0",
)

# CORS 配置（生产环境应收紧为具体域名）
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000,http://43.139.133.245:8080,https://43.139.133.245:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 速率限制 ──────────────────────────────
# 双层限流策略：
#   公共 API（/api/* 非 auth）→ 120 req/min/IP（防止爬虫）
#   用户操作（/api/auth/*）   → 30 req/min/IP（收藏/历史写操作）
#   登录（POST /api/auth/login）→ 不在本后端，由 Supabase Auth 直接处理

rate_limit_store: dict = {}   # 普通 API
auth_limit_store: dict = {}   # auth 路径（更严格）

# 公共 API 限流参数
RATE_LIMIT_MAX_IPS = 1000
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQS = 120

# Auth 路径限流参数
AUTH_LIMIT_MAX_REQS = 30   # 每分钟最多 30 次


def _cleanup_rate_limit():
    """清理所有限流存储，防止内存泄漏"""
    global rate_limit_store, auth_limit_store
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    
    rate_limit_store = {
        ip: [t for t in ts if t > cutoff]
        for ip, ts in rate_limit_store.items()
        if any(t > cutoff for t in ts)
    }
    auth_limit_store = {
        ip: [t for t in ts if t > cutoff]
        for ip, ts in auth_limit_store.items()
        if any(t > cutoff for t in ts)
    }


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # 放行：静态文件、文档、代理
    if path.startswith("/test/") or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/api/proxy"):
        return await call_next(request)

    now = time.time()

    # 定期清理
    if int(now) % RATE_LIMIT_WINDOW == 0:
        _cleanup_rate_limit()
    if len(rate_limit_store) > RATE_LIMIT_MAX_IPS or len(auth_limit_store) > RATE_LIMIT_MAX_IPS:
        _cleanup_rate_limit()

    # 选择限流策略
    if path.startswith("/api/auth/"):
        # Auth 路径 — 更严格
        store = auth_limit_store
        max_reqs = AUTH_LIMIT_MAX_REQS
        err_msg = "操作过于频繁，请稍后再试"
    elif path.startswith("/api/"):
        # 普通 API
        store = rate_limit_store
        max_reqs = RATE_LIMIT_MAX_REQS
        err_msg = "请求过于频繁，请稍后再试"
    else:
        # 非 API 路径不限流
        return await call_next(request)

    # 清理当前 IP 过期记录
    store[client_ip] = [t for t in store.get(client_ip, []) if now - t < RATE_LIMIT_WINDOW]

    if len(store[client_ip]) >= max_reqs:
        return JSONResponse(
            status_code=429,
            content={"detail": err_msg, "retry_after": 60}
        )

    store[client_ip].append(now)
    return await call_next(request)


# ── 健康检查 ────────────────────────────

@app.get("/health")
async def health():
    """系统健康检查（数据库连通性 + 基础状态）"""
    db_ok = False
    try:
        from api.models.database import get_db
        db = get_db()
        db.client.table("articles").select("id").limit(1).execute()
        db_ok = True
    except Exception:
        db_ok = False
    
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "2.0.0",
        "db": "ok" if db_ok else "error",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
    }


# 注册路由
app.include_router(content_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")
app.include_router(recommend_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(websocket_router)  # WebSocket 不需要前缀
app.include_router(newsletter_router)  # 退订落地页 /unsubscribe（无前缀）
app.include_router(stories_router, prefix="/api")  # 今日主线聚类 /api/main-thread（§2.1）
app.include_router(public_digest_router)  # 公开页 SEO：/digest/{date} + /sitemap.xml + /robots.txt（§2.3，须在 SPA fallback 之前注册）
app.include_router(podcast_router)  # 播客 RSS：/podcast.xml（§2.2，须在 SPA fallback 之前注册）
app.include_router(comments_router, prefix="/api")  # 评论区：/api/comments（§3.2）

# ── 优雅关闭 ────────────────────────────

@app.on_event("shutdown")
async def shutdown():
    """服务关闭时：通知 WebSocket 用户 + 等待请求完成 + 释放资源"""
    print("[Shutdown] 开始优雅关闭...")
    # 1. 通知所有在线用户
    try:
        from api.services.websocket_manager import ws_manager
        await ws_manager.broadcast({
            "type": "shutdown",
            "message": "服务正在维护，请稍后重新连接"
        })
    except Exception:
        pass
    # 2. 等待 3 秒让已有请求完成
    import asyncio
    await asyncio.sleep(3)
    # 3. 释放 Redis 连接
    try:
        from api.services.cache import cache
        if cache._redis:
            cache._redis.close()
    except Exception:
        pass
    print("[Shutdown] 优雅关闭完成")

# ── 静态文件托管 ────────────────────────────

# 1. 测试前端
test_dir = Path(__file__).resolve().parent.parent / "test"
if test_dir.exists():
    app.mount("/test", StaticFiles(directory=str(test_dir), html=True), name="test")

# 2. 生产前端（位于 frontend/dist）
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend_assets")

# 3. 播客音频（§2.2）：静态托管 media/podcast → /podcast
#    与 frontend/dist 挂载并存（不同前缀，无冲突）。目录不存在时创建空目录以便挂载成功。
podcast_dir = Path(__file__).resolve().parent.parent / "media" / "podcast"
try:
    podcast_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
if podcast_dir.exists():
    app.mount("/podcast", StaticFiles(directory=str(podcast_dir)), name="podcast")

    from fastapi.responses import FileResponse

    @app.get("/favicon.ico")
    async def favicon():
        fav = frontend_dist / "favicon.svg"
        if fav.exists():
            return FileResponse(fav, media_type="image/svg+xml")
        return JSONResponse(status_code=204)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback：非 API 路径返回 index.html"""
        # 放行 API、WebSocket、文档路径 + 公开页 SEO（§2.3）+ 播客 RSS（§2.2）+ 退订（§1.3）+ favicon
        if full_path.startswith(("api/", "ws", "docs", "openapi", "health", "test",
                                  "digest/", "sitemap.xml", "robots.txt", "podcast.xml",
                                  "unsubscribe", "track/", "favicon.ico")):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        html_path = frontend_dist / "index.html"
        if html_path.exists():
            return FileResponse(str(html_path), media_type="text/html")
        return JSONResponse(content={"name": "Signal", "version": "2.0.0"})
