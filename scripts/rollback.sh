#!/bin/bash
# Signal - 回滚脚本
# 用法: bash scripts/rollback.sh [commit_hash]

set -e

cd /opt/ai-industry-digest

# 获取当前 commit 用于回滚后恢复
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "📍 当前版本: $CURRENT_COMMIT"

# 如果指定了 commit，回滚到该版本
if [ -n "$1" ]; then
    TARGET_COMMIT=$1
    echo "🔄 回滚到: $TARGET_COMMIT"
    git checkout $TARGET_COMMIT
else
    # 默认回滚到上一个版本
    echo "🔄 回滚到上一个版本..."
    git checkout HEAD~1
fi

# 重新安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt -q
cd frontend && npm install --silent && npm run build && cd ..

# 重启后端服务
echo "🔄 重启后端服务..."
pm2 restart signal-backend 2>/dev/null || echo "⚠️  pm2 进程不存在，请手动启动"

# 健康检查
echo "🏥 健康检查..."
sleep 3
HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' | head -1)
if echo "$HEALTH" | grep -q "ok"; then
    echo "✅ 回滚成功！服务状态: $HEALTH"
else
    echo "❌ 回滚后服务异常，请手动检查"
    exit 1
fi

echo ""
echo "📋 回滚完成"
echo "   如需恢复，运行: git checkout $CURRENT_COMMIT"
