from api.models.database import get_db

db = get_db()

# 获取知识库文档列表
result = db.client.table("kb_documents").select("id", "name", "file_type", "created_at").order("created_at", desc=True).limit(20).execute()

print("知识库文档列表（最近20个）：")
for doc in result.data:
    print(f"\nID: {doc['id'][:8]}...")
    print(f"名称: {doc['name']}")
    print(f"类型: {doc['file_type']}")
    print(f"创建时间: {doc['created_at']}")

# 检查切片内容
print("\n\n切片内容示例：")
chunks_result = db.client.table("kb_chunks").select("content").limit(5).execute()
for i, chunk in enumerate(chunks_result.data):
    content = chunk.get("content", "")
    print(f"\n切片{i+1}: {content[:200]}...")