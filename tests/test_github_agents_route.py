"""
P3-home · /api/github-agents 路由单测

用独立 FastAPI + TestClient 仅挂载该 router（不加载整个 app，避免 Supabase 等重依赖）。
mock processor.github_agents.fetch_github_agents，覆盖：成功返回 / 参数透传 / 异常降级返回空 + 200。
零网络、零 Supabase。
"""
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.github_agents import router


def _make_app():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


def _sample_items():
    return [
        {
            "name": "agentic",
            "full_name": "openai/agentic",
            "url": "https://github.com/openai/agentic",
            "stars": 12000,
            "description": "Build agentic workflows",
            "language": "Python",
            "pushed_at": "2026-07-10T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
            "stars_per_day": 30.0,
            "is_rising_star": True,
        },
        {
            "name": "autogpt",
            "full_name": "significant/autogpt",
            "url": "https://github.com/significant/autogpt",
            "stars": 90000,
            "description": "An open-source AI agent",
            "language": "Python",
            "pushed_at": "2026-07-11T00:00:00Z",
            "created_at": "2023-01-01T00:00:00Z",
            "stars_per_day": 80.0,
            "is_rising_star": False,
        },
    ]


def test_github_agents_success():
    with patch("api.routes.github_agents.fetch_github_agents", return_value=_sample_items()):
        client = TestClient(_make_app())
        r = client.get("/api/github-agents")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 2
        assert len(body["items"]) == 2
        assert body["range"] == "week"
        assert body["min_stars"] == 100
        assert body["sort"] == "stars"
        assert body["items"][0]["full_name"] == "openai/agentic"


def test_github_agents_param_passthrough():
    captured = {}

    def fake_fetch(range="week", min_stars=100, sort="stars", limit=30, use_cache=True):
        captured.update(range=range, min_stars=min_stars, sort=sort, limit=limit)
        return []

    with patch("api.routes.github_agents.fetch_github_agents", side_effect=fake_fetch):
        client = TestClient(_make_app())
        r = client.get("/api/github-agents?range=month&min_stars=200&sort=trending&limit=5")
        assert r.status_code == 200
        assert captured == {"range": "month", "min_stars": 200, "sort": "trending", "limit": 5}
        assert r.json()["count"] == 0


def test_github_agents_fetch_exception_degrades_empty():
    with patch(
        "api.routes.github_agents.fetch_github_agents",
        side_effect=Exception("network down"),
    ):
        client = TestClient(_make_app())
        r = client.get("/api/github-agents")
        assert r.status_code == 200  # 不 500
        body = r.json()
        assert body["items"] == []
        assert body["count"] == 0
        assert body["error"] == "fetch_failed"


def test_github_agents_empty_items_ok():
    with patch("api.routes.github_agents.fetch_github_agents", return_value=[]):
        client = TestClient(_make_app())
        r = client.get("/api/github-agents")
        assert r.status_code == 200
        assert r.json()["count"] == 0
