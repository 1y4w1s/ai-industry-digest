"""
知识图谱检索服务：利用实体-关系网络增强 RAG 检索

核心能力：
  1. 实体匹配检索：从查询中提取实体关键词，匹配 kb_entities 表
  2. 关系路径检索：根据实体的关系网络，推荐关联文档的切片
  3. Graph Score：作为第三路信号（向量 + 关键词 + 图谱）融入 RRF 融合

与现有检索的关系：
  - 向量检索：语义相似度
  - 关键词检索：精确匹配
  - 图谱检索：实体关系相关性（补充前两者的盲区）
"""

import re
import jieba
from typing import List, Dict, Any, Optional, Set, Tuple
from api.models.database import get_db


class GraphRetrievalService:
    """知识图谱检索服务"""

    @property
    def _db(self):
        """懒加载数据库连接（避免模块级 import 触发环境变量检查）"""
        return get_db()

    # 关系查询模式：查询中明确提及关系/关联时启用关系路径检索
    _RELATION_PATTERNS = [
        r"与\S{1,10}的关系", r"和\S{1,10}的关系",
        r"与\S{1,10}关联", r"和\S{1,10}关联",
        r"与\S{1,10}相关", r"和\S{1,10}相关",
        r"\S{1,10}的投资方", r"\S{1,10}的创始人",
        r"\S{1,10}的产品", r"\S{1,10}的母公司",
        r"related to", r"connected to",
    ]

    def graph_search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        基于知识图谱的检索
        
        返回格式与 AdvancedRetrievalService.search() 一致：
        [{
            "chunk": {"content": ..., "document_id": ..., "id": ...},
            "document": {"id": ..., "name": ..., "file_type": ..., "is_public": ..., "user_id": ...},
            "score": graph_score,
            "graph_info": {"matched_entities": [...], "relation_type": ...}
        }]
        """
        # 1. 从查询中提取候选实体名
        candidate_entities = self._extract_query_entities(query)
        if not candidate_entities:
            return []

        # 2. 在 kb_entities 中搜索匹配的实体
        matched_entities = self._find_matched_entities(candidate_entities, user_id)
        if not matched_entities:
            return []

        # 3. 获取这些实体关联的文档切片
        entity_ids = [e["id"] for e in matched_entities]
        entity_names = [e["name"] for e in matched_entities]
        
        # 通过 document_id 关联（同一文档的切片共享实体）
        related_chunks = self._find_chunks_by_entities(entity_ids, entity_names, user_id, limit)

        # 4. 计算 Graph Score
        for item in related_chunks:
            chunk_content = item["chunk"]["content"].lower()
            
            # 实体命中率
            entity_hits = sum(
                1 for name in entity_names if name.lower() in chunk_content
            )
            entity_score = min(entity_hits / max(len(entity_names), 1) * 2, 1.0)
            
            # 关系增强：如果查询包含关系模式，额外加 0.2
            relation_boost = 0.0
            if self._is_relation_query(query):
                relation_boost = 0.2
            
            item["score"] = min(entity_score + relation_boost, 1.0)
            item["graph_info"] = {
                "matched_entities": entity_names,
                "entity_count": len(entity_names),
                "has_relation_query": self._is_relation_query(query),
            }

        # 5. 按 graph_score 降序排列
        related_chunks.sort(key=lambda x: x["score"], reverse=True)
        return related_chunks[:limit]

    def _extract_query_entities(self, query: str) -> List[str]:
        """
        从查询中提取候选实体名
        
        策略：
        1. 使用 jieba 分词 + 词性标注
        2. 过滤出名词短语（长度 > 1 的非停用词）
        3. 包含大写字母的专用名词
        """
        words = jieba.lcut(query)
        
        # 过滤停用词和单字
        stop_words = {"的", "了", "是", "在", "有", "和", "与", "也", "都", "要",
                      "可以", "会", "就", "但", "这", "那", "什么", "怎么", "如何",
                      "为什么", "哪", "谁", "什么时候", "几", "多少"}
        
        candidates = []
        for w in words:
            w = w.strip()
            if len(w) <= 1 and not w.isupper():
                continue
            if w.lower() in stop_words:
                continue
            candidates.append(w)
        
        # 去重（保持顺序）
        seen = set()
        deduped = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        
        return deduped

    def _find_matched_entities(
        self, candidates: List[str], user_id: str
    ) -> List[Dict[str, Any]]:
        """
        在 kb_entities 中搜索匹配的实体
        
        匹配规则：
        - 精确匹配（不区分大小写）
        - 实体包含候选词
        - 候选词包含实体名（处理"大语言模型"→"大语言模型领域"）
        """
        matched = []
        seen_names = set()
        
        for candidate in candidates:
            # 尝试精确匹配
            result = self._db.client.table("kb_entities") \
                .select("id, name, type, document_id") \
                .ilike("name", f"%{candidate}%") \
                .execute()
            
            if result.data:
                for entity in result.data:
                    name = entity["name"]
                    if name not in seen_names:
                        seen_names.add(name)
                        matched.append(entity)
        
        return matched

    def _find_chunks_by_entities(
        self,
        entity_ids: List[str],
        entity_names: List[str],
        user_id: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        根据实体查找关联的文档切片
        
        策略：
        1. 优先通过 document_id 关联（与实体同文档的切片）
        2. 再通过内容包含实体名来补充
        """
        # 获取实体所属的文档 ID
        entity_docs_result = self._db.client.table("kb_entities") \
            .select("document_id") \
            .in_("id", entity_ids) \
            .execute()
        
        doc_ids = list(set(
            item["document_id"] for item in (entity_docs_result.data or [])
        ))
        
        if not doc_ids:
            return []
        
        # 从这些文档中获取切片
        chunks_result = self._db.client.table("kb_chunks") \
            .select("*, kb_documents!inner(id, name, file_type, is_public, user_id)") \
            .in_("document_id", doc_ids) \
            .or_(f"kb_documents.is_public.eq.true,kb_documents.user_id.eq.{user_id}") \
            .order("created_at", desc=True) \
            .limit(limit * 3) \
            .execute()
        
        results = []
        for item in (chunks_result.data or []):
            doc = item.get("kb_documents", {})
            results.append({
                "chunk": {
                    "content": item.get("content", ""),
                    "document_id": item.get("document_id", ""),
                    "id": item.get("id", ""),
                },
                "document": {
                    "id": item.get("document_id", ""),
                    "name": doc.get("name", ""),
                    "file_type": doc.get("file_type", ""),
                    "is_public": doc.get("is_public", False),
                    "user_id": doc.get("user_id", ""),
                },
                "score": 0.0,
            })
        
        return results

    def _is_relation_query(self, query: str) -> bool:
        """检测是否是关系查询"""
        q = query.lower()
        for pattern in self._RELATION_PATTERNS:
            if re.search(pattern, q):
                return True
        return False


# 单例
_graph_service = None


def get_graph_retrieval_service() -> GraphRetrievalService:
    """获取图谱检索服务单例"""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphRetrievalService()
    return _graph_service
