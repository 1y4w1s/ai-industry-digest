#!/usr/bin/env python3
"""完整修复 Nginx Gzip 配置"""

def main():
    # 读取原始配置
    with open('/etc/nginx/nginx.conf', 'r') as f:
        content = f.read()
    
    # 如果已经有 gzip on; 就不添加
    if 'gzip on;' not in content:
        # 在 http 块中添加 gzip 配置
        http_config = '''        gzip on;
        gzip_vary on;
        gzip_proxied any;
        gzip_comp_level 6;
        gzip_buffers 16 8k;
        gzip_http_version 1.1;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript application/x-javascript application/font-woff2 image/svg+xml;
'''
        
        # 在 http { 后面添加配置
        content = content.replace('http {', 'http {' + '\n' + http_config)
    
    # 写入配置文件
    with open('/etc/nginx/nginx.conf', 'w') as f:
        f.write(content)
    
    print("✅ Nginx 主配置已更新")
    
    # 也在站点配置中添加 gzip 配置（确保生效）
    site_config = '''server {
    listen 8080;
    server_name 43.139.133.245;

    # 启用 Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript application/x-javascript application/font-woff2 image/svg+xml;

    # 前端静态文件 — index.html 不可缓存（确保新部署立即生效）
    location / {
        root /opt/ai-industry-digest/frontend/dist;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # 构建产物（hash 文件名）— 永久缓存
    location /assets/ {
        root /opt/ai-industry-digest/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 后端API代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}'''
    
    with open('/etc/nginx/sites-available/signal', 'w') as f:
        f.write(site_config)
    
    print("✅ 站点配置已更新")
    
    # 测试配置
    import subprocess
    try:
        subprocess.run(['nginx', '-t'], check=True, capture_output=True)
        print("✅ 配置测试通过")
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
        print("✅ Nginx 已重新加载")
    except subprocess.CalledProcessError as e:
        print(f"❌ 配置错误: {e.stderr.decode()}")

if __name__ == "__main__":
    main()
