from api.models.database import get_db
from api.routes.chat import search_kb_chunks

db = get_db()

# 测试知识库查询
print("测试1：直接查询知识库")
result = db.client.table("kb_chunks").select("*, kb_documents!inner(id, name, file_type, is_public, user_id)").execute()
print(f"查询结果数量: {len(result.data)}")
if result.data:
    print("第一个结果:", result.data[0].keys())

# 测试 or_ 条件
print("\n测试2：测试 or_ 查询")
try:
    # 测试正确的 or_ 语法
    result = db.client.table("kb_chunks").select("*").or_("kb_documents.is_public.eq.true").execute()
    print(f"or_ 查询成功, 结果数量: {len(result.data)}")
except Exception as e:
    print(f"or_ 查询失败: {e}")

# 测试 search_kb_chunks 函数
print("\n测试3：测试 search_kb_chunks 函数")
try:
    chunks = search_kb_chunks("AI", "demo_user", limit=3)
    print(f"搜索结果数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"结果{i+1}:")
        print(f"  分数: {chunk['score']}")
        print(f"  文档名: {chunk['document'].get('name', '')[:50]}...")
        print(f"  内容: {chunk['chunk'].get('content', '')[:100]}...")
except Exception as e:
    print(f"search_kb_chunks 失败: {e}")