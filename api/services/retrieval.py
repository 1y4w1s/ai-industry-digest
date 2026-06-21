"""
高级检索服务
实现：Query 改写、混合检索、RRF 结果融合
"""

import os
from typing import List, Dict, Any, Optional
import jieba
from api.models.database import get_db
from api.services.embedding import get_embedding_service
import asyncio

# 初始化
db = get_db()


class AdvancedRetrievalService:
    """高级检索服务"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        
    def rewrite_query(self, query: str, history: Optional[List[Dict]] = None) -> str:
        """
        使用 LLM 改写查询
        
        参数:
            query: 原始查询
            history: 对话历史（可选）
        
        返回:
            改写后的查询
        """
        import httpx
        
        history_str = ""
        if history:
            for msg in history[-3:]:  # 只取最近3条历史
                role = "用户" if msg.get("role") == "user" else "助手"
                history_str += f"{role}: {msg.get('content', '')}\n"
        
        prompt = f"""
        请将以下用户查询改写为更适合知识库检索的形式。
        
        要求：
        1. 提取核心关键词
        2. 补充相关术语（如果需要）
        3. 去除口语化表达
        4. 如果有对话历史，请结合上下文理解
        
        对话历史：
        {history_str}
        
        用户查询：{query}
        
        改写后的查询（直接输出，不要解释）：
        """
        
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                return query
            
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 100,
                    },
                )
                if resp.status_code == 200:
                    response = resp.json()["choices"][0]["message"]["content"].strip()
                    return response if response else query
                return query
        except Exception as e:
            print(f"Query 改写失败: {e}")
            return query
    
    def keyword_search(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        关键词检索
        
        返回格式:
            [{
                "chunk": {...},
                "document": {...},
                "score": 分数
            }]
        """
        try:
            docs_result = db.client.table("kb_documents") \
                .select("id") \
                .or_(f"is_public.eq.true,user_id.eq.{user_id}") \
                .execute()
            
            doc_ids = set(doc["id"] for doc in (docs_result.data or []))
            
            if not doc_ids:
                return []
            
            query_keywords = jieba.lcut(query.lower())
            query_keywords = [w for w in query_keywords if len(w) > 1]
            
            chunks_query = db.client.table("kb_chunks") \
                .select("*, kb_documents!inner(id, name, file_type, is_public, user_id)") \
                .order("created_at", desc=True) \
                .limit(200)
            
            result = chunks_query.execute()
            all_chunks = result.data or []
            filtered_chunks = [chunk for chunk in all_chunks if chunk.get("document_id") in doc_ids]
            
            scored_chunks = []
            for chunk in filtered_chunks:
                content = chunk.get("content", "").lower()
                doc = chunk.get("kb_documents", {})
                doc_name = doc.get("name", "").lower()
                
                score = 0
                for keyword in query_keywords:
                    if keyword in content:
                        score += content.count(keyword) * 3
                    if keyword in doc_name:
                        score += 2
                
                if score > 0:
                    scored_chunks.append({
                        "chunk": {
                            "content": chunk.get("content", ""),
                            "document_id": chunk.get("document_id", ""),
                            "id": chunk.get("id", "")
                        },
                        "document": {
                            "id": chunk.get("document_id", ""),
                            "name": doc.get("name", ""),
                            "file_type": doc.get("file_type", ""),
                            "is_public": doc.get("is_public", False),
                            "user_id": doc.get("user_id", "")
                        },
                        "score": score
                    })
            
            # 按分数排序
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            return scored_chunks[:limit]
            
        except Exception as e:
            print(f"关键词检索失败: {e}")
            return []
    
    async def vector_search(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        向量检索
        
        返回格式:
            [{
                "chunk": {...},
                "document": {...},
                "score": 相似度分数 (0-100)
            }]
        """
        try:
            query_embedding = await self.embedding_service.get_embedding(query)
            
            if not query_embedding:
                return []
            
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            result = db.client.rpc(
                'search_kb_by_embedding',
                {
                    'query_embedding': embedding_str,
                    'user_id': user_id,
                    'limit_count': limit
                }
            ).execute()
            
            if not result.data:
                return []
            
            scored_chunks = []
            for item in result.data:
                scored_chunks.append({
                    "chunk": {
                        "content": item.get("content", ""),
                        "document_id": item.get("document_id", ""),
                        "id": item.get("id", "")
                    },
                    "document": {
                        "id": item.get("document_id", ""),
                        "name": item.get("document_name", ""),
                        "file_type": item.get("file_type", ""),
                        "is_public": item.get("is_public", False),
                        "user_id": item.get("doc_user_id", "")
                    },
                    "score": item.get("similarity", 0) * 100
                })
            
            return scored_chunks
            
        except Exception as e:
            print(f"向量检索失败: {e}")
            return []
    
    def rrf_fusion(self, vector_results: List[Dict], keyword_results: List[Dict], k: int = 60) -> List[Dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合算法
        
        参数:
            vector_results: 向量检索结果（已按分数排序）
            keyword_results: 关键词检索结果（已按分数排序）
            k: 常数参数，通常取 60
        
        返回:
            融合后的结果（按融合分数排序）
        """
        # 为每个 chunk_id 建立排名映射
        vector_ranks = {}
        for rank, item in enumerate(vector_results, start=1):
            chunk_id = item["chunk"]["id"]
            vector_ranks[chunk_id] = rank
        
        keyword_ranks = {}
        for rank, item in enumerate(keyword_results, start=1):
            chunk_id = item["chunk"]["id"]
            keyword_ranks[chunk_id] = rank
        
        # 合并所有结果
        all_results = {}
        for item in vector_results:
            chunk_id = item["chunk"]["id"]
            all_results[chunk_id] = item
        
        for item in keyword_results:
            chunk_id = item["chunk"]["id"]
            if chunk_id not in all_results:
                all_results[chunk_id] = item
        
        # 计算融合分数
        fused_results = []
        for chunk_id, item in all_results.items():
            vector_rank = vector_ranks.get(chunk_id, float('inf'))
            keyword_rank = keyword_ranks.get(chunk_id, float('inf'))
            
            # RRF 分数计算
            vector_score = 1 / (k + vector_rank) if vector_rank != float('inf') else 0
            keyword_score = 1 / (k + keyword_rank) if keyword_rank != float('inf') else 0
            
            # 加权融合（向量占 60%，关键词占 40%）
            fused_score = 0.6 * vector_score + 0.4 * keyword_score
            
            fused_results.append({
                **item,
                "fused_score": fused_score,
                "vector_rank": vector_rank,
                "keyword_rank": keyword_rank
            })
        
        # 按融合分数排序
        fused_results.sort(key=lambda x: x["fused_score"], reverse=True)
        
        return fused_results
    
    async def search(self, query: str, user_id: str, limit: int = 5, 
                    use_rewrite: bool = True, use_hybrid: bool = True) -> List[Dict[str, Any]]:
        """
        高级检索入口
        
        参数:
            query: 用户查询
            user_id: 用户ID
            limit: 返回结果数量
            use_rewrite: 是否启用 Query 改写
            use_hybrid: 是否启用混合检索
        
        返回:
            检索结果列表
        """
        print(f"[高级检索] 原始查询: {query}")
        
        # 1. Query 改写
        if use_rewrite:
            rewritten_query = self.rewrite_query(query)
            print(f"[高级检索] 改写后: {rewritten_query}")
        else:
            rewritten_query = query
        
        # 2. 检查是否是推荐请求
        recommend_keywords = ["推荐", "看看", "有什么", "什么内容", "内容", "文档", "资料"]
        is_recommend = any(keyword in rewritten_query.lower() for keyword in recommend_keywords)
        
        if is_recommend and len(rewritten_query) < 10:
            # 推荐模式：返回最新文档
            print("[高级检索] 推荐模式")
            result = db.client.table("kb_chunks") \
                .select("*, kb_documents!inner(id, name, file_type, is_public, user_id)") \
                .or_(f"kb_documents.is_public.eq.true,kb_documents.user_id.eq.{user_id}") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            if result.data:
                return [{
                    "chunk": {
                        "content": item.get("content", ""),
                        "document_id": item.get("document_id", ""),
                        "id": item.get("id", "")
                    },
                    "document": {
                        "id": item.get("document_id", ""),
                        "name": item.get("name", ""),
                        "file_type": item.get("file_type", ""),
                        "is_public": item.get("is_public", False),
                        "user_id": item.get("user_id", "")
                    },
                    "score": 0
                } for item in result.data]
            return []
        
        # 3. 混合检索
        if use_hybrid:
            print("[高级检索] 混合检索模式")
            
            # 并行执行两种检索
            vector_results = await self.vector_search(rewritten_query, user_id, limit * 2)
            keyword_results = self.keyword_search(rewritten_query, user_id, limit * 2)
            
            print(f"[高级检索] 向量检索: {len(vector_results)} 条")
            print(f"[高级检索] 关键词检索: {len(keyword_results)} 条")
            
            # RRF 融合
            fused = self.rrf_fusion(vector_results, keyword_results)
            
            # 去重并返回
            seen = set()
            final_results = []
            for item in fused:
                chunk_id = item["chunk"]["id"]
                if chunk_id not in seen:
                    seen.add(chunk_id)
                    final_results.append(item)
                    if len(final_results) >= limit:
                        break
            
            return final_results
        else:
            # 仅向量检索
            print("[高级检索] 仅向量检索")
            return (await self.vector_search(rewritten_query, user_id, limit))[:limit]


# 单例
_retrieval_service = None

def get_retrieval_service() -> AdvancedRetrievalService:
    """获取检索服务单例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = AdvancedRetrievalService()
    return _retrieval_service
