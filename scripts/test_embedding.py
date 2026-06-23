#!/usr/bin/env python3
"""
简化的批量处理脚本 - 用于诊断问题
"""

import os
import sys
import asyncio

sys.path.insert(0, '/opt/ai-industry-digest')

print("=" * 60)
print("  简化版 Embedding 批量处理脚本")
print("=" * 60)

# 检查环境变量
api_key = os.getenv("ALIBABA_API_KEY")
print(f"API Key 配置: {'已配置' if api_key else '未配置'}")

if not api_key:
    print("❌ 错误: ALIBABA_API_KEY 未配置")
    sys.exit(1)

print("✅ API Key 已配置")

# 测试导入
try:
    from api.services.embedding import get_embedding_service
    print("✅ 成功导入 Embedding 服务")
    
    service = get_embedding_service()
    print("✅ 成功创建 Embedding 服务实例")
    
    # 测试生成 Embedding
    test_text = "测试文本"
    embedding = asyncio.run(service.get_embedding(test_text))
    if embedding:
        print(f"✅ 成功生成 Embedding, 维度: {len(embedding)}")
    else:
        print("❌ Embedding 生成失败")
        
except Exception as e:
    print(f"❌ 导入或调用失败: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
