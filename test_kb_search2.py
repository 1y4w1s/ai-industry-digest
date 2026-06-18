from api.models.database import get_db

db = get_db()

# 测试基础查询
print("测试1：直接查询知识库（不带条件）")
result = db.client.table("kb_chunks").select("*, kb_documents!inner(id, name, file_type, is_public, user_id)").execute()
print(f"查询结果数量: {len(result.data)}")
if result.data:
    first = result.data[0]
    print("第一个结果:")
    print(f"  id: {first.get('id')[:8]}")
    print(f"  document_id: {first.get('document_id')[:8]}")
    print(f"  kb_documents: {type(first.get('kb_documents'))}")
    if first.get('kb_documents'):
        print(f"    name: {first['kb_documents'].get('name', '')[:30]}")
        print(f"    is_public: {first['kb_documents'].get('is_public')}")

# 测试简单的 filter
print("\n测试2：测试简单 filter")
try:
    result = db.client.table("kb_chunks").select("*").filter("document_id", "is", "not.null").execute()
    print(f"filter 查询成功, 结果数量: {len(result.data)}")
except Exception as e:
    print(f"filter 查询失败: {e}")

# 测试 or 条件（使用正确的 URL 参数格式）
print("\n测试3：测试 or 条件（URL 参数格式）")
try:
    # 使用 URL 参数方式传递 or 条件
    result = db.client.table("kb_documents").select("*").or_(f"is_public.eq.true,user_id.eq.demo_user").execute()
    print(f"or_ 查询成功, 结果数量: {len(result.data)}")
except Exception as e:
    print(f"or_ 查询失败: {e}")