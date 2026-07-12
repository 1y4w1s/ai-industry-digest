"""
Signal - 社媒一手源采集器（一级热源）

设计原则（见 docs/改造计划.md §1.1）：
- 社媒 = 一级热源：快、带话题、带热度信号，与 arXiv/RSS（二级沉淀）互补。
- 可插拔适配器：先接「免费、无登录」源（Hacker News / GitHub / Reddit），
  凭证类源（X / YouTube / B站 / 小红书）留作凭证就绪后的可插拔桩——
  默认无凭证即返回 []，绝不尝试登录，规避封号风险。

所有 fetch 均带 timeout + 异常降级，失败时返回 []（不抛错、不阻断主流程）。
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from collector.base import BaseCollector, Article

# 免费、无登录的一级热源
FREE_SOCIAL = {"hackernews", "github", "reddit"}
# 凭证类源（需 Cookie / API key，无凭证时安全跳过）
CRED_SOCIAL = {"twitter", "youtube", "bilibili", "xiaohongshu"}

DEFAULT_TIMEOUT = 15
UA = {"User-Agent": "AI-Industry-Digest/1.0 (+https://1y4w1s.icu)"}


def _http_get_json(url: str, params=None, timeout=DEFAULT_TIMEOUT, headers=None):
    """带超时与降级的 JSON GET；失败返回 None（不抛错）。"""
    try:
        resp = requests.get(
            url, params=params, timeout=timeout, headers=headers or UA
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:  # noqa: BLE001 - 降级：任何异常都返回 None
        print(f"  [WARN] social fetch failed ({url}): {e}")
        return None


def _parse_iso(s: Optional[str]) -> datetime:
    if not s:
        return datetime.utcnow()
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:  # noqa: BLE001
        return datetime.utcnow()


# ---------------- 免费适配器（一级热源） ----------------

def fetch_hackernews(params: dict) -> List[dict]:
    """Hacker News Algolia API：免费、无 key、自带 points/comments 热度信号。"""
    query = params.get("query", "AI OR LLM OR machine learning")
    n = int(params.get("max_results", 20))
    data = _http_get_json(
        "https://hn.algolia.com/api/v1/search",
        params={"tags": "story", "query": query, "hitsPerPage": n},
    )
    if not data:
        return []
    out = []
    for h in data.get("hits", []):
        title = h.get("title")
        if not title:
            continue
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        ts = h.get("created_at_i")
        published = datetime.utcfromtimestamp(ts) if ts else datetime.utcnow()
        engagement = {
            "platform": "hackernews",
            "score": h.get("points") or 0,
            "comments": h.get("num_comments") or 0,
        }
        out.append(
            {
                "title": title,
                "url": url,
                "content": h.get("story_text") or title,
                "published_at": published,
                "engagement": engagement,
            }
        )
    return out


def fetch_github(params: dict) -> List[dict]:
    """GitHub 仓库搜索 API：免费；可选 GITHUB_TOKEN 提升限流。"""
    topic = params.get("topic", "llm")
    n = int(params.get("max_results", 15))
    since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    headers = dict(UA)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = _http_get_json(
        "https://api.github.com/search/repositories",
        params={
            "q": f"topic:{topic} pushed:>{since}",
            "sort": "updated",
            "order": "desc",
            "per_page": n,
        },
        headers=headers,
    )
    if not data:
        return []
    out = []
    for r in data.get("items", []):
        name = r.get("full_name", "")
        url = r.get("html_url", "")
        if not name or not url:
            continue
        engagement = {"platform": "github", "stars": r.get("stargazers_count") or 0}
        out.append(
            {
                "title": f"[GitHub] {name}",
                "url": url,
                "content": r.get("description") or "",
                "published_at": _parse_iso(r.get("pushed_at")),
                "engagement": engagement,
            }
        )
    return out


def fetch_reddit(params: dict) -> List[dict]:
    """Reddit hot 列表 JSON：免费；需带描述性 UA 避免被拦。"""
    sub = params.get("subreddit", "MachineLearning")
    n = int(params.get("max_results", 15))
    data = _http_get_json(
        f"https://www.reddit.com/r/{sub}/hot.json",
        params={"limit": n},
        headers={"User-Agent": "AI-Industry-Digest/1.0 by (research digest)"},
    )
    if not data:
        return []
    out = []
    for c in data.get("data", {}).get("children", []):
        d = c.get("data", {})
        title = d.get("title")
        permalink = d.get("permalink", "")
        if not title or not permalink:
            continue
        ts = d.get("created_utc")
        published = datetime.utcfromtimestamp(ts) if ts else datetime.utcnow()
        engagement = {"platform": "reddit", "score": d.get("ups") or 0}
        out.append(
            {
                "title": title,
                "url": f"https://www.reddit.com{permalink}",
                "content": d.get("selftext") or title,
                "published_at": published,
                "engagement": engagement,
            }
        )
    return out


# ---------------- 凭证类桩（无凭证即安全跳过） ----------------

def fetch_credentialed(social_type: str, params: dict) -> List[dict]:
    """凭证类源：仅当对应环境变量就绪才尝试（当前未实现 Agent-Reach 登录），
    无凭证直接返回 []，绝不尝试登录，规避封号风险。"""
    env_map = {
        "twitter": "TWITTER_BEARER_TOKEN",
        "youtube": "YOUTUBE_API_KEY",
        "bilibili": "BILIBILI_COOKIE",
        "xiaohongshu": "XIAOHONGSHU_COOKIE",
    }
    env_key = env_map.get(social_type)
    if not env_key or not os.environ.get(env_key):
        print(f"  [SKIP] social_type={social_type}: 未配置 {env_key or '凭证'}，安全跳过")
        return []
    # 凭证就绪时的实现入口（经 Agent-Reach / opencli 只读抓取），本期未实现。
    print(f"  [WARN] social_type={social_type}: 凭证已配置，但 Agent-Reach 读取逻辑待实现")
    return []


class SocialCollector(BaseCollector):
    """社媒一手源采集器：按 social_type 分发到对应适配器。"""

    def collect(self) -> List[Article]:
        collectors = self.config.get("collectors", [])
        social_cfg = next((c for c in collectors if c.get("type") == "social"), None)
        if not social_cfg:
            print(f"  [WARN] {self.name}: 未配置 social 参数")
            return []

        social_type = social_cfg.get("social_type")
        params = social_cfg.get("params", {}) or {}

        if social_type in FREE_SOCIAL:
            fetcher = {
                "hackernews": fetch_hackernews,
                "github": fetch_github,
                "reddit": fetch_reddit,
            }[social_type]
            raw = fetcher(params)
        elif social_type in CRED_SOCIAL:
            raw = fetch_credentialed(social_type, params)
        else:
            print(f"  [WARN] {self.name}: 未知 social_type={social_type}")
            return []

        articles: List[Article] = []
        for r in raw:
            a = self._make_article(
                r["title"], r["url"], r.get("content") or r["title"], r.get("published_at")
            )
            if r.get("engagement"):
                a.engagement = r["engagement"]
            articles.append(a)
        print(f"  [FETCH] {self.name}: 社媒源 {social_type} 采集 {len(articles)} 篇")
        return articles
