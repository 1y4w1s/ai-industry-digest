#!/bin/bash
#
# Celery 服务安装脚本
# 使用方法: bash scripts/install_celery_services.sh
#

set -e

echo "============================================================"
echo "    Celery 服务安装脚本"
echo "============================================================"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

echo ""
echo "📦 [1/5] 安装 Celery 和 Redis..."
apt-get update
apt-get install -y redis-server
pip3 install celery redis

echo ""
echo "✅ [2/5] 启动 Redis 服务..."
systemctl enable redis-server
systemctl start redis-server

echo ""
echo "✅ [3/5] 配置虚拟环境..."
cd /opt/ai-industry-digest
source venv/bin/activate
pip install celery redis
deactivate

echo ""
echo "✅ [4/5] 安装 systemd 服务..."
# 复制服务文件
cp /opt/ai-industry-digest/scripts/celery-beat.service /etc/systemd/system/
cp /opt/ai-industry-digest/scripts/celery-worker.service /etc/systemd/system/

# 重新加载 systemd
systemctl daemon-reload

echo ""
echo "✅ [5/5] 启动 Celery 服务..."
# 启动 Celery Beat（调度器）
systemctl enable celery-beat
systemctl start celery-beat

# 启动 Celery Worker（执行器）
systemctl enable celery-worker
systemctl start celery-worker

echo ""
echo "============================================================"
echo "    安装完成！"
echo "============================================================"
echo ""
echo "📊 服务状态："
echo "----------------------------------------"
systemctl status celery-beat --no-pager || true
echo ""
systemctl status celery-worker --no-pager || true
echo ""
echo "📝 常用命令："
echo "----------------------------------------"
echo "  查看日志: journalctl -u celery-beat -f"
echo "  查看日志: journalctl -u celery-worker -f"
echo "  重启服务: systemctl restart celery-beat celery-worker"
echo "  停止服务: systemctl stop celery-beat celery-worker"
echo "============================================================"
