from api.models.database import get_db
from api.services.jwt_verify import DEMO_USER_UUID

db = get_db()

# 检查知识库文档内容
print("检查知识库文档内容：")
result = db.client.table("kb_chunks").select("*, kb_documents!inner(id, name)").limit(5).execute()
for chunk in result.data:
    doc_name = chunk['kb_documents'].get('name', '')
    content = chunk.get('content', '')
    print(f"\n文档: {doc_name}")
    print(f"内容长度: {len(content)}")
    print(f"内容预览: {content[:150]}...")
    print(f"包含 'ai': {'ai' in content.lower()}")

# 测试 in_ 操作符
print("\n\n测试 in_ 操作符：")
try:
    doc_ids = ["5ada8b88-..."]  # 假ID测试
    result = db.client.table("kb_chunks").select("*").in_("document_id", doc_ids).execute()
    print(f"in_ 查询成功, 结果数量: {len(result.data)}")
except Exception as e:
    print(f"in_ 查询失败: {e}")