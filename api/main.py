"""
Signal - FastAPI 入口
"""

import time
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes.content import router as content_router
from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.kb import router as kb_router
from api.routes.recommend import router as recommend_router
from api.routes.admin import router as admin_router

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
app.include_router(kb_router, prefix="/api")
app.include_router(recommend_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# 静态文件托管（测试前端）
test_dir = Path(__file__).resolve().parent.parent / "test"
if test_dir.exists():
    app.mount("/test", StaticFiles(directory=str(test_dir), html=True), name="test")



@app.get("/")
async def root():
    return {
        "name": "Signal",
        "version": "2.0.0",
        "docs": "/docs",
        "test_frontend": "/test/",
    }
