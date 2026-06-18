from api.models.database import get_db
from api.services.jwt_verify import DEMO_USER_UUID
from api.routes.chat import search_kb_chunks

db = get_db()

print(f"DEMO_USER_UUID: {DEMO_USER_UUID}")

# 测试修复后的 search_kb_chunks 函数
print("\n测试：search_kb_chunks 函数")
try:
    chunks = search_kb_chunks("AI", DEMO_USER_UUID, limit=3)
    print(f"搜索结果数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n结果{i+1}:")
        print(f"  分数: {chunk['score']}")
        print(f"  文档名: {chunk['document'].get('name', '')[:50]}...")
        print(f"  内容预览: {chunk['chunk'].get('content', '')[:100]}...")
except Exception as e:
    print(f"search_kb_chunks 失败: {e}")