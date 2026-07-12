"""
Signal - GitHub AI Agent 高星项目采集（每日日报「本周 AI Agent 新星」小节数据源）

设计决策（用户 2026-07-12）：
- 内嵌每日日报：每天生成日报（邮件 / 公开页）时实时 fetch GitHub Search API，
  注入 report['github_agents']，双端同源。
- stars_per_day 近似：stars ÷ 仓库存在天数，标识 is_rising_star（新星），
  不需要历史快照持久化（用户明确不要真实增长增量层）。
- 零持久化、零 schema 改动；网络/限流失败一律返回 []，优雅降级。
- 走后端代理 GitHub API（避免前端暴露 token / 触发限流）；可选 GITHUB_TOKEN 提额。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

UA = {"User-Agent": "AI-Industry-Digest/1.0 (+https://1y4w1s.icu)"}
DEFAULT_TIMEOUT = 15
CACHE_TTL = 600  # 进程内缓存 10 分钟，避免重复打 GitHub（限流保护）

_RANGE_DAYS = {"week": 7, "month": 30, "quarter": 90}
RISING_MAX_AGE_DAYS = 365
RISING_MIN_STARS_PER_DAY = 3.0

# 进程内缓存：key -> (timestamp, data)
_cache: Dict[str, tuple] = {}


def _parse_gh_time(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def _range_to_since(range_key: str) -> str:
    days = _RANGE_DAYS.get(range_key, _RANGE_DAYS["week"])
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


def _stars_per_day(stars: int, created_at: Optional[str], now: datetime) -> float:
    c = _parse_gh_time(created_at)
    if not c:
        return 0.0
    age_days = max(1, (now - c).days)
    return round(stars / age_days, 2)


def fetch_github_agents(
    range: str = "week",
    min_stars: int = 100,
    sort: str = "stars",
    limit: int = 30,
    use_cache: bool = True,
) -> List[dict]:
    """从 GitHub 搜索 AI Agent 相关高星仓库。

    返回 list[dict]，字段：name, full_name, url, stars, description, language,
    pushed_at, created_at, stars_per_day, is_rising_star。
    任何失败（网络/限流 403/异常）均返回 []，不抛错、不阻断日报。
    """
    range = range if range in _RANGE_DAYS else "week"
    sort = sort if sort in ("stars", "trending") else "stars"
    cache_key = f"{range}:{min_stars}:{sort}:{limit}"
    now = datetime.utcnow()

    if use_cache and cache_key in _cache:
        ts, data = _cache[cache_key]
        if now.timestamp() - ts < CACHE_TTL:
            return data

    since = _range_to_since(range)
    headers = dict(UA)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    q = f"agent AI in:name,description,readme stars:>={min_stars} pushed:>={since}"
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": q, "sort": "stars", "order": "desc", "per_page": limit},
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code == 403:
            print("  [WARN] GitHub Search API 限流(403)，AI Agent 小节降级为空")
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] GitHub Agent 项目抓取失败（降级为空）: {e}")
        return []

    items = data.get("items", []) or []
    out: List[dict] = []
    for r in items:
        name = r.get("full_name", "")
        url = r.get("html_url", "")
        if not name or not url:
            continue
        stars = r.get("stargazers_count") or 0
        created_at = r.get("created_at") or ""
        spd = _stars_per_day(stars, created_at, now)
        c = _parse_gh_time(created_at)
        age_days = max(1, (now - c).days) if c else 9999
        is_rising = age_days <= RISING_MAX_AGE_DAYS and spd >= RISING_MIN_STARS_PER_DAY
        out.append({
            "name": name,
            "full_name": name,
            "url": url,
            "stars": stars,
            "description": (r.get("description") or "").strip(),
            "language": r.get("language") or "",
            "pushed_at": r.get("pushed_at") or "",
            "created_at": created_at,
            "stars_per_day": spd,
            "is_rising_star": bool(is_rising),
        })

    if sort == "trending":
        out.sort(key=lambda x: x["stars_per_day"], reverse=True)

    if use_cache:
        _cache[cache_key] = (now.timestamp(), out)
    return out
