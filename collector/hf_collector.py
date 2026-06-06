"""
Signal - Hugging Face Daily Papers 采集器
通过 Hugging Face 公开 API 获取每日精选论文
"""

from datetime import datetime
from typing import List, Optional
import requests
import json

from collector.base import BaseCollector, Article


class HFCollector(BaseCollector):
    """Hugging Face Daily Papers 采集器"""

    API_URL = "https://huggingface.co/api/daily_papers"

    def collect(self) -> List[Article]:
        collectors = self.config.get("collectors", [])
        api_config = next((c for c in collectors if c.get("type") == "api"), None)
        if not api_config:
            print(f"  [WARN] {self.name}: 未配置 API 参数")
            return []

        max_results = api_config.get("params", {}).get("max_results", 20)

        print(f"  [FETCH] {self.name}: 正在从 HF API 获取每日论文")
        try:
            resp = requests.get(
                self.API_URL,
                timeout=30,
                headers={"User-Agent": "AI-Industry-Digest/1.0"}
            )
            resp.raise_for_status()
            papers = resp.json()
        except Exception as e:
            print(f"  [ERROR] {self.name}: API 请求失败 - {e}")
            return []

        if not papers:
            print(f"  [EMPTY] {self.name}: 无数据")
            return []

        articles = []
        for paper in papers[:max_results]:
            try:
                article = self._parse_paper(paper)
                if article:
                    articles.append(article)
            except Exception as e:
                print(f"  [WARN] {self.name}: 解析条目失败 - {e}")
                continue

        print(f"  [OK] {self.name}: 采集到 {len(articles)} 篇论文")
        return articles

    def _parse_paper(self, paper: dict) -> Optional[Article]:
        """解析单篇论文"""
        title = paper.get("title", "").strip()
        if not title:
            return None

        # URL
        paper_id = paper.get("id", "")
        url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""

        # 摘要
        summary = paper.get("summary", "").strip()
        # 作者
        authors = paper.get("authors", [])
        author_str = ", ".join([a.get("name", "") for a in authors[:3]])
        if len(authors) > 3:
            author_str += " et al."

        # 拼接内容
        content = f"作者: {author_str}\n{papers}" if author_str else summary

        # 日期
        published_at = None
        pub_date = paper.get("publishedAt", "")
        if pub_date:
            try:
                published_at = datetime.strptime(pub_date[:10], "%Y-%m-%d")
            except ValueError:
                pass

        # 标签
        tags = ["academic", "deep learning"]
        keywords = paper.get("keywords", [])
        if keywords:
            tags.extend(keywords[:3])

        # Votes / 热度
        upvotes = paper.get("ups", 0) or paper.get("upvotes", 0)

        # 重要性：按 upvotes 粗略判断
        importance = "medium"
        if upvotes >= 10:
            importance = "high"
        elif upvotes <= 2:
            importance = "low"

        article = self._make_article(
            title=title,
            url=url,
            content=content,
            published_at=published_at,
        )
        article.tags = tags
        article.importance = importance
        article.importance_reason = f"Hugging Face upvotes: {upvotes}"
        return article
