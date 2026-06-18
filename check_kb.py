from api.models.database import get_db

db = get_db()

# 检查知识库文档
result = db.client.table("kb_documents").select("*").execute()
print("知识库文档数量:", len(result.data))
for doc in result.data[:5]:
    print(f"ID: {doc.get('id')[:8]}...")
    print(f"名称: {doc.get('name')}")
    print(f"类型: {doc.get('file_type')}")
    print(f"公开: {doc.get('is_public')}")
    print("---")

# 检查知识库切片
result2 = db.client.table("kb_chunks").select("*").execute()
print("\n知识库切片数量:", len(result2.data))