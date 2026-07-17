"""
Signal - 公开页 SEO / 每日简报公开归档页 单元测试（改造计划 §2.3）
仅覆盖纯逻辑（渲染 meta / canonical 绝对 URL / 空输入降级 / sitemap 绝对链接 / robots），
不依赖真实 Supabase；路由集成用 TestClient + monkeypatch 模拟 DB，保持 pytest 绿。

验收映射：
  - 公开页 HTML 含关键 meta 标签（title / description / og:* / JSON-LD）
  - canonical / og:url 为绝对 URL（带 PUBLIC_BASE_URL）
  - 空输入 / DB 不可达降级，不 500
  - sitemap 日期生成绝对链接
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, timezone

from unittest.mock import MagicMock, patch

from scripts.newsletter import _demo_report, NewsletterRenderer
from api.routes.public_digest import (
    PublicDigestRenderer,
    _empty_report,
    DEFAULT_PUBLIC_BASE_URL,
)


# ── 渲染层：真实内容（用 demo 报告，无 DB）─────────────────

def test_public_digest_html_has_seo_meta():
    report = _demo_report(8)
    rd = date(2026, 7, 10)
    html = PublicDigestRenderer(base_url="http://localhost:8000").render(report, rd)

    # 关键 meta 标签齐全
    assert "<title>" in html
    assert 'name="description"' in html
    assert 'property="og:title"' in html
    assert 'property="og:description"' in html
    assert 'property="og:type" content="article"' in html
    assert 'property="og:url"' in html
    assert 'rel="canonical"' in html
    # 结构化数据 JSON-LD
    assert 'application/ld+json' in html
    assert '"@type":"CollectionPage"' in html or '"@type": "CollectionPage"' in html
    assert '"@type":"ItemList"' in html or '"@type": "ItemList"' in html
    # 内容同源：今日主线 + 文章 + so_what
    assert "今日主线" in html
    assert "OpenAI 发布" in html
    assert "So What / 对你意味着什么" in html
    # 公开页不得含退订链接 / 追踪像素（与邮件区分）
    assert "/unsubscribe" not in html
    assert "/track/open" not in html


def test_public_digest_canonical_and_og_url_absolute():
    report = _demo_report(8)
    rd = date(2026, 7, 10)
    base = "http://localhost:8000"
    html = PublicDigestRenderer(base_url=base).render(report, rd)
    canonical = f"{base}/digest/2026-07-10"

    assert f'<link rel="canonical" href="{canonical}">' in html
    assert f'<meta property="og:url" content="{canonical}">' in html
    # 必须是绝对 URL（http://localhost:8000）
    assert canonical.startswith("http://localhost:8000")
    # JSON-LD 内的 url 也是绝对
    assert canonical in html


def test_public_digest_default_base_url_is_8080_domain():
    # 不传 base_url 时应取缺省 http://localhost:8000（带端口）
    r = PublicDigestRenderer()
    assert r.base_url == DEFAULT_PUBLIC_BASE_URL == "http://localhost:8000"


def test_public_digest_base_url_override_via_env(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://signal.example.com")
    r = PublicDigestRenderer()
    assert r.base_url == "https://signal.example.com"
    # 且能拼出正确 canonical
    report = _demo_report(8)
    html = r.render(report, date(2026, 7, 10))
    assert "https://signal.example.com/digest/2026-07-10" in html


# ── 渲染层：空输入 / 降级 ──────────────────────────────

def test_public_digest_empty_report_degrades_friendly():
    # 空 report（DB 不可达 / 无文章）应返回合法 meta 的友好空页，不抛错
    rd = date(2026, 7, 10)
    html = PublicDigestRenderer().render(_empty_report(), rd, degraded=True)

    assert "<title>" in html
    assert 'rel="canonical"' in html
    assert 'name="description"' in html
    # 友好提示（降级横幅 or 暂无内容）
    assert ("暂时无法加载" in html) or ("暂无收录内容" in html)
    # 仍不是 500（这里只是字符串，断言无异常即代表可正常返回）


def test_public_digest_no_articles_still_has_meta():
    report = _demo_report(8)
    report["articles"] = {"high": [], "medium": [], "low": []}
    report["main_stories"] = {"stories": [], "total_stories": 0}
    html = PublicDigestRenderer().render(report, date(2026, 7, 10))
    # 无文章但 meta 合法 + 提示
    assert 'rel="canonical"' in html
    assert "今日暂无收录内容" in html


def test_render_unavailable_for_invalid_date():
    html = PublicDigestRenderer().render_unavailable("2026-13-99")
    assert "<title>" in html
    assert 'rel="canonical"' in html
    assert "日期格式无效" in html
    assert "/digest/2026-13-99" in html


# ── 路由集成：TestClient + 模拟 DB（不连真实 Supabase）───

def _make_app_client():
    """复用 test_api 的 patch 手法，避免模块加载时真正建连。"""
    with patch('api.models.database.create_client'):
        with patch('api.models.database.DatabaseManager._create_client'):
            from api.main import app
            from fastapi.testclient import TestClient
            return TestClient(app)


def test_route_digest_invalid_date_returns_404_meta():
    client = _make_app_client()
    resp = client.get("/digest/2026-13-99")
    assert resp.status_code == 404
    body = resp.text
    assert "<title>" in body
    assert 'rel="canonical"' in body
    assert "日期格式无效" in body


def test_route_digest_db_unreachable_degrades_200():
    client = _make_app_client()
    # DB 不可达：get_db 抛错 → 路由捕获 → 友好空页（200，合法 meta），不 500
    with patch("api.routes.public_digest.get_db", side_effect=RuntimeError("db down")):
        resp = client.get("/digest/2026-07-10")
    assert resp.status_code == 200
    body = resp.text
    assert "<title>" in body
    assert 'rel="canonical"' in body
    assert "http://localhost:8000/digest/2026-07-10" in body
    # 不得泄露异常堆栈
    assert "Traceback" not in body and "RuntimeError" not in body


def test_route_digest_with_content_renders_canonical():
    client = _make_app_client()
    # 模拟 DB 返回 demo 行，使 build_report 跑通真实内容路径
    today = date.today().isoformat()
    rows = [
        {
            "title": "OpenAI 发布 GPT-6，推理成本下降 70%",
            "url": "https://example.com/1", "source_name": "机器之心",
            "summary": "OpenAI 今日发布 GPT-6。", "tags": ["大模型", "OpenAI"],
            "importance": "high", "importance_reason": "行业重磅",
            "so_what": "对中小团队意味着 API 成本大幅下降。",
            "published_at": f"{today}T09:00:00+00:00",
        },
        {
            "title": "Hugging Face 上线本地推理网关",
            "url": "https://example.com/2", "source_name": "Hugging Face",
            "summary": "HF 推出本地推理网关。", "tags": ["开源"],
            "importance": "medium", "importance_reason": "工程利好",
            "so_what": "数据合规团队可绕开公有云。",
            "published_at": f"{today}T10:00:00+00:00",
        },
    ]
    fake_db = MagicMock()
    fake_db.get_articles.return_value = {"items": rows}
    fake_db.get_report_dates.return_value = [today]

    with patch("api.routes.public_digest.get_db", return_value=fake_db):
        resp = client.get(f"/digest/{today}")
    assert resp.status_code == 200
    body = resp.text
    # 内容 + canonical + 同源 so_what
    assert "OpenAI 发布" in body
    assert "So What / 对你意味着什么" in body
    assert f"http://localhost:8000/digest/{today}" in body
    assert "/unsubscribe" not in body and "/track/open" not in body


def test_route_sitemap_absolute_links():
    client = _make_app_client()
    with patch("api.routes.public_digest.get_db") as mg:
        fake_db = MagicMock()
        fake_db.get_report_dates.return_value = ["2026-07-10", "2026-07-09", "2026-07-08"]
        mg.return_value = fake_db
        resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")
    body = resp.text
    assert "<urlset" in body
    assert "http://localhost:8000/digest/2026-07-10" in body
    assert "http://localhost:8000/digest/2026-07-09" in body
    # 每个 <loc> 都是绝对 URL
    assert body.count("<loc>http://") == 3


def test_route_sitemap_db_unreachable_empty():
    client = _make_app_client()
    with patch("api.routes.public_digest.get_db", side_effect=RuntimeError("db down")):
        resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "<urlset" in resp.text
    # 合法空 sitemap，不 500
    assert "Traceback" not in resp.text


def test_route_robots_points_to_sitemap():
    client = _make_app_client()
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    body = resp.text
    assert "User-agent: *" in body
    assert "Allow: /" in body
    assert "Sitemap: http://localhost:8000/sitemap.xml" in body


# ── P1a-2 · OG SVG 分享卡片 ──────────────────────────────

def test_route_og_svg_returns_valid_svg():
    client = _make_app_client()
    resp = client.get("/og/digest/2026-07-10.svg")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    body = resp.text
    assert body.startswith("<?xml")
    assert '<svg' in body
    assert 'viewBox="0 0 1200 630"' in body
    # 品牌元素
    assert "Signal" in body
    assert "EDITORIAL" in body
    # 日期注入
    assert "2026" in body


def test_route_og_svg_invalid_date_returns_placeholder():
    client = _make_app_client()
    resp = client.get("/og/digest/not-a-date.svg")
    assert resp.status_code == 200  # 优雅降级，不是 500
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert "暂无主线数据" in resp.text


def test_route_og_svg_db_down_degrades():
    client = _make_app_client()
    with patch("api.routes.public_digest.get_db", side_effect=RuntimeError("db down")):
        resp = client.get("/og/digest/2026-07-10.svg")
    assert resp.status_code == 200
    body = resp.text
    # 降级但仍是合法 SVG
    assert "<svg" in body
    # 不泄露堆栈
    assert "Traceback" not in body


def test_route_og_svg_escapes_user_content():
    """XSS 防护：标题含 HTML 时必须 escape"""
    client = _make_app_client()
    # 注入恶意 main_thread 标题
    fake_report = {
        "date": date(2026, 7, 10),
        "main_thread": [
            {"title": "<script>alert(1)</script>", "entity": "BAD"},
        ],
    }
    with patch("api.routes.public_digest.build_report", return_value=fake_report):
        resp = client.get("/og/digest/2026-07-10.svg")
    assert resp.status_code == 200
    body = resp.text
    # script 标签必须被 escape
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_route_digest_html_includes_og_image_meta():
    """digest HTML 必须注入 og:image / twitter:card meta，引用 /og/digest/{date}.svg"""
    client = _make_app_client()
    resp = client.get("/digest/2026-07-10")
    assert resp.status_code == 200
    body = resp.text
    assert 'property="og:image"' in body
    assert "/og/digest/2026-07-10.svg" in body
    assert 'name="twitter:card"' in body
    assert 'content="summary_large_image"' in body


def test_route_digest_github_agents_section_and_filter():
    """公开页应渲染「今日 GitHub 推荐」卡片 + 时间范围/最低 star/排序筛选器。"""
    client = _make_app_client()
    today = date.today().isoformat()
    items = [{
        "name": "o/p", "url": "https://github.com/o/p", "stars": 1234,
        "description": "d", "language": "Python",
        "pushed_at": "2025-01-01T00:00:00Z", "created_at": "2025-01-01T00:00:00Z",
        "stars_per_day": 5.0, "is_rising_star": False,
    }]
    fake_report = _demo_report(8)
    fake_report["github_agents"] = items
    fake_report["gh_filter"] = {"range": "week", "min_stars": 100, "sort": "stars"}
    with patch("api.routes.public_digest.build_report", return_value=fake_report):
        resp = client.get(f"/digest/{today}")
    assert resp.status_code == 200
    body = resp.text
    assert "今日 GitHub 推荐" in body
    assert 'name="gh_range"' in body
    assert 'name="gh_min_stars"' in body
    assert 'name="gh_sort"' in body
    assert f'action="/digest/{today}"' in body


def test_route_digest_github_filter_changes_query():
    """公开页筛选器应把 gh_range/gh_min_stars/gh_sort 透传到 build_report(gh_params)。"""
    client = _make_app_client()
    today = date.today().isoformat()
    captured = {}

    def spy(db, report_date, top_n=8, window_days=3, gh_params=None):
        captured["gh_params"] = gh_params
        return _demo_report(8)

    with patch("api.routes.public_digest.build_report", side_effect=spy):
        resp = client.get(
            f"/digest/{today}?gh_range=month&gh_min_stars=500&gh_sort=trending"
        )
    assert resp.status_code == 200
    assert captured.get("gh_params") == {
        "range": "month", "min_stars": 500, "sort": "trending", "limit": 30
    }
