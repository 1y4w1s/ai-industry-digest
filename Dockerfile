# Signal API (FastAPI) — 单阶段 slim 镜像
# 仅跑 API 服务；每日采集流水线留在 GitHub Actions（更稳，已含 health_check + daily_verify）
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先拷贝依赖清单以利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝应用代码（.dockerignore 已排除 .env / node_modules / frontend/src / 测试 / 文档）
COPY . .

# 前端 dist 由 CI 构建后挂载/同步（同 prod 架构）；建空目录防止 StaticFiles 启动崩溃
RUN mkdir -p frontend/dist/assets

EXPOSE 8000

# 健康检查：API 自带 /health 路由（api/main.py:124）
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4"]
