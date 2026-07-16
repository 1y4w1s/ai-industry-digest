"""Chat/Tag 仓储"""
from typing import Dict, List
from .base_repo import BaseRepository


class ChatRepository(BaseRepository):

    def upsert_user_tag(self, user_id: str, tag: str, source: str = "chat") -> None:
        existing = self.client.table("user_tags").select("id, weight").eq("user_id", user_id).eq("tag", tag).limit(1).execute()
        if existing.data:
            new_weight = (existing.data[0].get("weight") or 0) + 1
            self.client.table("user_tags").update({"weight": new_weight}).eq("id", existing.data[0]["id"]).execute()
        else:
            self.client.table("user_tags").insert({"user_id": user_id, "tag": tag, "weight": 1, "source": source}).execute()

    def get_user_tags(self, user_id: str) -> List[Dict]:
        result = self.client.table("user_tags").select("tag, weight").eq("user_id", user_id).order("weight", desc=True).execute()
        return result.data or []
