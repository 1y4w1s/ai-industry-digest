"""
Signal - arXiv API 采集器
通过 arXiv API 获取最新论文
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import urllib.error

from collector.base import BaseCollector, Article


class ArxivCollector(BaseCollector):
    """arXiv API 采集器"""
    BASE_URL = "http://export.arxiv.org/api/query"
    # arXiv API 限流：每 3 秒最多 1 次请求
    REQUEST_INTERVAL = 3.0
    _last_request_time = 0.0

    @classmethod
    def _rate_limit(cls):
        """类级别限流：所有实例共享"""
        elapsed = time.time() - cls._last_request_time
        if elapsed < cls.REQUEST_INTERVAL:
            wait = cls.REQUEST_INTERVAL - elapsed
            time.sleep(wait)
        cls._last_request_time = time.time()

    def collect(self) -> List[Article]:
        """查询 arXiv API 并返回论文列表"""
        # 从配置中获取参数
        collectors = self.config.get("collectors", [])
        api_config = next((c for c in collectors if c.get("type") == "api"), None)
        if not api_config:
            print(f"  [WARN] {self.name}: 未配置 API 参数")
            return []

        params = api_config.get("params", {})
        category = params.get("category", "cs.AI")
        max_results = params.get("max_results", 30)

        # 查询近 3 天的新论文
        since_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y%m%d")
        query = (
            f"search_query=cat:{category}"
            f"&sortBy=submittedDate"
            f"&sortOrder=descending"
            f"&max_results={max_results}"
        )
        url = f"{self.BASE_URL}?{query}"

        print(f"  [FETCH] {self.name} ({category}): 正在查询 arXiv API")

        try:
            self._rate_limit()  # 限流等待
            req = urllib.request.Request(url, headers={"User-Agent": "AI-Industry-Digest/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                xml_data = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  [WARN] {self.name}: 触发限流 (429)，额外等待 10 秒后重试")
                time.sleep(10)
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "AI-Industry-Digest/1.0"})
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        xml_data = resp.read().decode("utf-8")
                except Exception as e2:
                    print(f"  [ERROR] {self.name}: API 重试请求失败 - {e2}")
                    return []
            else:
                print(f"  [ERROR] {self.name}: API 请求失败 - {e}")
                return []
        except Exception as e:
            print(f"  [ERROR] {self.name}: API 请求失败 - {e}")
            return []

        articles = self._parse_response(xml_data)
        print(f"  [OK] {self.name}: 采集到 {len(articles)} 篇论文")
        return articles

    def _parse_response(self, xml_data: str) -> List[Article]:
        """解析 arXiv API 返回的 XML 数据"""
        articles = []

        # arXiv API 返回的是 Atom 格式
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            print(f"  [ERROR] {self.name}: XML 解析失败 - {e}")
            return []

        for entry in root.findall("atom:entry", ns):
            try:
                article = self._parse_entry(entry, ns)
                if article:
                    articles.append(article)
            except Exception as e:
                print(f"  [WARN] {self.name}: 解析条目失败 - {e}")
                continue

        return articles

    def _parse_entry(self, entry, ns: dict) -> Optional[Article]:
        """解析单条 Atom 条目"""
        # 标题
        title_el = entry.find("atom:title", ns)
        if title_el is None or not title_el.text:
            return None
        title = title_el.text.strip().replace("\n", " ")

        # 链接 - arXiv 的 link 在 <id> 标签中
        link_el = entry.find("atom:id", ns)
        url = link_el.text.strip() if link_el is not None else ""

        # 摘要
        summary_el = entry.find("atom:summary", ns)
        summary = summary_el.text.strip() if summary_el is not None else ""
        # arXiv 摘要可能包含"\\n"，替换掉
        summary = summary.replace("\n", " ").replace("  ", " ")

        # 发布时间
        published_el = entry.find("atom:published", ns)
        published_at = None
        if published_el is not None and published_el.text:
            try:
                published_at = datetime.strptime(
                    published_el.text.strip()[:10],
                    "%Y-%m-%d"
                )
            except ValueError:
                pass

        # 作者信息
        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        # arXiv 特有字段：分类
        cat_el = entry.find("arxiv:primary_category", ns)
        primary_cat = cat_el.get("term", "") if cat_el is not None else ""

        # 拼接 content
        content = f"[{primary_cat}] {summary}"
        if author_str:
            content = f"作者: {author_str}\n{content}"

        return self._make_article(
            title=title,
            url=url,
            content=content,
            published_at=published_at
        )
