"""
Signal - 数据库管理
Supabase 写入、查询、分页、搜索
"""

import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from supabase import create_client, Client
from dotenv import load_dotenv

from collector.base import Article

load_dotenv()


class DatabaseManager:
    """Supabase 数据库管理器"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

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
        self._url = url
        self._key = key
        self.client: Client = self._create_client()

    def _create_client(self) -> Client:
        """创建 Supabase 客户端"""
        return create_client(self._url, self._key)

    def _execute_with_retry(self, operation, *args, **kwargs):
        """带重试机制的数据库操作"""
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    wait = self.RETRY_DELAY * (2 ** attempt)
                    print(f"  [DB RETRY] 操作失败，{wait}秒后重试 ({attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(wait)
                    # 重新创建客户端（处理连接断开）
                    self.client = self._create_client()
                else:
                    print(f"  [DB ERROR] 操作最终失败: {e}")
                    raise
        raise last_error

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
            # 优先全文搜索，fallback 到 ilike
            query = query.or_(
                f"search_vector.phfts.{keyword},title.ilike.%{keyword}%"
            )
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

    def get_report_dates(self) -> list:
        """获取所有已有日报的日期列表（用于归档日历）"""
        result = self.client.table("daily_reports") \
            .select("report_date") \
            .order("report_date", desc=True) \
            .execute()
        return [row["report_date"] for row in (result.data or []) if row.get("report_date")]

    def get_report_by_date(self, report_date: str) -> Optional[dict]:
        """按日期获取单日报详情"""
        result = self.client.table("daily_reports") \
            .select("*") \
            .eq("report_date", report_date) \
            .execute()
        if not result.data:
            return None

        report = result.data[0]

        # 如果有关联文章 ID，查询文章详情并按重要性分组
        article_ids = report.get("article_ids", [])
        if article_ids:
            raw = self.client.table("articles") \
                .select("*") \
                .in_("id", article_ids) \
                .execute()
            raw_articles = raw.data or []

            # 按重要性分组
            grouped = {"high": [], "medium": [], "low": []}
            for a in raw_articles:
                imp = a.get("importance", "low") or "low"
                if imp in grouped:
                    grouped[imp].append(a)
                else:
                    grouped["low"].append(a)

            report["articles"] = grouped
        else:
            report["articles"] = {"high": [], "medium": [], "low": []}

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

    def add_reading_history(self, user_id: str, article_id: str,
                            read_percent: Optional[float] = None,
                            duration_sec: Optional[int] = None) -> bool:
        """记录浏览历史（同天同篇取 max read_percent）"""
        today = date.today().isoformat()
        existing = self.client.table("reading_history") \
            .select("id, read_percent") \
            .eq("user_id", user_id) \
            .eq("article_id", article_id) \
            .gte("read_at", today) \
            .execute()

        if existing.data:
            # 已存在 → 更新 read_percent（取较大值）
            existing_id = existing.data[0]["id"]
            existing_pct = existing.data[0].get("read_percent")
            if read_percent is not None and (
                existing_pct is None or read_percent > existing_pct
            ):
                self.client.table("reading_history") \
                    .update({"read_percent": read_percent, "read_at": datetime.now().isoformat()}) \
                    .eq("id", existing_id) \
                    .execute()
            return False

        # 不存在 → 插入
        data = {"user_id": user_id, "article_id": article_id}
        if read_percent is not None:
            data["read_percent"] = read_percent
        if duration_sec is not None:
            data["duration_sec"] = duration_sec
        self.client.table("reading_history") \
            .insert(data) \
            .execute()
        return True

    def clear_reading_history(self, user_id: str) -> bool:
        """清除用户所有浏览历史"""
        self.client.table("reading_history") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()
        return True

    # ── 用户画像 ────────────────────────────

    def upsert_user_tag(self, user_id: str, tag: str, source: str = 'chat') -> None:
        """更新用户标签权重（存在则 +1，不存在则插入）"""
        now = datetime.now().isoformat()
        # 检查是否已存在
        existing = self.client.table("user_tags") \
            .select("weight") \
            .eq("user_id", user_id) \
            .eq("tag", tag) \
            .eq("source", source) \
            .execute()
        if existing.data:
            # 存在 → 权重 +1
            self.client.table("user_tags") \
                .update({"weight": existing.data[0]["weight"] + 1, "updated_at": now}) \
                .eq("user_id", user_id) \
                .eq("tag", tag) \
                .eq("source", source) \
                .execute()
        else:
            # 不存在 → 插入
            self.client.table("user_tags") \
                .insert({"user_id": user_id, "tag": tag, "weight": 1, "source": source, "updated_at": now}) \
                .execute()

    def get_user_tags(self, user_id: str) -> List[dict]:
        """获取用户所有标签权重"""
        result = self.client.table("user_tags") \
            .select("tag, weight, source") \
            .eq("user_id", user_id) \
            .order("weight", desc=True) \
            .execute()
        return result.data or []

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

    def get_user_stats(self, user_id: str) -> dict:
        """获取用户统计信息"""
        # 收藏总数
        bookmark_count = self.client.table("bookmarks") \
            .select("id", count="exact") \
            .eq("user_id", user_id) \
            .execute()
        total_bookmarks = bookmark_count.count or 0

        # 阅读总数
        history_count = self.client.table("reading_history") \
            .select("id", count="exact") \
            .eq("user_id", user_id) \
            .execute()
        total_read = history_count.count or 0

        # 连续阅读天数
        streak = 0
        history_dates = self.client.table("reading_history") \
            .select("read_at") \
            .eq("user_id", user_id) \
            .order("read_at", desc=True) \
            .execute()
        if history_dates.data:
            seen = set()
            for row in history_dates.data:
                d = row.get("read_at", "")[:10]
                if d:
                    seen.add(d)
            sorted_dates = sorted(seen, reverse=True)
            streak = 0
            today = date.today()
            check = today
            for d_str in sorted_dates:
                d = datetime.strptime(d_str, "%Y-%m-%d").date()
                if d == check:
                    streak += 1
                    check -= timedelta(days=1)
                elif d < check:
                    break

        # 月度阅读热力图（最近 365 天）
        heatmap = {}
        today = date.today()
        for i in range(365):
            d = today - timedelta(days=i)
            heatmap[d.isoformat()] = 0
        if history_dates.data:
            for row in history_dates.data:
                d = row.get("read_at", "")[:10]
                if d in heatmap:
                    heatmap[d] += 1

        # 来源分布
        source_dist = {}
        history_articles = self.client.table("reading_history") \
            .select("articles(source_name)") \
            .eq("user_id", user_id) \
            .execute()
        if history_articles.data:
            for row in history_articles.data:
                article = row.get("articles") or {}
                src = article.get("source_name")
                if src:
                    source_dist[src] = source_dist.get(src, 0) + 1

        return {
            "total_bookmarks": total_bookmarks,
            "total_read": total_read,
            "streak_days": streak,
            "heatmap": heatmap,
            "source_distribution": source_dist,
        }

    def get_reading_trends(self, user_id: str) -> dict:
        """获取阅读趋势统计"""
        history = self.client.table("reading_history") \
            .select("read_at, articles(raw_content)") \
            .eq("user_id", user_id) \
            .order("read_at", desc=True) \
            .execute()

        records = history.data or []

        # Monthly trend (last 6 months)
        monthly = {}
        # Hour distribution
        hourly = {h: 0 for h in range(24)}
        total_chars = 0
        total_read_with_content = 0

        for row in records:
            read_at = row.get("read_at", "")
            if read_at:
                month_key = read_at[:7]
                monthly[month_key] = monthly.get(month_key, 0) + 1

                try:
                    hour = int(read_at[11:13])
                    hourly[hour] = hourly.get(hour, 0) + 1
                except (ValueError, IndexError):
                    pass

                article = row.get("articles") or {}
                raw = article.get("raw_content") or ""
                if raw:
                    total_chars += len(raw)
                    total_read_with_content += 1

        # Build monthly trend array (last 6 months, sorted)
        today = date.today()
        monthly_trend = []
        for i in range(5, -1, -1):
            y = today.year
            m = today.month - i
            if m <= 0:
                y -= 1
                m += 12
            key = f"{y}-{str(m).zfill(2)}"
            monthly_trend.append({"month": key, "count": monthly.get(key, 0)})

        # Peak reading hour
        peak_hour = max(hourly, key=hourly.get) if any(hourly.values()) else None

        # Avg read length
        avg_read_length = round(total_chars / total_read_with_content) if total_read_with_content > 0 else 0

        return {
            "monthly_trend": monthly_trend,
            "hourly_distribution": hourly,
            "peak_hour": peak_hour,
            "avg_read_length": avg_read_length,
        }
