"""
Signal · 用户仓储
用户档案、统计、阅读历史
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
from .base_repo import BaseRepository


class UserRepository(BaseRepository):

    def get_or_create_profile(self, user_id: str, email: str) -> Dict:
        existing = self.client.table("user_profiles").select("*").eq("id", user_id).limit(1).execute()
        if existing.data:
            return existing.data[0]
        self.client.table("user_profiles").insert({"id": user_id, "email": email}).execute()
        return {"id": user_id, "email": email, "nickname": None}

    def add_reading_history(self, user_id: str, article_id: str, read_percent: int = 0) -> None:
        today = date.today().isoformat()
        existing = self.client.table("reading_history").select("id, read_percent").eq("user_id", user_id).eq("article_id", article_id).eq("read_date", today).limit(1).execute()
        if existing.data:
            existing_percent = existing.data[0].get("read_percent", 0)
            if read_percent > existing_percent:
                self.client.table("reading_history").update({"read_percent": read_percent}).eq("id", existing.data[0]["id"]).execute()
        else:
            self.client.table("reading_history").insert({"user_id": user_id, "article_id": article_id, "read_percent": read_percent, "read_date": today}).execute()

    def clear_reading_history(self, user_id: str) -> None:
        self.client.table("reading_history").delete().eq("user_id", user_id).execute()

    def get_reading_history(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        offset = (page - 1) * page_size
        result = self.client.table("reading_history").select("id, read_at, read_percent, articles(*)").eq("user_id", user_id).order("read_at", desc=True).range(offset, offset + page_size - 1).execute()
        total = result.count or 0
        return {"items": result.data or [], "total": total, "page": page, "page_size": page_size,
               "pages": (total + page_size - 1) // page_size if page_size > 0 else 0}

    def get_user_stats(self, user_id: str) -> Dict:
        bookmarks = self.client.table("bookmarks").select("id", count="exact").eq("user_id", user_id).execute()
        total_bookmarks = bookmarks.count or 0
        read_count = self.client.table("reading_history").select("id", count="exact").eq("user_id", user_id).execute()
        total_read = read_count.count or 0

        history_dates = self.client.table("reading_history").select("read_at").eq("user_id", user_id).order("read_at", desc=True).execute()
        streak = 0
        heatmap = {}
        source_dist = {}
        if history_dates.data:
            seen = set()
            for row in history_dates.data:
                d = row.get("read_at", "")[:10]
                if d:
                    seen.add(d)
            sorted_dates = sorted(seen, reverse=True)
            today = date.today()
            check = today
            for d_str in sorted_dates:
                d = datetime.strptime(d_str, "%Y-%m-%d").date()
                if d == check:
                    streak += 1
                    check -= timedelta(days=1)
                elif d < check:
                    break
            for i in range(365):
                d = (today - timedelta(days=i)).isoformat()
                heatmap[d] = heatmap.get(d, 0) + (1 if d in seen else 0)

        return {"total_bookmarks": total_bookmarks, "total_read": total_read, "streak_days": streak,
                "heatmap": heatmap, "source_distribution": source_dist}

    def get_reading_trends(self, user_id: str) -> Dict:
        history = self.client.table("reading_history").select("read_at").eq("user_id", user_id).order("read_at", desc=True).execute()
        records = history.data or []
        monthly = {}
        hourly = {h: 0 for h in range(24)}
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
        monthly_trend = [{"month": k, "count": v} for k, v in sorted(monthly.items())]
        peak_hour = max(hourly, key=hourly.get) if any(hourly.values()) else None
        return {"monthly_trend": monthly_trend, "hourly_distribution": hourly, "peak_hour": peak_hour}
