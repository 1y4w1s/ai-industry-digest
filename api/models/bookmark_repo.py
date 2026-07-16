"""Bookmark 仓储"""
from typing import Dict, List, Optional
from .base_repo import BaseRepository


class BookmarkRepository(BaseRepository):

    def add_bookmark(self, user_id: str, article_id: str, note: str = "") -> Dict:
        result = self.client.table("bookmarks").insert({"user_id": user_id, "article_id": article_id, "note": note}).execute()
        return result.data[0] if result.data else {"id": None}

    def remove_bookmark(self, bookmark_id: int, user_id: str) -> None:
        self.client.table("bookmarks").delete().eq("id", bookmark_id).eq("user_id", user_id).execute()

    def get_bookmarks(self, user_id: str, page: int = 1, page_size: int = 20) -> Dict:
        offset = (page - 1) * page_size
        result = self.client.table("bookmarks").select("*, articles(*)").eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
        total = result.count or 0
        return {"items": result.data or [], "total": total, "page": page, "page_size": page_size,
               "pages": (total + page_size - 1) // page_size if page_size > 0 else 0}

    def get_bookmark_id(self, user_id: str, article_id: str) -> Optional[int]:
        result = self.client.table("bookmarks").select("id").eq("user_id", user_id).eq("article_id", article_id).limit(1).execute()
        return result.data[0]["id"] if result.data else None
