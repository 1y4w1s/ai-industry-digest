#!/bin/bash

# 启用 Nginx Gzip 压缩
echo "=== 配置 Nginx Gzip 压缩 ==="

# 备份原始配置
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# 使用 sed 删除原有注释的 gzip 配置
sudo sed -i '/# gzip_vary on;/d' /etc/nginx/nginx.conf
sudo sed -i '/# gzip_proxied any;/d' /etc/nginx/nginx.conf
sudo sed -i '/# gzip_comp_level 6;/d' /etc/nginx/nginx.conf
sudo sed -i '/# gzip_buffers 16 8k;/d' /etc/nginx/nginx.conf
sudo sed -i '/# gzip_http_version 1.1;/d' /etc/nginx/nginx.conf
sudo sed -i '/# gzip_types text\/plain text\/css application\/json application\/javascript text\/xml application\/xml application\/xml+rss text\/javascript;/d' /etc/nginx/nginx.conf

# 在 gzip on; 后面添加配置
sudo sed -i '/gzip on;/a\        gzip_vary on;' /etc/nginx/nginx.conf
sudo sed -i '/gzip on;/a\        gzip_proxied any;' /etc/nginx/nginx.conf
sudo sed -i '/gzip on;/a\        gzip_comp_level 6;' /etc/nginx/nginx.conf
sudo sed -i '/gzip on;/a\        gzip_buffers 16 8k;' /etc/nginx/nginx.conf
sudo sed -i '/gzip on;/a\        gzip_http_version 1.1;' /etc/nginx/nginx.conf
sudo sed -i '/gzip on;/a\        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript application/x-javascript application/font-woff2 image/svg+xml;' /etc/nginx/nginx.conf

# 测试配置
echo "测试 Nginx 配置..."
if sudo nginx -t; then
    echo "配置测试通过，重新加载 Nginx..."
    sudo systemctl reload nginx
    echo "✅ Gzip 压缩已启用"
else
    echo "❌ 配置测试失败，恢复备份"
    sudo cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
fi

# 验证
echo ""
echo "=== 验证压缩是否生效 ==="
curl -I -H "Accept-Encoding: gzip" http://localhost:8080/assets/index-T45QGQ17.js 2>/dev/null | grep -E "Content-Encoding|Content-Length"
