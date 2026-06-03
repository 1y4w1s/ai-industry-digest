"""
AI Industry Digest - RSS 采集器
通过 RSS/Atom Feed 订阅获取文章
"""

from datetime import datetime
from typing import List, Optional
import feedparser

from collector.base import BaseCollector, Article


class RSSCollector(BaseCollector):
    """RSS/Atom Feed 采集器"""

    def collect(self) -> List[Article]:
        """解析 RSS Feed 并返回文章列表
        支持多个 RSS URL 回退：第一个失败则尝试第二个
        """
        collectors = self.config.get("collectors", [])
        rss_configs = [c for c in collectors if c.get("type") == "rss"]
        if not rss_configs:
            print(f"  [WARN] {self.name}: 未配置 RSS 源")
            return []

        for idx, rss_config in enumerate(rss_configs):
            feed_url = rss_config.get("url")
            timeout = rss_config.get("timeout", 30)

            if idx > 0:
                print(f"  [FALLBACK] 尝试备用 RSS: {feed_url}")

            print(f"  [FETCH] {self.name}: 正在抓取 {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
            except Exception as e:
                print(f"  [ERROR] {self.name}: 抓取失败 - {e}")
                continue

            if feed.bozo and not feed.entries:
                print(f"  [WARN] {self.name}: RSS 格式异常 - {feed.bozo_exception}")
                continue

            if feed.bozo and feed.entries:
                print(f"  [WARN] {self.name}: RSS 格式有小问题，尝试继续解析")

            articles = []
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    print(f"  [WARN] {self.name}: 解析条目失败 - {e}")
                    continue

            if articles:
                print(f"  [OK] {self.name}: 采集到 {len(articles)} 篇文章")
                return articles

        print(f"  [EMPTY] {self.name}: 所有 RSS 源均失败")
        return []

    def _parse_entry(self, entry) -> Optional[Article]:
        """解析单条 RSS 条目"""
        # 标题
        title = entry.get("title", "")
        if not title:
            return None

        # 链接
        url = entry.get("link", "")
        # 某些 RSS 的 link 可能是相对路径
        if url and not url.startswith("http"):
            return None
        if not url:
            return None

        # 正文/描述
        content = ""
        # 优先取 content（完整内容），没有则取 summary（摘要）
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        elif entry.get("summary"):
            content = entry.get("summary", "")
        elif entry.get("description"):
            content = entry.get("description", "")

        # 发布时间
        published_at = None
        if entry.get("published_parsed"):
            import time
            published_at = datetime(*entry.published_parsed[:6])
        elif entry.get("updated_parsed"):
            import time
            published_at = datetime(*entry.updated_parsed[:6])

        return self._make_article(
            title=title,
            url=url,
            content=content,
            published_at=published_at
        )
