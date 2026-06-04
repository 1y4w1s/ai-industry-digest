#!/bin/bash
# ============================================================
# Signal - 一键部署脚本
# 用法: bash scripts/deploy.sh
# 功能: git pull → pip 更新 → 前端构建 → 重启后端
# ============================================================

set -e

PROJECT_DIR="/opt/ai-industry-digest"
BACKEND_LOG="$PROJECT_DIR/backend.log"

echo "===================== Signal 部署 ====================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "项目路径: $PROJECT_DIR"
echo "========================================================"

# 1. 进入项目目录
cd "$PROJECT_DIR" || { echo "❌ 项目目录不存在: $PROJECT_DIR"; exit 1; }

# 2. 拉取最新代码
echo ""
echo "📦 [1/4] 拉取最新代码..."
git pull origin master
echo "   ✅ 代码已更新"

# 3. 更新 Python 依赖（如有变更）
echo ""
echo "📦 [2/4] 更新 Python 依赖..."
pip install -r requirements.txt -q 2>/dev/null && echo "   ✅ Python 依赖已更新" || echo "   ⏭  Python 依赖无变更"

# 4. 构建前端
echo ""
echo "📦 [3/4] 构建前端..."
cd frontend
npm install --silent 2>/dev/null
npm run build
echo "   ✅ 前端构建完成"

# 5. 重启后端
echo ""
echo "📦 [4/4] 重启后端服务..."
cd "$PROJECT_DIR"

# 停止旧进程
pkill -f "uvicorn api.main:app" 2>/dev/null || true
sleep 1

# 启动新进程
nohup /home/ubuntu/.local/bin/uvicorn api.main:app \
    --host 0.0.0.0 --port 8000 \
    > "$BACKEND_LOG" 2>&1 &

sleep 2

# 检查是否启动成功
if pgrep -f "uvicorn api.main:app" > /dev/null; then
    echo "   ✅ 后端服务已启动 (PID: $(pgrep -f 'uvicorn api.main:app'))"
else
    echo "   ❌ 后端服务启动失败，查看日志: tail -20 $BACKEND_LOG"
    exit 1
fi

# 6. 验证
echo ""
echo "===================== 部署完成 ====================="
echo "验证 API: curl http://localhost:8000/api/reports"
echo "访问地址: http://43.139.133.245:8080"
echo "后端日志: tail -f $BACKEND_LOG"
echo "========================================================"
