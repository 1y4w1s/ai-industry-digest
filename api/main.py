"""
AI Industry Digest - FastAPI 入口
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.content import router as content_router
from api.routes.auth import router as auth_router

app = FastAPI(
    title="AI Industry Digest API",
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

# 注册路由
app.include_router(content_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")

# 静态文件托管（测试前端）
test_dir = Path(__file__).resolve().parent.parent / "test"
if test_dir.exists():
    app.mount("/test", StaticFiles(directory=str(test_dir), html=True), name="test")


@app.get("/")
async def root():
    return {
        "name": "AI Industry Digest",
        "version": "2.0.0",
        "docs": "/docs",
        "test_frontend": "/test/",
    }
