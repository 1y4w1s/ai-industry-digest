"""
P2a 社媒一手源采集器测试（全 mock，零网络、零 Supabase）

覆盖：免费源解析 / url 兜底 / 凭证源无 env 安全跳过 / 未知 type 返空 /
SocialCollector 分发 / 无 social 配置返空。
"""
import os
from datetime import datetime
from unittest.mock import patch

from collector.social_collector import (
    SocialCollector,
    fetch_hackernews,
    fetch_github,
    fetch_reddit,
    fetch_credentialed,
    CRED_SOCIAL,
)
from collector.base import Article


def _fake_source(social_type, params=None, name="Test Social"):
    return {
        "name": name,
        "id": "test_social",
        "priority": 1,
        "enabled": True,
        "tier": 1,
        "collectors": [
            {"type": "social", "social_type": social_type, "params": params or {}},
        ],
    }


def test_fetch_hackernews_parses():
    fake = {
        "hits": [
            {
                "title": "New LLM beats SOTA",
                "url": "https://example.com/a",
                "objectID": "1",
                "points": 320,
                "num_comments": 45,
                "created_at_i": 1700000000,
            }
        ]
    }
    with patch("collector.social_collector._http_get_json", return_value=fake):
        raw = fetch_hackernews({"query": "LLM", "max_results": 5})
    assert len(raw) == 1
    r = raw[0]
    assert r["title"] == "New LLM beats SOTA"
    assert r["url"] == "https://example.com/a"
    assert r["engagement"]["platform"] == "hackernews"
    assert r["engagement"]["score"] == 320
    assert r["engagement"]["comments"] == 45
    assert isinstance(r["published_at"], datetime)


def test_fetch_hackernews_url_fallback():
    fake = {
        "hits": [
            {
                "title": "Ask HN",
                "url": None,
                "objectID": "99",
                "points": 10,
                "num_comments": 1,
                "created_at_i": 1700000000,
            }
        ]
    }
    with patch("collector.social_collector._http_get_json", return_value=fake):
        raw = fetch_hackernews({})
    assert raw[0]["url"] == "https://news.ycombinator.com/item?id=99"


def test_fetch_hackernews_no_response():
    with patch("collector.social_collector._http_get_json", return_value=None):
        assert fetch_hackernews({}) == []


def test_fetch_github_parses():
    fake = {
        "items": [
            {
                "full_name": "org/model",
                "html_url": "https://github.com/org/model",
                "description": "a new llm",
                "stargazers_count": 1200,
                "pushed_at": "2026-07-01T10:00:00Z",
            }
        ]
    }
    with patch("collector.social_collector._http_get_json", return_value=fake):
        raw = fetch_github({"topic": "llm", "max_results": 5})
    assert len(raw) == 1
    assert raw[0]["title"] == "[GitHub] org/model"
    assert raw[0]["engagement"]["stars"] == 1200
    assert isinstance(raw[0]["published_at"], datetime)


def test_fetch_github_no_response():
    with patch("collector.social_collector._http_get_json", return_value=None):
        assert fetch_github({}) == []


def test_fetch_reddit_parses():
    fake = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Cool paper",
                        "permalink": "/r/ML/comments/x/",
                        "ups": 88,
                        "created_utc": 1700000000,
                    }
                }
            ]
        }
    }
    with patch("collector.social_collector._http_get_json", return_value=fake):
        raw = fetch_reddit({"subreddit": "MachineLearning", "max_results": 5})
    assert len(raw) == 1
    assert raw[0]["url"] == "https://www.reddit.com/r/ML/comments/x/"
    assert raw[0]["engagement"]["score"] == 88
    assert isinstance(raw[0]["published_at"], datetime)


def test_fetch_reddit_skips_missing_permalink():
    fake = {"data": {"children": [{"data": {"title": "no link", "permalink": ""}}]}}
    with patch("collector.social_collector._http_get_json", return_value=fake):
        assert fetch_reddit({}) == []


def test_fetch_reddit_no_response():
    with patch("collector.social_collector._http_get_json", return_value=None):
        assert fetch_reddit({}) == []


def test_unknown_social_type_returns_empty():
    col = SocialCollector(_fake_source("unknown_xyz"))
    assert col.collect() == []


def test_credentialed_without_env_skips():
    env_keys = [
        "TWITTER_BEARER_TOKEN",
        "YOUTUBE_API_KEY",
        "BILIBILI_COOKIE",
        "XIAOHONGSHU_COOKIE",
    ]
    saved = {k: os.environ.pop(k, None) for k in env_keys}
    try:
        for st in CRED_SOCIAL:
            assert fetch_credentialed(st, {}) == []
    finally:
        for k in env_keys:
            if saved[k] is not None:
                os.environ[k] = saved[k]


def test_social_collector_dispatch_hn():
    fake = {
        "hits": [
            {
                "title": "T",
                "url": "https://e.com",
                "objectID": "1",
                "points": 5,
                "num_comments": 0,
                "created_at_i": 1700000000,
            }
        ]
    }
    with patch("collector.social_collector._http_get_json", return_value=fake):
        col = SocialCollector(_fake_source("hackernews"))
        articles = col.collect()
    assert len(articles) == 1
    assert isinstance(articles[0], Article)
    assert articles[0].engagement["platform"] == "hackernews"
    assert articles[0].source_name == "Test Social"


def test_social_collector_no_social_config():
    src = {"name": "x", "collectors": [{"type": "rss", "url": "u"}]}
    assert SocialCollector(src).collect() == []
