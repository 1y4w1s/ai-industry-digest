"""GitHub AI Agent 高星项目采集 · 单测（全 mock、零网络、零 Supabase）"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from processor.github_agents import (
    fetch_github_agents,
    _stars_per_day,
    _range_to_since,
)
from scripts.newsletter import NewsletterRenderer


def _item(full_name, stars, created_at, pushed_at=None, description="", language="Python"):
    return {
        "full_name": full_name,
        "html_url": f"https://github.com/{full_name}",
        "stargazers_count": stars,
        "created_at": created_at,
        "pushed_at": pushed_at or created_at,
        "description": description,
        "language": language,
    }


class _FakeResp:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._data


class TestFetchGithubAgents(unittest.TestCase):
    def test_success_parses_and_keeps_star_order(self):
        data = {"items": [
            _item("new/hot", 9000, "2025-01-01T00:00:00Z", description="d2"),
            _item("old/stable", 5000, "2020-01-01T00:00:00Z", description="d1"),
        ]}
        with patch("processor.github_agents.requests.get",
                   return_value=_FakeResp(200, data)) as m:
            res = fetch_github_agents(range="week", min_stars=100, limit=10, use_cache=False)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "new/hot")  # GitHub 返回 stars desc
        self.assertEqual(res[0]["stars"], 9000)
        self.assertEqual(res[0]["description"], "d2")
        self.assertIn("stars_per_day", res[0])
        self.assertIn("is_rising_star", res[0])
        q = m.call_args.kwargs["params"]["q"]
        self.assertIn("stars:>=100", q)
        self.assertIn("agent AI", q)
        self.assertIn("pushed:>=", q)

    def test_rising_flag(self):
        now = datetime.utcnow()
        recent = (now - timedelta(days=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {"items": [
            _item("fresh/rising", 1000, recent),   # spd≈10, age=100 → 新星
            _item("old/slow", 5000, "2015-01-01T00:00:00Z"),  # age 大 → 非新星
        ]}
        with patch("processor.github_agents.requests.get", return_value=_FakeResp(200, data)):
            res = fetch_github_agents(use_cache=False)
        rising = next(r for r in res if r["name"] == "fresh/rising")
        slow = next(r for r in res if r["name"] == "old/slow")
        self.assertTrue(rising["is_rising_star"])
        self.assertFalse(slow["is_rising_star"])
        self.assertAlmostEqual(rising["stars_per_day"], 10.0, places=1)

    def test_trending_sort(self):
        now = datetime.utcnow()
        recent = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {"items": [
            _item("big/old", 90000, "2015-01-01T00:00:00Z"),
            _item("small/new", 3000, recent),   # 日增远高于 big/old
        ]}
        with patch("processor.github_agents.requests.get", return_value=_FakeResp(200, data)):
            res = fetch_github_agents(sort="trending", use_cache=False)
        self.assertEqual(res[0]["name"], "small/new")

    def test_rate_limit_returns_empty(self):
        with patch("processor.github_agents.requests.get", return_value=_FakeResp(403)):
            self.assertEqual(fetch_github_agents(use_cache=False), [])

    def test_network_error_returns_empty(self):
        with patch("processor.github_agents.requests.get", side_effect=Exception("boom")):
            self.assertEqual(fetch_github_agents(use_cache=False), [])

    def test_range_mapping(self):
        today = datetime.utcnow().date()
        for key, days in (("week", 7), ("month", 30), ("quarter", 90)):
            since = datetime.strptime(_range_to_since(key), "%Y-%m-%d").date()
            self.assertEqual((today - since).days, days)
        since_bad = datetime.strptime(_range_to_since("bogus"), "%Y-%m-%d").date()
        self.assertEqual((today - since_bad).days, 7)

    def test_invalid_range_param_falls_back(self):
        data = {"items": [_item("a/b", 100, "2025-01-01T00:00:00Z")]}
        with patch("processor.github_agents.requests.get", return_value=_FakeResp(200, data)) as m:
            fetch_github_agents(range="not-a-range", use_cache=False)
        self.assertIn("pushed:>=", m.call_args.kwargs["params"]["q"])


class TestNewsletterRender(unittest.TestCase):
    def _report(self, items):
        return {
            "summary_insight": "x",
            "main_stories": {"stories": []},
            "main_thread": [],
            "articles": {"high": [], "medium": [], "low": []},
            "github_agents": items,
            "gh_filter": {"range": "week", "min_stars": 100, "sort": "stars"},
        }

    def test_render_includes_section(self):
        from datetime import date
        items = [{
            "name": "o/p", "url": "https://github.com/o/p", "stars": 1234,
            "description": " desc ", "language": "Python",
            "pushed_at": "2025-01-01T00:00:00Z", "created_at": "2025-01-01T00:00:00Z",
            "stars_per_day": 5.0, "is_rising_star": True,
        }]
        html = NewsletterRenderer().render(self._report(items), "https://unsub", date(2026, 7, 12))
        self.assertIn("本周 AI Agent 新星", html)
        self.assertIn("o/p", html)
        self.assertIn("⚡ 新星", html)
        self.assertIn("★ 1,234", html)


if __name__ == "__main__":
    unittest.main()
