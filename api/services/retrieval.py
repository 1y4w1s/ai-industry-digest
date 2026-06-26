"""
高级检索服务
实现：Query 改写、混合检索、RRF 结果融合
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import jieba
from api.models.database import get_db
from api.services.embedding import get_embedding_service
from api.services.reranker import get_reranker_service
from api.services.compression import get_compression_service
from api.services.router import get_router_service, QueryIntent
from api.services.graph_retrieval import get_graph_retrieval_service
import asyncio
import time

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
    
    def _log_search(self, query: str, rewritten_query: str,
                    use_rewrite: bool, use_hybrid: bool,
                    mode: str, results: List[Dict],
                    vector_count: int = 0, keyword_count: int = 0,
                    latency_ms: int = 0) -> None:
        """记录检索日志到文件（文件日志 + F-15 监控指标）"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "rewritten_query": rewritten_query if use_rewrite else None,
                "use_rewrite": use_rewrite,
                "use_hybrid": use_hybrid,
                "mode": mode,
                "vector_results_count": vector_count,
                "keyword_results_count": keyword_count,
                "final_results_count": len(results),
                "top_scores": [
                    r.get("fused_score", r.get("score", 0))
                    for r in results[:5]
                ]
            }
            log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "retrieval.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[检索日志] 写入失败: {e}")
        
        # F-15 监控指标采集
        try:
            from api.services.monitor import get_metric_collector
            collector = get_metric_collector()
            collector.collect("search", {
                "query": query,
                "latency_ms": latency_ms,
                "vector_count": vector_count,
                "final_count": len(results),
                "top_scores": [
                    r.get("fused_score", r.get("score", 0))
                    for r in results[:5]
                ],
                "route": mode,
                "mode": "hybrid" if use_hybrid else "vector_only",
            })
        except Exception:
            pass
    
    async def compress_context(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        *,
        max_chars: int = 800,
        mode: str = "extract",
    ) -> str:
        """
        对检索结果做上下文压缩（减少 LLM token 消耗）
        
        参数:
            query: 用户查询
            chunks: 检索结果列表
            max_chars: 压缩后的最大字符数
            mode: 压缩模式（extract / summarize / truncate）
        
        返回:
            压缩后的文本字符串
        """
        compressor = get_compression_service()
        return await compressor.compress(query, chunks, max_chars=max_chars, mode=mode)
    
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
    
    def rrf_fusion(self, vector_results: List[Dict], keyword_results: List[Dict],
                   graph_results: Optional[List[Dict]] = None, k: int = 60) -> List[Dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合算法
        
        参数:
            vector_results: 向量检索结果（已按分数排序）
            keyword_results: 关键词检索结果（已按分数排序）
            graph_results: 图谱检索结果（可选，第三路信号）
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
        
        graph_ranks = {}
        if graph_results:
            for rank, item in enumerate(graph_results, start=1):
                chunk_id = item["chunk"]["id"]
                graph_ranks[chunk_id] = rank
        
        # 合并所有结果
        all_results = {}
        for item in vector_results:
            chunk_id = item["chunk"]["id"]
            all_results[chunk_id] = item
        
        for item in keyword_results:
            chunk_id = item["chunk"]["id"]
            if chunk_id not in all_results:
                all_results[chunk_id] = item
        
        if graph_results:
            for item in graph_results:
                chunk_id = item["chunk"]["id"]
                if chunk_id not in all_results:
                    all_results[chunk_id] = item
        
        # 计算融合分数
        has_graph = graph_results is not None and len(graph_results) > 0
        fused_results = []
        for chunk_id, item in all_results.items():
            vector_rank = vector_ranks.get(chunk_id, float('inf'))
            keyword_rank = keyword_ranks.get(chunk_id, float('inf'))
            graph_rank = graph_ranks.get(chunk_id, float('inf')) if has_graph else float('inf')
            
            # RRF 分数计算
            vector_score = 1 / (k + vector_rank) if vector_rank != float('inf') else 0
            keyword_score = 1 / (k + keyword_rank) if keyword_rank != float('inf') else 0
            graph_score = 1 / (k + graph_rank) if graph_rank != float('inf') else 0
            
            # 三路加权融合
            if has_graph:
                # 向量 50%，关键词 30%，图谱 20%
                fused_score = 0.50 * vector_score + 0.30 * keyword_score + 0.20 * graph_score
            else:
                # 向量 60%，关键词 40%（向后兼容）
                fused_score = 0.60 * vector_score + 0.40 * keyword_score
            
            fused_results.append({
                **item,
                "fused_score": fused_score,
                "vector_rank": vector_rank,
                "keyword_rank": keyword_rank,
                "graph_rank": graph_rank if has_graph else None,
            })
        
        # 按融合分数排序
        fused_results.sort(key=lambda x: x["fused_score"], reverse=True)
        
        return fused_results
    
    async def search(self, query: str, user_id: str, limit: int = 5, 
                    use_rewrite: bool = True, use_hybrid: bool = True,
                    use_reranker: bool = True, use_routing: bool = True) -> List[Dict[str, Any]]:
        """
        高级检索入口
        
        参数:
            query: 用户查询
            user_id: 用户ID
            limit: 返回结果数量
            use_rewrite: 是否启用 Query 改写（当 use_routing=True 时由路由覆盖）
            use_hybrid: 是否启用混合检索（当 use_routing=True 时由路由覆盖）
            use_reranker: 是否启用 Cross-encoder 精排（当 use_routing=True 时由路由覆盖）
            use_routing: 是否启用查询意图路由自动选择策略
        
        返回:
            检索结果列表
        """
        start_time = time.time()
        print(f"[高级检索] 原始查询: {query}")
        
        # 1. 查询意图路由
        if use_routing:
            router = get_router_service()
            strategy = router.route(query)
            print(f"[高级检索] 路由策略: {strategy.intent_label}")
            effective_limit = max(1, int(limit * strategy.limit_multiplier))
            use_rewrite = strategy.use_rewrite
            use_hybrid = strategy.use_hybrid
            use_reranker = strategy.use_reranker
        else:
            strategy = None
            effective_limit = limit
        
        # 2. Query 改写
        if use_rewrite:
            rewritten_query = self.rewrite_query(query)
            print(f"[高级检索] 改写后: {rewritten_query}")
        else:
            rewritten_query = query
        
        # 3. 推荐模式：按时间排序返回最新文档
        if strategy and strategy.intent == QueryIntent.RECOMMEND:
            print("[高级检索] 推荐模式")
            result = db.client.table("kb_chunks") \
                .select("*, kb_documents!inner(id, name, file_type, is_public, user_id)") \
                .or_(f"kb_documents.is_public.eq.true,kb_documents.user_id.eq.{user_id}") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            if result.data:
                results = [{
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
                self._log_search(query, rewritten_query, use_rewrite, use_hybrid,
                                "recommend", results, vector_count=0, keyword_count=0,
                                latency_ms=int((time.time() - start_time) * 1000))
                return results
            self._log_search(query, rewritten_query, use_rewrite, use_hybrid,
                            "recommend", [], vector_count=0, keyword_count=0,
                            latency_ms=int((time.time() - start_time) * 1000))
            
            # F-14 Query Suggestion：推荐模式下也提供建议
            from api.services.query_suggestion import get_query_suggestion_service
            suggester = get_query_suggestion_service()
            return self._enrich_with_suggestions([], suggester.suggest(query, user_id))
        
        # 3. 混合检索
        if use_hybrid:
            print("[高级检索] 混合检索模式")
            
            # 并行执行检索（向量 + 关键词 + 图谱）
            vector_results = await self.vector_search(rewritten_query, user_id, effective_limit)
            keyword_results = self.keyword_search(rewritten_query, user_id, effective_limit)
            
            print(f"[高级检索] 向量检索: {len(vector_results)} 条")
            print(f"[高级检索] 关键词检索: {len(keyword_results)} 条")
            
            # 图谱检索（第三路信号）
            graph_results = None
            try:
                graph_service = get_graph_retrieval_service()
                graph_results = graph_service.graph_search(rewritten_query, user_id, limit=effective_limit)
                if graph_results:
                    print(f"[高级检索] 图谱检索: {len(graph_results)} 条")
            except Exception as e:
                print(f"[高级检索] 图谱检索失败（跳过）: {e}")
            
            # RRF 三路融合
            fused = self.rrf_fusion(vector_results, keyword_results, graph_results)
            
            # 去重并返回
            seen = set()
            final_results = []
            for item in fused:
                chunk_id = item["chunk"]["id"]
                if chunk_id not in seen:
                    seen.add(chunk_id)
                    final_results.append(item)
                    if len(final_results) >= effective_limit:
                        break
            
            # Re-ranker 二次精排
            if use_reranker and final_results:
                try:
                    reranker = get_reranker_service()
                    final_results = await reranker.rerank(rewritten_query, final_results, top_k=limit)
                    print(f"[高级检索] 精排后: {len(final_results)} 条")
                except Exception as e:
                    print(f"[高级检索] 精排失败（跳过）: {e}")
            else:
                final_results = final_results[:limit]
            
            self._log_search(query, rewritten_query, use_rewrite, use_hybrid,
                            "hybrid", final_results,
                            vector_count=len(vector_results), keyword_count=len(keyword_results),
                            latency_ms=int((time.time() - start_time) * 1000))
            
            # F-14 Query Suggestion：结果不足时提供建议
            from api.services.query_suggestion import get_query_suggestion_service
            suggester = get_query_suggestion_service()
            suggestions = suggester.suggest(query, user_id) if len(final_results) < 3 else {}
            return self._enrich_with_suggestions(final_results, suggestions)
        else:
            # 仅向量检索
            print("[高级检索] 仅向量检索")
            vector_results = (await self.vector_search(rewritten_query, user_id, effective_limit))[:effective_limit]
            
            vector_results_final = [dict(item) for item in vector_results]  # 浅拷贝避免副作用
            
            # Re-ranker 二次精排
            if use_reranker and vector_results_final:
                try:
                    reranker = get_reranker_service()
                    vector_results_final = await reranker.rerank(rewritten_query, vector_results_final, top_k=limit)
                    print(f"[高级检索] 精排后: {len(vector_results_final)} 条")
                except Exception as e:
                    print(f"[高级检索] 精排失败（跳过）: {e}")
                    vector_results_final = vector_results[:limit]
            else:
                vector_results_final = vector_results[:limit]
            
            self._log_search(query, rewritten_query, use_rewrite, use_hybrid,
                            "vector_only", vector_results_final,
                            vector_count=len(vector_results_final), keyword_count=0,
                            latency_ms=int((time.time() - start_time) * 1000))
            
            # F-14 Query Suggestion：结果不足时提供建议
            from api.services.query_suggestion import get_query_suggestion_service
            suggester = get_query_suggestion_service()
            suggestions = suggester.suggest(query, user_id) if len(vector_results_final) < 3 else {}
            return self._enrich_with_suggestions(vector_results_final, suggestions)


    def _enrich_with_suggestions(self, results: list, suggestions: dict) -> list:
        """将建议注入到检索结果中"""
        # 检查是否有实际建议（而非空字段的默认 dict）
        has_real_suggestions = bool(
            suggestions.get("correction")
            or suggestions.get("topics")
            or suggestions.get("related_queries")
        )
        if not has_real_suggestions:
            return results
        
        # 如果是空结果，创建一个包含建议的包装结果
        if not results:
            return [{
                "chunk": {"content": "", "document_id": "", "id": "_suggestion_"},
                "document": {"id": "", "name": "建议", "file_type": ""},
                "score": 0,
                "fused_score": 0,
                "_suggestions": suggestions,
            }]
        
        # 非空结果，将建议附加到每个结果上
        enriched = []
        for r in results:
            enriched.append({**r, "_suggestions": suggestions})
        return enriched


# 单例
_retrieval_service = None

def get_retrieval_service() -> AdvancedRetrievalService:
    """获取检索服务单例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = AdvancedRetrievalService()
    return _retrieval_service
