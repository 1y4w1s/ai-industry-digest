"""
Signal - RSS 采集器
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
                print(f"  [WARN] {self.name}: feedparser 解析失败 ({feed.bozo_exception})")
                print(f"  [FALLBACK] 尝试手动解析 XML...")
                articles = self._parse_raw_rss(feed_url)
                if articles:
                    print(f"  [OK] {self.name}: 手动解析成功，采集到 {len(articles)} 篇文章")
                    return articles
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

    def _parse_raw_rss(self, feed_url: str) -> List[Article]:
        """手动解析格式异常的 RSS XML（feedparser 失败时备用）"""
        import re
        import requests

        try:
            resp = requests.get(
                feed_url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Industry-Digest/1.0)"}
            )
            raw = resp.text
        except Exception as e:
            print(f"    [ERROR] 获取原始 XML 失败: {e}")
            return []

        # 提取所有 <item> 块（使用非贪婪匹配，绕过 CDATA 内的标签问题）
        items = re.findall(r'<item>(.*?)</item>', raw, re.DOTALL)
        if not items:
            # 尝试 Atom 格式
            items = re.findall(r'<entry>(.*?)</entry>', raw, re.DOTALL)

        articles = []
        for item_xml in items:
            try:
                title = self._extract_tag(item_xml, 'title')
                url = self._extract_tag(item_xml, 'link')
                if not title or not url:
                    continue

                # 提取描述（优先 content:encoded 然后是 description）
                content = self._extract_tag(item_xml, 'content:encoded')
                if not content:
                    content = self._extract_tag(item_xml, 'description')

                # 提取发布时间
                pub_date = self._extract_tag(item_xml, 'pubDate')
                published_at = None
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        published_at = parsedate_to_datetime(pub_date)
                    except Exception:
                        pass

                article = self._make_article(
                    title=title,
                    url=url,
                    content=content,
                    published_at=published_at
                )
                articles.append(article)
            except Exception as e:
                print(f"    [WARN] 手动解析条目失败: {e}")
                continue

        return articles

    @staticmethod
    def _extract_tag(xml_block: str, tag: str) -> str:
        """从 XML 块中提取标签内容（处理 CDATA）"""
        import re
        # 匹配 <tag>content</tag> 或 <tag><![CDATA[content]]></tag>
        pattern = rf'<{tag}[^>]*>(?:<!\[CDATA\[(.*?)\]\]>|(.*?))</{tag}>'
        match = re.search(pattern, xml_block, re.DOTALL)
        if match:
            return (match.group(1) or match.group(2) or "").strip()
        return ""

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
