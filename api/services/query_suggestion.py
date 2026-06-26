"""
Query Suggestion 服务（F-14）

功能：
  1. 拼写纠正（Spelling Correction）：当用户输入存在拼写/用词偏差时，
     从已知文档名和实体名中找到最接近的匹配项。
  2. 主题推荐（Topic Suggestion）：当检索结果不足时，推荐相近主题。
  3. 综合入口 suggest()：接入 search() 无结果处理链路。

设计原则：
  - 轻量：零外部 API 依赖，纯字符和向量相似度计算
  - 降级优先：所有异常被捕获，不阻塞主检索流程
  - 快速响应：主体逻辑控制在 50ms 内完成
"""

import re
import jieba
from typing import List, Dict, Optional, Tuple
from collections import Counter

from api.models.database import get_db


# ── 中文标点（拼写纠正时忽略） ──────────────────────
PUNCTUATION = set("，。！？、；：""''（）【】《》·—…·,.:;!?()[]{}\"'")

# ── 常用中文停用词 ──────────────────────────────────
STOP_WORDS = set("的了在是有和我与就这那都而及但或一个不被把让向对从到").union(
    {"如何", "什么", "怎么", "为什么", "哪些", "哪个", "多少", "是否", "有没有"}
)


class QuerySuggestionService:
    """查询建议服务"""

    def suggest(self, query: str, user_id: str = "", limit: int = 3) -> Dict:
        """
        综合分析查询并生成建议

        返回:
            {
                "correction": str | None,     # 拼写纠正建议
                "correction_confidence": float,  # 纠正置信度 (0-1)
                "topics": [str],              # 推荐主题
                "related_queries": [str],     # 相近查询建议
            }
        """
        result = {
            "correction": None,
            "correction_confidence": 0.0,
            "topics": [],
            "related_queries": [],
        }

        try:
            # 1. 拼写纠正
            candidates = self._find_spelling_candidates(query)
            if candidates:
                best = candidates[0]
                if best["score"] >= 0.5:
                    result["correction"] = best["term"]
                    result["correction_confidence"] = round(best["score"], 3)

            # 2. 主题推荐
            result["topics"] = self._suggest_topics(query, user_id, limit)

            # 3. 相近查询
            result["related_queries"] = self._suggest_related_queries(query, user_id, limit)

        except Exception as e:
            print(f"[QuerySuggestion] 生成建议失败: {e}")

        return result

    # ── 拼写纠正 ──────────────────────────────────────

    def _find_spelling_candidates(self, query: str, max_candidates: int = 5) -> List[Dict]:
        """
        从 kb_entities 和 kb_documents 中查找拼写相近的候选词

        策略：
          1. 分词并去除非关键词（停用词、单字）
          2. 从数据库获取已知实体名和文档名
          3. 对每个关键词计算字符级 Jaccard 相似度
          4. 返回 TopN 候选
        """
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        known_terms = self._load_known_terms()
        candidates = []

        for kw in keywords:
            for term in known_terms:
                score = self._char_jaccard(kw, term)
                if score >= 0.3:
                    candidates.append({"original": kw, "term": term, "score": score})

        # 合并相似 candidate（相同 term 取最高分）
        merged = {}
        for c in candidates:
            key = c["term"]
            if key not in merged or c["score"] > merged[key]["score"]:
                merged[key] = c

        # 按分数降序
        result = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return result[:max_candidates]

    def _char_jaccard(self, a: str, b: str) -> float:
        """
        字符级 Jaccard 相似度
        
        对中文纠错特别适合：
          - "openai" vs "opneai" → 字符集相同，但顺序不同也能匹配
          - "大预言模型" vs "大语言模型" → 共享字符比例高
        """
        if not a or not b:
            return 0.0

        a_lower = a.lower().strip()
        b_lower = b.lower().strip()

        if a_lower == b_lower:
            return 1.0

        set_a = set(a_lower)
        set_b = set(b_lower)

        intersection = set_a & set_b
        union = set_a | set_b

        if not union:
            return 0.0

        base_score = len(intersection) / len(union)

        # 长度惩罚：长度差异越大，越不可能是纠错
        length_ratio = min(len(a_lower), len(b_lower)) / max(len(a_lower), len(b_lower), 1)
        
        return base_score * length_ratio

    # ── 主题推荐 ──────────────────────────────────────

    def _suggest_topics(self, query: str, user_id: str, limit: int = 3) -> List[str]:
        """
        基于现有知识推荐相关主题

        策略：
          1. 提取查询中的关键词
          2. 在 kb_entities 中查找相关实体类型
          3. 推荐同类型下的高频实体
        """
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        try:
            db = get_db()
            
            # 查找匹配的实体类型
            matched_types = set()
            for kw in keywords:
                result = db.client.table("kb_entities") \
                    .select("type") \
                    .ilike("name", f"%{kw}%") \
                    .execute()
                for row in (result.data or []):
                    if row.get("type"):
                        matched_types.add(row["type"])

            if not matched_types:
                return self._fallback_topics(query, keywords, limit)

            # 在同类型下找高频实体
            type_list = list(matched_types)[:3]
            type_filters = ",".join(f"type.eq.{t}" for t in type_list)
            result = db.client.table("kb_entities") \
                .select("name, count") \
                .or_(type_filters) \
                .execute()

            if result.data:
                topics = [row["name"] for row in result.data[:limit]]
                return topics

        except Exception as e:
            print(f"[QuerySuggestion] 主题推荐失败: {e}")

        return self._fallback_topics(query, keywords, limit)

    def _fallback_topics(self, query: str, keywords: List[str], limit: int = 3) -> List[str]:
        """降级：基于关键词的字面推荐"""
        # 简单返回查询中的非停用词关键词
        result = []
        for kw in keywords:
            if kw not in STOP_WORDS and len(kw) > 1:
                result.append(kw)
        return result[:limit]

    # ── 相近查询推荐 ──────────────────────────────────

    def _suggest_related_queries(self, query: str, user_id: str, limit: int = 3) -> List[str]:
        """
        推荐相近查询

        策略：
          1. 从 kb_entities 中找到与查询关键词相似的实体
          2. 从 kb_documents 中找到名称相似的其他文档
          3. 组合去重
        """
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        suggestions = []

        try:
            db = get_db()
            for kw in keywords:
                # 搜索文档名（取最相近的 3 个文档）
                docs = db.client.table("kb_documents") \
                    .select("name") \
                    .or_(f"is_public.eq.true,user_id.eq.{user_id}") \
                    .ilike("name", f"%{kw}%") \
                    .limit(5) \
                    .execute()
                for doc in (docs.data or []):
                    name = doc["name"]
                    # 去掉文件扩展名
                    name_clean = re.sub(r"\.(md|txt|pdf|docx)$", "", name, flags=re.IGNORECASE)
                    if name_clean and name_clean not in suggestions:
                        suggestions.append(name_clean)
                        if len(suggestions) >= limit:
                            break
                if len(suggestions) >= limit:
                    break

        except Exception as e:
            print(f"[QuerySuggestion] 相近查询推荐失败: {e}")

        return suggestions[:limit]

    # ── 工具方法 ──────────────────────────────────────

    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词（去停用词、去单字、去标点）"""
        # 去除标点
        clean = "".join(c for c in query if c not in PUNCTUATION)
        words = jieba.lcut(clean)
        return [
            w.strip().lower()
            for w in words
            if w.strip() and len(w.strip()) > 1 and w.strip() not in STOP_WORDS
        ]

    def _load_known_terms(self) -> List[str]:
        """
        加载已知术语（实体名 + 文档名）
        结果会被缓存到实例变量中以减少数据库查询
        """
        if hasattr(self, "_cached_terms") and self._cached_terms:
            return self._cached_terms

        terms = set()
        try:
            db = get_db()

            # 从实体表加载
            entities = db.client.table("kb_entities") \
                .select("name") \
                .limit(500) \
                .execute()
            for row in (entities.data or []):
                name = (row.get("name") or "").strip()
                if len(name) > 1:
                    terms.add(name)

            # 从文档表加载
            docs = db.client.table("kb_documents") \
                .select("name") \
                .limit(500) \
                .execute()
            for row in (docs.data or []):
                name = re.sub(r"\.(md|txt|pdf|docx)$", "", (row.get("name") or ""), flags=re.IGNORECASE)
                name = name.strip()
                if len(name) > 1:
                    terms.add(name)

        except Exception as e:
            print(f"[QuerySuggestion] 加载术语失败: {e}")

        self._cached_terms = list(terms)
        return self._cached_terms


# 单例
_suggester = None


def get_query_suggestion_service() -> QuerySuggestionService:
    global _suggester
    if _suggester is None:
        _suggester = QuerySuggestionService()
    return _suggester
