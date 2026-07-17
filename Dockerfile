# Signal API (FastAPI) — 多阶段构建
# 仅跑 API 服务；每日采集流水线留在 GitHub Actions

# ====== Stage 1: Builder ======
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
# --user 安装到 /root/.local，runtime stage 只拷这个目录
RUN pip install --no-cache-dir --user -r requirements.txt

# ====== Stage 2: Runtime ======
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# 只复制已安装的 Python 包，不包含 build 工具链
COPY --from=builder /root/.local /root/.local

# 复制应用代码（.dockerignore 已过滤不需要的文件）
COPY . .

# 前端 dist 由 CI 构建后挂载；建空目录防止 StaticFiles 启动崩溃
RUN mkdir -p frontend/dist/assets

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
