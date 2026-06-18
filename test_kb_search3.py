from api.models.database import get_db
from api.services.jwt_verify import DEMO_USER_UUID

db = get_db()

print(f"DEMO_USER_UUID: {DEMO_USER_UUID}")

# 测试 or_ 查询（使用正确的 UUID）
print("\n测试1：测试 or_ 查询（使用正确的 UUID）")
try:
    result = db.client.table("kb_documents").select("*").or_(f"is_public.eq.true,user_id.eq.{DEMO_USER_UUID}").execute()
    print(f"or_ 查询成功, 结果数量: {len(result.data)}")
    if result.data:
        print(f"第一个文档: {result.data[0].get('name')[:50]}")
except Exception as e:
    print(f"or_ 查询失败: {e}")

# 测试知识库切片查询（带 or_ 条件）
print("\n测试2：测试知识库切片查询（带 or_ 条件）")
try:
    result = db.client.table("kb_chunks").select("*, kb_documents!inner(id, name, file_type, is_public, user_id)").or_(f"kb_documents.is_public.eq.true,kb_documents.user_id.eq.{DEMO_USER_UUID}").execute()
    print(f"切片查询成功, 结果数量: {len(result.data)}")
    if result.data:
        first = result.data[0]
        print(f"第一个切片的文档名: {first['kb_documents'].get('name')[:50]}")
        print(f"切片内容预览: {first.get('content', '')[:50]}")
except Exception as e:
    print(f"切片查询失败: {e}")