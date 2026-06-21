"""
知识库检索测试脚本
模拟完整的关键词 + 向量检索流程

使用方法：
    python test_retrieval.py
"""

import os
import sys
import asyncio
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from api.services.embedding import get_embedding_service
from api.models.database import get_db

# 初始化
db = get_db()
embedding_service = get_embedding_service()


def print_header(text: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(title: str, data: Any):
    """打印结果"""
    print(f"\n📌 {title}")
    print("-" * 40)
    print(data)


def print_list(title: str, items: List[Dict], max_items: int = 3):
    """打印列表"""
    print(f"\n📌 {title}")
    print("-" * 40)
    for i, item in enumerate(items[:max_items], 1):
        doc_name = item.get("document", {}).get("name", "未知文档")
        score = item.get("score", 0)
        content = item.get("chunk", {}).get("content", "")[:100]
        print(f"\n  [{i}] 文档: {doc_name}")
        print(f"      得分: {score:.2f}")
        print(f"      内容: {content}...")


# ============================================================
# 测试 1：Embedding 服务测试
# ============================================================

async def test_embedding_service():
    """测试 Embedding 服务"""
    print_header("测试 1：Embedding 服务")

    test_texts = [
        "苹果手机最新款是什么？",
        "iPhone 有什么新品？",
        "香蕉多少钱一斤？"
    ]

    print_result("测试文本", "\n".join(f"  {i+1}. {t}" for i, t in enumerate(test_texts)))

    print("\n🔄 正在生成 Embedding...")

    embeddings = await embedding_service.get_embeddings(test_texts)

    if embeddings and all(e is not None for e in embeddings):
        print_result("✅ Embedding 生成成功",
                    f"生成了 {len(embeddings)} 个向量\n"
                    f"每个向量维度: {len(embeddings[0])}")
    else:
        print_result("❌ Embedding 生成失败", "请检查 ALIBABA_API_KEY 配置")
        return False

    # 打印部分向量
    print(f"\n📊 向量示例（只显示前5个维度）:")
    for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
        print(f"  {i+1}. {text}: [{', '.join(f'{x:.4f}' for x in emb[:5])} ...]")

    return True


# ============================================================
# 测试 2：向量相似度计算
# ============================================================

def calculate_similarity(emb1: List[float], emb2: List[float]) -> float:
    """计算余弦相似度"""
    import math

    dot_product = sum(a * b for a, b in zip(emb1, emb2))
    norm1 = math.sqrt(sum(a * a for a in emb1))
    norm2 = math.sqrt(sum(b * b for b in emb2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


async def test_vector_similarity():
    """测试向量相似度"""
    print_header("测试 2：向量相似度计算")

    texts = [
        "苹果手机最新款是什么？",
        "iPhone 有什么新品？",
        "香蕉多少钱一斤？"
    ]

    print_result("测试文本", "\n".join(f"  {i+1}. {t}" for i, t in enumerate(texts)))

    print("\n🔄 正在生成 Embedding...")

    embeddings = await embedding_service.get_embeddings(texts)

    if not embeddings or not all(e is not None for e in embeddings):
        print_result("❌ Embedding 生成失败", "跳过此测试")
        return

    # 计算相似度
    print("\n📊 相似度矩阵:")
    print("\n        ", "    ".join(f"{'T'+str(i+1)}" for i in range(len(texts))))

    for i, (text1, emb1) in enumerate(zip(texts, embeddings)):
        similarities = []
        for j, emb2 in enumerate(embeddings):
            sim = calculate_similarity(emb1, emb2)
            similarities.append(f"{sim:.3f}")

        short_text = text1[:8] + "..."
        print(f"  T{i+1} ({short_text})  {'    '.join(similarities)}")

    # 解释结果
    sim_12 = calculate_similarity(embeddings[0], embeddings[1])
    sim_13 = calculate_similarity(embeddings[0], embeddings[2])

    print(f"\n💡 解释:")
    print(f"  - '苹果手机' vs 'iPhone': {sim_12:.3f} (语义相似)")
    print(f"  - '苹果手机' vs '香蕉': {sim_13:.3f} (语义不相似)")


# ============================================================
# 测试 3：向量检索
# ============================================================

async def test_vector_search(query: str):
    """测试向量检索"""
    print_header(f"测试 3：向量检索 (查询: '{query}')")

    print("\n🔄 正在执行向量检索...")

    try:
        # 生成查询向量
        query_embedding = await embedding_service.get_embedding(query)

        if not query_embedding:
            print_result("❌ 生成查询向量失败", "请检查 ALIBABA_API_KEY 配置")
            return []

        print_result("✅ 查询向量生成成功", f"维度: {len(query_embedding)}")

        # 将向量转换为字符串格式
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # 执行向量检索
        result = db.client.rpc(
            'search_kb_by_embedding',
            {
                'query_embedding': embedding_str,
                'user_id': '00000000-0000-0000-0000-000000000000',  # 演示用户ID
                'limit': 5
            }
        ).execute()

        if result.data:
            print_result("✅ 向量检索成功", f"返回 {len(result.data)} 个结果")

            results = []
            for item in result.data:
                results.append({
                    "chunk": {
                        "content": item.get("content", ""),
                        "document_id": item.get("document_id", "")
                    },
                    "document": {
                        "id": item.get("document_id", ""),
                        "name": item.get("document_name", ""),
                    },
                    "score": item.get("similarity", 0) * 100
                })

            print_list("检索结果", results)
            return results
        else:
            print_result("⚠️ 向量检索无结果", "可能原因:\n"
                        "  1. 数据库中没有文档切片\n"
                        "  2. 切片没有生成 Embedding\n"
                        "  3. 文档不是公开的或不属于当前用户")
            return []

    except Exception as e:
        print_result("❌ 向量检索失败", f"错误: {str(e)}")
        return []


# ============================================================
# 测试 4：关键词检索
# ============================================================

def test_keyword_search(query: str, limit: int = 5):
    """测试关键词检索"""
    print_header(f"测试 4：关键词检索 (查询: '{query}')")

    import jieba

    print("\n🔄 正在执行关键词检索...")

    try:
        # 分词
        keywords = jieba.lcut(query.lower())
        keywords = [w for w in keywords if len(w) > 1]
        print_result("📝 分词结果", " ".join(keywords))

        # 查询切片
        chunks_query = db.client.table("kb_chunks") \
            .select("*, kb_documents!inner(id, name, file_type, is_public, user_id)") \
            .order("created_at", desc=True) \
            .limit(50)

        result = chunks_query.execute()
        all_chunks = result.data or []

        print_result("📊 查询到切片", f"共 {len(all_chunks)} 个")

        # 关键词匹配
        scored_chunks = []
        for chunk in all_chunks:
            content = chunk.get("content", "").lower()
            doc = chunk.get("kb_documents", {})
            doc_name = doc.get("name", "").lower()

            score = 0
            for keyword in keywords:
                if keyword in content:
                    score += content.count(keyword) * 3
                if keyword in doc_name:
                    score += 2

            if score > 0:
                scored_chunks.append({
                    "chunk": chunk,
                    "document": doc,
                    "score": score
                })

        # 排序
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        results = scored_chunks[:limit]

        if results:
            print_result("✅ 关键词检索成功", f"返回 {len(results)} 个结果")
            print_list("检索结果", results)
        else:
            print_result("⚠️ 关键词检索无结果", "没有找到包含关键词的文档")

        return results

    except Exception as e:
        print_result("❌ 关键词检索失败", f"错误: {str(e)}")
        return []


# ============================================================
# 测试 5：对比测试
# ============================================================

async def test_comparison(query: str):
    """对比向量检索和关键词检索"""
    print_header(f"测试 5：对比测试 (查询: '{query}')")

    print("\n" + "=" * 60)
    print("  向量检索")
    print("=" * 60)
    vector_results = await test_vector_search(query)

    print("\n" + "=" * 60)
    print("  关键词检索")
    print("=" * 60)
    keyword_results = test_keyword_search(query)

    # 对比分析
    print("\n" + "=" * 60)
    print("  对比分析")
    print("=" * 60)

    vector_doc_ids = set(r["document"]["id"] for r in vector_results if r.get("document", {}).get("id"))
    keyword_doc_ids = set(r.get("document", {}).get("id", "") for r in keyword_results if r.get("document", {}).get("id"))

    common_docs = vector_doc_ids & keyword_doc_ids

    print(f"\n📊 结果对比:")
    print(f"  - 向量检索结果数: {len(vector_results)}")
    print(f"  - 关键词检索结果数: {len(keyword_results)}")
    print(f"  - 两者共同结果数: {len(common_docs)}")

    if common_docs:
        print(f"\n✅ 两种方法找到的共同文档:")
        for doc_id in common_docs:
            vec_result = next((r for r in vector_results if r.get("document", {}).get("id") == doc_id), None)
            if vec_result:
                print(f"  - {vec_result['document'].get('name', '未知文档')} "
                      f"(向量得分: {vec_result.get('score', 0):.2f})")

    print(f"\n💡 分析:")
    if len(vector_results) > len(keyword_results):
        print("  - 向量检索找到更多结果（语义理解能力强）")
    if len(keyword_results) > len(vector_results):
        print("  - 关键词检索找到更多结果（精确匹配能力强）")
    if common_docs:
        print("  - 两种方法互补，可考虑混合检索")


# ============================================================
# 测试 6：检查数据库状态
# ============================================================

def test_database_status():
    """检查数据库状态"""
    print_header("测试 6：数据库状态")

    try:
        # 查询文档数量
        docs_result = db.client.table("kb_documents") \
            .select("id", count="exact") \
            .execute()

        total_docs = docs_result.count or 0
        print_result("📚 文档总数", f"{total_docs} 个")

        # 查询切片数量
        chunks_result = db.client.table("kb_chunks") \
            .select("id", count="exact") \
            .execute()

        total_chunks = chunks_result.count or 0
        print_result("📄 切片总数", f"{total_chunks} 个")

        # 查询有 Embedding 的切片数量
        chunks_with_embedding = db.client.table("kb_chunks") \
            .select("id", count="exact") \
            .not_.is_("embedding", None) \
            .execute()

        chunks_with_emb_count = chunks_with_embedding.count or 0
        print_result("🔢 有 Embedding 的切片", f"{chunks_with_emb_count} 个")

        # 计算覆盖率
        if total_chunks > 0:
            coverage = (chunks_with_emb_count / total_chunks) * 100
            print_result("📊 Embedding 覆盖率", f"{coverage:.1f}%")

            if coverage < 100:
                print("\n⚠️  提示: 有文档切片没有生成 Embedding")
                print("   原因: 这些文档是在添加向量检索功能之前上传的")
                print("   解决: 重新处理这些文档即可生成 Embedding")

        return {
            "total_docs": total_docs,
            "total_chunks": total_chunks,
            "chunks_with_embedding": chunks_with_emb_count
        }

    except Exception as e:
        print_result("❌ 数据库查询失败", f"错误: {str(e)}")
        return None


# ============================================================
# 主函数
# ============================================================

async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("    知识库检索测试脚本")
    print("    模拟完整的关键词 + 向量检索流程")
    print("=" * 60)

    # 测试数据库状态
    db_status = test_database_status()

    if db_status and db_status["total_chunks"] == 0:
        print("\n⚠️  提示: 数据库中没有文档切片")
        print("   请先上传一些文档后再运行测试")

    # 检查 Embedding API
    print("\n🔍 检查 Embedding API 配置...")
    api_key = os.getenv("ALIBABA_API_KEY")
    if api_key:
        print(f"✅ ALIBABA_API_KEY 已配置 (前8位: {api_key[:8]}...)")
    else:
        print("❌ ALIBABA_API_KEY 未配置")
        print("   请在 .env 文件中添加: ALIBABA_API_KEY=your_key")

    # 执行测试
    print("\n" + "=" * 60)
    print("  是否执行详细测试？")
    print("=" * 60)
    print("\n可用的测试查询:")
    print("  1. AI 相关的新闻")
    print("  2. iPhone 最新消息")
    print("  3. 自动驾驶技术")
    print("  4. 自定义查询")
    print("\n或者直接运行: python test_retrieval.py <查询内容>")

    # 默认测试查询
    test_queries = [
        "AI 融资",
        "iPhone",
        "自动驾驶"
    ]

    for query in test_queries:
        await test_comparison(query)
        await asyncio.sleep(1)  # 避免 API 限流

    print("\n" + "=" * 60)
    print("  测试完成！")
    print("=" * 60)

    print("\n📝 下一步:")
    print("  1. 上传新文档测试 Embedding 生成")
    print("  2. 查看日志文件: tail -f chat.log")
    print("  3. 在前端页面测试对话功能")


if __name__ == "__main__":
    # 如果有命令行参数，使用参数作为查询
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        asyncio.run(test_comparison(query))
    else:
        asyncio.run(main())
