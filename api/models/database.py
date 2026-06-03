"""
AI Industry Digest - 数据库管理
Supabase 写入与查询
"""

import os
from typing import List, Optional
from datetime import datetime

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

    def save_articles(self, articles: List[Article]) -> dict:
        """批量写入文章到 Supabase（自动去重）
        返回: {"inserted": N, "skipped": N, "errors": N}
        """
        result = {"inserted": 0, "skipped": 0, "errors": 0}

        for article in articles:
            try:
                # 检查 URL 是否已存在
                existing = self.client.table("articles") \
                    .select("id") \
                    .eq("url", article.url) \
                    .execute()

                if existing.data and len(existing.data) > 0:
                    result["skipped"] += 1
                    continue

                # 写入新文章
                data = {
                    "title": article.title,
                    "url": article.url,
                    "source_name": article.source_name,
                    "raw_content": article.raw_content[:50000],  # 截断超长内容
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                }
                self.client.table("articles").insert(data).execute()
                result["inserted"] += 1

            except Exception as e:
                print(f"    [DB ERROR] 写入失败 [{article.url[:50]}...]: {e}")
                result["errors"] += 1

        return result

    def get_recent_articles(self, limit: int = 10) -> List[dict]:
        """获取最近的文章（用于验证）"""
        result = self.client.table("articles") \
            .select("*") \
            .order("published_at", desc=True) \
            .limit(limit) \
            .execute()
        return result.data

    def get_article_count(self) -> int:
        """获取文章总数"""
        result = self.client.table("articles") \
            .select("id", count="exact") \
            .execute()
        return result.count or 0
