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

app = FastAPI(
    title="Signal API",
    description="AI 行业日报系统后端接口",
    version="2.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制中间件（每 IP 每分钟最多 30 次）
rate_limit_store = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # 不限制静态文件和 docs
    if path.startswith("/test/") or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/api/proxy"):
        return await call_next(request)

    now = time.time()
    window = 60  # 1 分钟窗口
    max_requests = 30  # 每分钟最多 30 次

    # 清理过期记录
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store.get(client_ip, [])
        if now - t < window
    ]

    if len(rate_limit_store[client_ip]) >= max_requests:
        return JSONResponse(
            status_code=429,
            content={"detail": "请求过于频繁，请稍后再试", "retry_after": 60}
        )

    rate_limit_store[client_ip].append(now)
    return await call_next(request)


# 注册路由
app.include_router(content_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")

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
