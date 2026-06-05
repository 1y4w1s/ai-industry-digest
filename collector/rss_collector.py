"""
Signal - RSS 采集器
通过 RSS/Atom Feed 订阅获取文章
RSS 仅提供摘要时，自动尝试从原文 URL 抓取完整内容
"""

from datetime import datetime
from typing import List, Optional
import feedparser
import requests
from bs4 import BeautifulSoup

from collector.base import BaseCollector, Article


class RSSCollector(BaseCollector):
    """RSS/Atom Feed 采集器"""

    MIN_CONTENT_LENGTH = 100  # RSS 内容 < 100 字符时，视为摘要而非全文

    def _fetch_full_content(self, url: str) -> Optional[str]:
        """尝试从原文 URL 抓取完整正文，保留 HTML 结构"""
        if not url:
            return None
        try:
            resp = requests.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/125.0.0.0 Safari/537.36"
                }
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 尝试常见正文选择器（按优先级）
            selectors = [
                'article',
                '.entry-content',
                '.post-content',
                '.article-content',
                '.rich_media_content',
                '.content',
                '#article-content',
                '.article-detail',
                '.post',
                'main',
            ]
            for sel in selectors:
                el = soup.select_one(sel)
                if el:
                    # 移除无用元素
                    for tag in el.select('script, style, nav, footer, .ads, .ad, .comments, .share, .related, .recommend'):
                        tag.decompose()
                    # 保留结构化 HTML：p, h2, h3, h4, ul, ol, li, strong, em, blockquote, br
                    inner = el.encode_contents().decode('utf-8')
                    if len(inner) > self.MIN_CONTENT_LENGTH:
                        return self._clean_html(inner)

            # 降级：取 body 内所有内容
            body = soup.find('body')
            if body:
                for tag in body.select('script, style, nav, footer, header'):
                    tag.decompose()
                inner = body.encode_contents().decode('utf-8')
                if len(inner) > self.MIN_CONTENT_LENGTH:
                    return self._clean_html(inner)

        except Exception as e:
            print(f"    [WARN] 抓取全文失败 {url[:50]}: {e}")
        return None

    @staticmethod
    def _clean_html(html: str) -> str:
        """清理 HTML：只保留安全的排版标签，移除属性"""
        import re

        # 移除不安全的标签和内容
        html = re.sub(r'<(script|style|iframe|object|embed|form|input|button|select|textarea)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # 允许的安全标签列表
        allowed = {
            'p': True, 'br': True,
            'h1': True, 'h2': True, 'h3': True, 'h4': True,
            'ul': True, 'ol': True, 'li': True,
            'strong': True, 'b': True,
            'em': True, 'i': True,
            'blockquote': True,
            'pre': True, 'code': True,
        }

        # 移除所有不在允许列表中的标签（保留内容）
        def strip_tag(m):
            tag = m.group(1).lower().split()[0].rstrip('>').rstrip('/')
            if tag in allowed:
                return m.group(0)  # 保留
            return ''  # 移除标签但保留内容

        html = re.sub(r'<[^>]+>', strip_tag, html)

        # 清理多余的空白行
        html = re.sub(r'\n{3,}', '\n\n', html)
        html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', html)

        return html.strip()

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

                # RSS 只提供摘要时，从原文 URL 抓取完整正文
                if len(content.strip()) < self.MIN_CONTENT_LENGTH:
                    fetched = self._fetch_full_content(url)
                    if fetched:
                        content = fetched

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

        # RSS 只提供摘要时，从原文 URL 抓取完整正文
        if len(content.strip()) < self.MIN_CONTENT_LENGTH:
            fetched = self._fetch_full_content(url)
            if fetched:
                print(f"    [FETCH] 从原文抓取全文成功: {title[:40]} ({len(fetched)} chars)")
                content = fetched

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
