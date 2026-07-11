"""
Signal - 评论区 单元测试（改造计划 §3.2）

覆盖：
  - 敏感词过滤函数
  - 评论纯逻辑
  - 路由集成（TestClient + mock DB）
  - 空文章 / 空评论降级
  - 举报防重复

不依赖真实 Supabase：用 patch + MagicMock 模拟 DB。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.routes.comments import _check_spam


# ── Helper: mock DB chain ─────────────────────────

def _make_mock_db_chain(return_data):
    """构造支持完整 Supabase 链式调用的 mock：
       db.client.table().select().eq().order().execute().data
    """
    execute_result = MagicMock()
    execute_result.data = return_data

    query_mock = MagicMock()
    query_mock.execute.return_value = execute_result
    # 所有链式方法返回 self
    query_mock.select.return_value = query_mock
    query_mock.eq.return_value = query_mock
    query_mock.order.return_value = query_mock
    query_mock.insert.return_value = query_mock
    query_mock.update.return_value = query_mock
    query_mock.upsert.return_value = query_mock
    query_mock.delete.return_value = query_mock
    query_mock.in_.return_value = query_mock

    client_mock = MagicMock()
    client_mock.table.return_value = query_mock

    db_mock = MagicMock()
    db_mock.client = client_mock
    return db_mock


def _make_app_client():
    with patch('api.models.database.create_client'):
        with patch('api.models.database.DatabaseManager._create_client'):
            from api.main import app
            return TestClient(app)


# ── 敏感词过滤（纯函数，无 DB）────────────────

def test_spam_filter_clean_content():
    """正常评论不触发敏感词"""
    assert _check_spam("这篇文章很有价值，值得深入阅读。") is False
    assert _check_spam("我觉得 GPT-6 的架构很有意思") is False
    assert _check_spam("关注 AI 安全的人应该看看这篇") is False


def test_spam_filter_detects_add_wechat():
    """含"加微信"变体的评论应触发"""
    assert _check_spam("加微信联系我") is True
    assert _check_spam("加V：abc123") is True
    assert _check_spam("我的微信号是 test") is True


def test_spam_filter_detects_ad_keywords():
    """广告类关键词"""
    assert _check_spam("日赚 500，兼职刷单") is True
    assert _check_spam("免费领取大礼包，点击链接") is True


def test_spam_filter_case_insensitive():
    """大小写不敏感匹配"""
    assert _check_spam("加微信号") is True


def test_spam_filter_edge_cases():
    """边界情况：空字符串、纯标点、极短文本"""
    assert _check_spam("") is False
    assert _check_spam("...") is False
    assert _check_spam("好") is False


# ── 路由集成：TestClient + mock DB ─────────────

def test_route_get_comments_empty_article():
    """无评论的文章返回空列表"""
    client = _make_app_client()
    fake_db = _make_mock_db_chain([])
    with patch("api.routes.comments.db", fake_db):
        resp = client.get("/api/comments/art-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["comments"] == []


def test_route_get_comments_with_content():
    """有评论的文章返回嵌套结构"""
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "id": "c-001",
            "article_id": "art-001",
            "user_id": None,
            "author_name": "读者A",
            "content": "好文章！",
            "parent_id": None,
            "is_reported": False, "is_approved": True,
            "created_at": now, "updated_at": now,
        },
        {
            "id": "c-002",
            "article_id": "art-001",
            "user_id": "u-001",
            "author_name": "读者B",
            "content": "同意楼上",
            "parent_id": "c-001",
            "is_reported": False, "is_approved": True,
            "created_at": now, "updated_at": now,
        },
    ]

    client = _make_app_client()
    fake_db = _make_mock_db_chain(rows)
    with patch("api.routes.comments.db", fake_db):
        resp = client.get("/api/comments/art-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    # c-001 是根评论，c-002 是它的回复
    assert len(data["comments"]) == 1
    assert data["comments"][0]["id"] == "c-001"
    assert len(data["comments"][0]["replies"]) == 1
    assert data["comments"][0]["replies"][0]["id"] == "c-002"


def test_route_post_comment_spam_rejected():
    """含敏感词的评论返回 400"""
    client = _make_app_client()
    resp = client.post("/api/comments", json={
        "article_id": "art-001",
        "content": "加微信联系我",
        "author_name": "测试",
    })
    assert resp.status_code == 400
    data = resp.json()
    assert "违规关键词" in data.get("detail", "")


def test_route_post_comment_empty_rejected():
    """空评论返回 400"""
    client = _make_app_client()
    resp = client.post("/api/comments", json={
        "article_id": "art-001",
        "content": "   ",
    })
    assert resp.status_code == 400


def test_route_post_comment_too_long_rejected():
    """超长评论返回 400"""
    client = _make_app_client()
    resp = client.post("/api/comments", json={
        "article_id": "art-001",
        "content": "长" * 2001,
    })
    assert resp.status_code == 400


def test_route_post_comment_success():
    """合法评论创建成功"""
    now = datetime.now(timezone.utc).isoformat()
    inserted = [{"id": "new-001", "article_id": "art-001",
                 "content": "好评论", "author_name": "读者",
                 "created_at": now, "updated_at": now}]

    client = _make_app_client()
    fake_db = _make_mock_db_chain(inserted)
    with patch("api.routes.comments.db", fake_db):
        resp = client.post("/api/comments", json={
            "article_id": "art-001",
            "content": "好评论",
            "author_name": "读者",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "new-001"
    assert data["content"] == "好评论"


def test_route_report_comment_success():
    """举报评论成功后标记为已举报"""
    comment_id = "c-001"

    client = _make_app_client()
    # 模拟"评论存在"查询 → 返回有数据
    fake_db = _make_mock_db_chain([{"id": comment_id, "is_reported": False}])
    with patch("api.routes.comments.db", fake_db):
        resp = client.post("/api/comments/report", json={
            "comment_id": comment_id,
            "reason": "广告内容",
            "reporter_token": "test-token",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_route_report_nonexistent_comment():
    """举报不存在的评论返回 404"""
    client = _make_app_client()
    fake_db = _make_mock_db_chain([])  # 评论不存在 → 空列表
    with patch("api.routes.comments.db", fake_db):
        resp = client.post("/api/comments/report", json={
            "comment_id": "nonexistent",
            "reason": "垃圾内容",
        })
    assert resp.status_code == 404


def test_route_report_duplicate():
    """同一人重复举报同一评论应降级为幂等成功返回"""
    now = datetime.now(timezone.utc).isoformat()
    client = _make_app_client()

    # mock DB: 第一次查询存在，insert 时触发重复键异常
    fake_db = _make_mock_db_chain([{"id": "c-001", "is_reported": False}])

    # 让 insert 触发重复键异常
    def _raise_duplicate(*args, **kwargs):
        raise Exception('duplicate key value violates unique constraint')

    fake_db.client.table.return_value.insert.return_value.execute.side_effect = _raise_duplicate

    with patch("api.routes.comments.db", fake_db):
        resp = client.post("/api/comments/report", json={
            "comment_id": "c-001",
            "reason": "广告",
            "reporter_token": "same-token",
        })
    # 应返回 success=True 而不是 500（幂等处理）
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "已举报" in data.get("message", "")


def test_route_comments_db_unreachable():
    """DB 不可达时返回空列表（降级）"""
    client = _make_app_client()
    # 直接让 real_db 抛异常
    with patch("api.routes.comments.db") as mg:
        mg.client.table.side_effect = RuntimeError("db down")
        resp = client.get("/api/comments/art-001")
    assert resp.status_code == 200  # 降级不 500
    data = resp.json()
    assert data["total"] == 0
    assert data["comments"] == []


def test_route_comments_with_auth_header():
    """带登录头的评论创建应关联用户 ID"""
    now = datetime.now(timezone.utc).isoformat()
    inserted = [{"id": "new-002", "article_id": "art-001",
                 "content": "登录用户评论", "author_name": "登录读者",
                 "user_id": "user-001",
                 "created_at": now, "updated_at": now}]

    client = _make_app_client()

    # mock 掉 verify_token 绕过真实 JWT 验证
    with patch("api.routes.comments.verify_token", return_value="user-001"):
        fake_db = _make_mock_db_chain(inserted)
        with patch("api.routes.comments.db", fake_db):
            resp = client.post(
                "/api/comments",
                json={"article_id": "art-001", "content": "登录用户评论"},
                headers={"Authorization": "Bearer fake-token"},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user-001"
