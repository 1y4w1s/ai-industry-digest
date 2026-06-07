#!/usr/bin/env python3
"""测试 Gzip 压缩是否生效"""

import urllib.request

def main():
    url = "http://localhost:8080/assets/index-T45QGQ17.js"
    
    # 测试不带压缩
    print("=== 测试不带压缩 ===")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        content_length = response.headers.get('Content-Length', '未知')
        content_encoding = response.headers.get('Content-Encoding', '无')
        print(f"Content-Length: {content_length}")
        print(f"Content-Encoding: {content_encoding}")
        actual_size = len(response.read())
        print(f"实际下载大小: {actual_size}")
    
    print()
    
    # 测试带压缩
    print("=== 测试带 Gzip 压缩 ===")
    req = urllib.request.Request(url, headers={'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(req) as response:
        content_length = response.headers.get('Content-Length', '未知')
        content_encoding = response.headers.get('Content-Encoding', '无')
        print(f"Content-Length: {content_length}")
        print(f"Content-Encoding: {content_encoding}")
        actual_size = len(response.read())
        print(f"实际下载大小: {actual_size}")
    
    print()
    print("=== 总结 ===")
    if content_encoding == 'gzip':
        print("✅ Gzip 压缩已生效！")
        compression_ratio = (1 - actual_size / 929514) * 100
        print(f"压缩率: {compression_ratio:.1f}%")
        print(f"节省: {929514 - actual_size:,} bytes")
    else:
        print("❌ Gzip 压缩未生效")

if __name__ == "__main__":
    main()
