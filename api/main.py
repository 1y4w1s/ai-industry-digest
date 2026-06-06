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

# 速率限制中间件（每 IP 每分钟最多 120 次）
rate_limit_store: dict = {}
RATE_LIMIT_MAX_IPS = 1000  # 最多追踪 1000 个 IP
RATE_LIMIT_WINDOW = 60     # 1 分钟窗口
RATE_LIMIT_MAX_REQS = 120  # 每分钟最多 120 次

def _cleanup_rate_limit_store():
    """定期清理过期的速率限制记录，防止内存泄漏"""
    global rate_limit_store
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    rate_limit_store = {
        ip: [t for t in timestamps if t > cutoff]
        for ip, timestamps in rate_limit_store.items()
        if any(t > cutoff for t in timestamps)
    }

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # 不限制静态文件和 docs
    if path.startswith("/test/") or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/api/proxy"):
        return await call_next(request)

    now = time.time()

    # 每 60 秒清理一次
    if int(now) % RATE_LIMIT_WINDOW == 0:
        _cleanup_rate_limit_store()

    # 限制追踪的 IP 数
    if len(rate_limit_store) > RATE_LIMIT_MAX_IPS:
        _cleanup_rate_limit_store()

    # 清理过期记录
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store.get(client_ip, [])
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQS:
        return JSONResponse(
            status_code=429,
            content={"detail": "请求过于频繁，请稍后再试", "retry_after": 60}
        )

    rate_limit_store[client_ip].append(now)
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
