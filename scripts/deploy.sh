#!/bin/bash
# ============================================================
# Signal - 一键部署脚本
# 用法: bash scripts/deploy.sh
# 功能: pip 更新 → 前端构建 → 重启后端
# 注意: 代码同步由 GitHub Actions 的 SCP 步骤完成
# ============================================================

set -e

PROJECT_DIR="/opt/ai-industry-digest"
BACKEND_LOG="$PROJECT_DIR/backend.log"

echo "===================== Signal 部署 ====================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "项目路径: $PROJECT_DIR"
echo "========================================================"

cd "$PROJECT_DIR" || { echo "❌ 项目目录不存在: $PROJECT_DIR"; exit 1; }

# 1. 更新 Python 依赖
echo ""
echo "📦 [1/3] 更新 Python 依赖..."
pip install -r requirements.txt -q 2>/dev/null && echo "   ✅ Python 依赖已更新" || echo "   ⏭  Python 依赖无变更"

# 2. 构建前端
echo ""
echo "📦 [2/3] 构建前端..."
cd frontend
npm install --silent 2>/dev/null
npm run build
echo "   ✅ 前端构建完成"

# 3. 重启后端
echo ""
echo "📦 [3/3] 重启后端服务..."
cd "$PROJECT_DIR"

pkill -f "uvicorn api.main:app" 2>/dev/null || true
sleep 1

nohup /home/ubuntu/.local/bin/uvicorn api.main:app \
    --host 0.0.0.0 --port 8000 \
    > "$BACKEND_LOG" 2>&1 &

sleep 2

if pgrep -f "uvicorn api.main:app" > /dev/null; then
    echo "   ✅ 后端服务已启动 (PID: $(pgrep -f 'uvicorn api.main:app'))"
else
    echo "   ❌ 后端服务启动失败，查看日志: tail -20 $BACKEND_LOG"
    exit 1
fi

# 4. 验证
echo ""
echo "===================== 部署完成 ====================="
echo "验证 API: curl http://localhost:8000/api/reports"
echo "访问地址: http://43.139.133.245:8080"
echo "后端日志: tail -f $BACKEND_LOG"
echo "========================================================"
