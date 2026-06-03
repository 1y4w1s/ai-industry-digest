"""
AI Industry Digest - 数据库管理
Supabase 写入、查询、分页、搜索
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from supabase import create_client, Client
from dotenv import load_dotenv

from collector.base import Article

load_dotenv()


class DatabaseManager:
    """Supabase 数据库管理器"""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "请设置环境变量 SUPABASE_URL 和 SUPABASE_KEY\n"
                "提示: 在项目根目录创建 .env 文件:\n"
                "  SUPABASE_URL=https://xxx.supabase.co\n"
                "  SUPABASE_KEY=your-service-role-key"
            )
        self.client: Client = create_client(url, key)

    # ── 写入 ─────────────────────────────────────

    def save_articles(self, articles: List[Article]) -> dict:
        """批量写入文章到 Supabase（自动去重）"""
        result = {"inserted": 0, "skipped": 0, "errors": 0}

        for article in articles:
            try:
                existing = self.client.table("articles") \
                    .select("id") \
                    .eq("url", article.url) \
                    .execute()

                if existing.data and len(existing.data) > 0:
                    result["skipped"] += 1
                    continue

                data = {
                    "title": article.title,
                    "url": article.url,
                    "source_name": article.source_name,
                    "raw_content": article.raw_content[:50000],
                    "summary": article.summary or "",
                    "tags": article.tags or [],
                    "importance": article.importance or "low",
                    "importance_reason": article.importance_reason or "",
                    "source_refs": article.source_refs or [],
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                }
                self.client.table("articles").insert(data).execute()
                result["inserted"] += 1

            except Exception as e:
                print(f"    [DB ERROR] 写入失败 [{article.url[:50]}...]: {e}")
                result["errors"] += 1

        return result

    # ── 文章查询（分页 + 搜索 + 过滤） ─────────────

    def get_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        tag: Optional[str] = None,
        source: Optional[str] = None,
        importance: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = "published_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """分页查询文章
        Returns:
            {"items": [...], "total": N, "page": P, "page_size": S, "pages": T}
        """
        query = self.client.table("articles").select("*", count="exact")

        # 过滤条件
        if keyword:
            query = query.ilike("title", f"%{keyword}%")
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

        # 排序
        order_direction = sort_order if sort_order in ("asc", "desc") else "desc"
        query = query.order(sort_by, desc=(order_direction == "desc"))

        # 分页
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        result = query.execute()

        total = result.count or 0
        return {
            "items": result.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    def get_article_by_id(self, article_id: str) -> Optional[dict]:
        """按 ID 获取单篇文章"""
        result = self.client.table("articles") \
            .select("*") \
            .eq("id", article_id) \
            .execute()
        return result.data[0] if result.data else None

    # ── 日报查询（分页） ─────────────────────────

    def get_reports(
        self,
        page: int = 1,
        page_size: int = 7,
    ) -> Dict[str, Any]:
        """分页查询日报列表"""
        query = self.client.table("daily_reports") \
            .select("*", count="exact") \
            .order("report_date", desc=True)

        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        result = query.execute()

        total = result.count or 0
        return {
            "items": result.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    def get_report_by_date(self, report_date: str) -> Optional[dict]:
        """按日期获取单日报详情"""
        result = self.client.table("daily_reports") \
            .select("*") \
            .eq("report_date", report_date) \
            .execute()
        if not result.data:
            return None

        report = result.data[0]

        # 如果有关联文章 ID，查询文章详情
        article_ids = report.get("article_ids", [])
        if article_ids:
            articles = self.client.table("articles") \
                .select("*") \
                .in_("id", article_ids) \
                .execute()
            report["articles"] = articles.data or []
        else:
            report["articles"] = []

        return report

    # ── 统计信息 ────────────────────────────────

    def get_article_count(self) -> int:
        """获取文章总数"""
        result = self.client.table("articles") \
            .select("id", count="exact") \
            .execute()
        return result.count or 0

    def get_sources(self) -> List[str]:
        """获取所有信息来源列表"""
        result = self.client.table("articles") \
            .select("source_name") \
            .execute()
        sources = set()
        for row in result.data or []:
            if row.get("source_name"):
                sources.add(row["source_name"])
        return sorted(sources)

    def get_tags(self) -> List[str]:
        """获取所有标签列表"""
        result = self.client.table("articles") \
            .select("tags") \
            .execute()
        tags = set()
        for row in result.data or []:
            for tag in row.get("tags", []) or []:
                tags.add(tag)
        return sorted(tags)

    # ── 用户相关操作 ────────────────────────────

    def get_or_create_profile(self, user_id: str, nickname: Optional[str] = None,
                              avatar_url: Optional[str] = None) -> dict:
        """获取或创建用户扩展信息"""
        result = self.client.table("user_profiles") \
            .select("*") \
            .eq("id", user_id) \
            .execute()

        if result.data:
            return result.data[0]

        # 创建新 profile
        data = {"id": user_id}
        if nickname:
            data["nickname"] = nickname
        if avatar_url:
            data["avatar_url"] = avatar_url

        self.client.table("user_profiles").insert(data).execute()
        return data

    def add_bookmark(self, user_id: str, article_id: str, note: str = "") -> dict:
        """添加收藏"""
        data = {
            "user_id": user_id,
            "article_id": article_id,
            "note": note,
        }
        result = self.client.table("bookmarks") \
            .insert(data) \
            .execute()
        return result.data[0] if result.data else {}

    def remove_bookmark(self, bookmark_id: str, user_id: str) -> bool:
        """取消收藏"""
        result = self.client.table("bookmarks") \
            .delete() \
            .eq("id", bookmark_id) \
            .eq("user_id", user_id) \
            .execute()
        return len(result.data) > 0

    def get_bookmarks(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取用户收藏列表"""
        query = self.client.table("bookmarks") \
            .select("*, articles(*)", count="exact") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True)

        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        result = query.execute()

        total = result.count or 0
        return {
            "items": result.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    def add_reading_history(self, user_id: str, article_id: str) -> bool:
        """记录浏览历史（同一天同一篇只记一次）"""
        today = date.today().isoformat()
        existing = self.client.table("reading_history") \
            .select("id") \
            .eq("user_id", user_id) \
            .eq("article_id", article_id) \
            .gte("read_at", today) \
            .execute()

        if existing.data:
            return False  # 已记录过

        self.client.table("reading_history") \
            .insert({"user_id": user_id, "article_id": article_id}) \
            .execute()
        return True

    def get_reading_history(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取用户浏览历史"""
        query = self.client.table("reading_history") \
            .select("*, articles(*)", count="exact") \
            .eq("user_id", user_id) \
            .order("read_at", desc=True)

        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        result = query.execute()

        total = result.count or 0
        return {
            "items": result.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    def submit_feedback(self, user_id: str, article_id: str, feedback: str) -> dict:
        """提交文章反馈 👍/👎"""
        if feedback not in ("thumbs_up", "thumbs_down"):
            raise ValueError("feedback 必须是 thumbs_up 或 thumbs_down")

        data = {
            "user_id": user_id,
            "article_id": article_id,
            "feedback": feedback,
        }
        result = self.client.table("article_feedback") \
            .upsert(data, on_conflict="user_id,article_id") \
            .execute()
        return result.data[0] if result.data else {}
