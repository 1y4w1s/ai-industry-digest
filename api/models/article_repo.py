"""
Signal · 文章仓储
文章查询、搜索、日报数据
"""

from typing import Optional, Dict, Any, List
from datetime import date
from .base_repo import BaseRepository
from ..services.cache import cache, cache_key, invalidate_cache
from ..services.logger import logger
from ..services.tokenizer import build_search_text


class ArticleRepository(BaseRepository):

    def save_articles(self, articles: List) -> dict:
        """批量写入文章到 Supabase（批量查重 + 批量 upsert）"""
        from ..models.article import Article
        
        result = {"inserted": 0, "skipped": 0, "errors": 0}
        if not articles:
            return result

        all_urls = [a.url for a in articles]
        existing_urls = set()
        BATCH_SIZE = 500

        for i in range(0, len(all_urls), BATCH_SIZE):
            batch = all_urls[i:i + BATCH_SIZE]
            try:
                resp = self.client.table("articles").select("url").in_("url", batch).execute()
                if resp.data:
                    existing_urls.update(item["url"] for item in resp.data)
            except Exception as e:
                logger.error("批量查重失败", extra={"error": str(e)})
                result["errors"] += 1
                return self._save_articles_fallback(articles)

        new_articles = [a for a in articles if a.url not in existing_urls]
        result["skipped"] = len(articles) - len(new_articles)
        if not new_articles:
            return result

        for i in range(0, len(new_articles), BATCH_SIZE):
            batch = new_articles[i:i + BATCH_SIZE]
            data_list = []
            for a in batch:
                data_list.append({
                    "search_text": build_search_text(
                        title=a.title, summary=a.summary or "",
                        source_name=a.source_name, tags=a.tags or []
                    ),
                    "title": a.title, "url": a.url, "source_name": a.source_name,
                    "raw_content": a.raw_content[:50000], "summary": a.summary or "",
                    "tags": a.tags or [], "importance": a.importance or "low",
                    "importance_reason": a.importance_reason or "",
                    "so_what": getattr(a, "so_what", None),
                    "source_refs": a.source_refs or [],
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                })
            try:
                self.client.table("articles").upsert(data_list, on_conflict="url", ignore_duplicates=True).execute()
                result["inserted"] += len(data_list)
            except Exception as e:
                logger.error("批量写入失败", extra={"error": str(e)})
                result["errors"] += len(data_list)

        if result["inserted"] > 0:
            invalidate_cache("articles:*")
        return result

    def _save_articles_fallback(self, articles: List) -> dict:
        """逐条插入（降级路径）"""
        result = {"inserted": 0, "skipped": 0, "errors": 0}
        for article in articles:
            try:
                existing = self.client.table("articles").select("id").eq("url", article.url).execute()
                if existing.data and len(existing.data) > 0:
                    result["skipped"] += 1
                    continue
                data = {
                    "search_text": build_search_text(
                        title=article.title, summary=article.summary or "",
                        source_name=article.source_name, tags=article.tags or []
                    ),
                    "title": article.title, "url": article.url, "source_name": article.source_name,
                    "raw_content": article.raw_content[:50000], "summary": article.summary or "",
                    "tags": article.tags or [], "importance": article.importance or "low",
                    "importance_reason": article.importance_reason or "",
                    "so_what": getattr(article, "so_what", None),
                    "source_refs": article.source_refs or [],
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                }
                self.client.table("articles").insert(data).execute()
                result["inserted"] += 1
            except Exception as e:
                logger.error("写入失败", extra={"url": article.url[:50], "error": str(e)})
                result["errors"] += 1
        if result["inserted"] > 0:
            invalidate_cache("articles:*")
        return result

    def get_articles(
        self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None,
        tag: Optional[str] = None, source: Optional[str] = None,
        importance: Optional[str] = None, date_from: Optional[str] = None,
        date_to: Optional[str] = None, sort_by: str = "published_at",
        sort_order: str = "desc", use_cache: bool = True,
    ) -> Dict[str, Any]:
        """分页查询文章"""
        if use_cache and not keyword:
            key = cache_key("articles", page, page_size, tag=tag, source=source,
                           importance=importance, date_from=date_from, date_to=date_to,
                           sort_by=sort_by, sort_order=sort_order)
            cached = cache.get(key)
            if cached is not None:
                return cached

        # RPC 搜索
        if keyword:
            try:
                offset = (page - 1) * page_size
                rpc_result = self.client.rpc("search_articles_ranked", {
                    "search_query": keyword, "result_limit": page_size, "result_offset": offset,
                }).execute()
                count_result = self.client.rpc("search_articles_count", {"search_query": keyword}).execute()
                items = rpc_result.data or []
                total = count_result.data[0]["search_articles_count"] if count_result.data else 0
                data = {"items": items, "total": total, "page": page, "page_size": page_size,
                       "pages": (total + page_size - 1) // page_size if page_size > 0 else 0}
                cache_key_str = cache_key("search", keyword, page, page_size)
                cache.set(cache_key_str, data, ttl=300)
                return data
            except Exception as e:
                logger.warning("RPC 搜索降级", extra={"error": str(e)[:100]})

        query = self.client.table("articles").select("*", count="exact")
        if keyword:
            query = query.or_(f"search_vector.phfts.{keyword},title.ilike.%{keyword}%")
        if tag:
            query = query.contains("tags", [tag])
        if source:
            query = query.eq("source_name", source)
        if importance:
            query = query.eq("importance", importance)
        if date_from:
            query = query.gte("published_at", date_from)
        if date_to:
            query = query.lte("published_at", date_to)

        order_direction = sort_order if sort_order in ("asc", "desc") else "desc"
        query = query.order(sort_by, desc=(order_direction == "desc"))
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        result = query.execute()
        total = result.count or 0
        data = {"items": result.data, "total": total, "page": page, "page_size": page_size,
               "pages": (total + page_size - 1) // page_size if page_size > 0 else 0}

        if use_cache and not keyword:
            key = cache_key("articles", page, page_size, tag=tag, source=source,
                           importance=importance, date_from=date_from, date_to=date_to,
                           sort_by=sort_by, sort_order=sort_order)
            cache.set(key, data, ttl=300)
        return data

    def get_article_by_id(self, article_id: str) -> Optional[Dict]:
        result = self.client.table("articles").select("*").eq("id", article_id).limit(1).execute()
        return result.data[0] if result.data else None

    def get_article_count(self) -> int:
        result = self.client.table("articles").select("id", count="exact").limit(0).execute()
        return result.count or 0

    def get_sources(self) -> List[str]:
        result = self.client.table("articles").select("source_name").order("source_name").execute()
        seen = set()
        return [r["source_name"] for r in (result.data or []) if r["source_name"] not in seen and not seen.add(r["source_name"])]

    def get_tags(self) -> List[str]:
        result = self.client.table("articles").select("tags").execute()
        seen = set()
        tags = []
        for r in (result.data or []):
            for t in (r.get("tags") or []):
                if t not in seen:
                    seen.add(t)
                    tags.append(t)
        return sorted(tags)
