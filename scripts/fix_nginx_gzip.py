#!/usr/bin/env python3
"""修复 Nginx Gzip 配置"""

import re

def main():
    config_path = "/etc/nginx/nginx.conf"
    
    # 读取配置文件
    with open(config_path, 'r') as f:
        content = f.read()
    
    # 移除所有现有的 gzip 配置行
    lines = content.split('\n')
    new_lines = []
    in_gzip_section = False
    
    for line in lines:
        # 检查是否包含 gzip 配置
        if 'gzip' in line.lower():
            # 跳过所有 gzip 相关行
            continue
        new_lines.append(line)
    
    # 在 http 块中添加正确的 gzip 配置
    result = '\n'.join(new_lines)
    
    # 找到 http 块的位置并在 gzip on; 后面添加配置
    gzip_config = """        gzip on;
        gzip_vary on;
        gzip_proxied any;
        gzip_comp_level 6;
        gzip_buffers 16 8k;
        gzip_http_version 1.1;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript application/x-javascript application/font-woff2 image/svg+xml;"""
    
    # 替换单独的 gzip on; 为完整配置
    result = result.replace('        gzip on;', gzip_config)
    
    # 写入配置文件
    with open(config_path, 'w') as f:
        f.write(result)
    
    print("✅ Nginx 配置已更新")
    
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
