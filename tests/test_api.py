"""
Signal - API 层单元测试
测试 auth 路由（收藏/历史相关端点）

运行: python -m pytest tests/test_api.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    with patch('api.routes.auth.db') as mock_db:
        with patch('api.routes.auth.get_user_id', return_value="test-user-id"):
            yield TestClient(app)


@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer test-token"}


class TestHistoryAPI:
    """浏览历史 API 测试"""

    def test_add_history(self, client, auth_header):
        """POST /api/auth/history 应记录浏览"""
        with patch('api.routes.auth.db.add_reading_history', return_value=True):
            resp = client.post("/api/auth/history", json={"article_id": "art-1"}, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_add_history_duplicate(self, client, auth_header):
        """重复记录应仍返回 success"""
        with patch('api.routes.auth.db.add_reading_history', return_value=False):
            resp = client.post("/api/auth/history", json={"article_id": "art-1"}, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_list_history(self, client, auth_header):
        """GET /api/auth/history 应返回分页列表"""
        mock_data = {
            "items": [{"id": "h1", "articles": {"title": "Test"}}],
            "total": 1, "page": 1, "page_size": 20, "pages": 1
        }
        with patch('api.routes.auth.db.get_reading_history', return_value=mock_data):
            resp = client.get("/api/auth/history?page=1&page_size=20", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_list_history_empty(self, client, auth_header):
        """无历史时返回空列表"""
        mock_empty = {"items": [], "total": 0, "page": 1, "page_size": 20, "pages": 0}
        with patch('api.routes.auth.db.get_reading_history', return_value=mock_empty):
            resp = client.get("/api/auth/history", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_clear_history(self, client, auth_header):
        """DELETE /api/auth/history 应清除所有历史"""
        with patch('api.routes.auth.db.clear_reading_history', return_value=True):
            resp = client.delete("/api/auth/history", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_history_requires_auth(self, client):
        """未登录应返回 401"""
        resp = client.get("/api/auth/history")
        assert resp.status_code == 401

    def test_clear_history_requires_auth(self, client):
        """未登录不能清除历史"""
        resp = client.delete("/api/auth/history")
        assert resp.status_code == 401


class TestBookmarkAPI:
    """收藏 API 测试"""

    def test_add_bookmark(self, client, auth_header):
        """POST /api/auth/bookmarks 应添加收藏"""
        with patch('api.routes.auth.db.add_bookmark', return_value={"id": "bm-1"}):
            resp = client.post("/api/auth/bookmarks", json={"article_id": "art-1"}, headers=auth_header)
        assert resp.status_code == 200

    def test_remove_bookmark(self, client, auth_header):
        """DELETE /api/auth/bookmarks/{id} 应取消收藏"""
        with patch('api.routes.auth.db.remove_bookmark', return_value=True):
            resp = client.delete("/api/auth/bookmarks/bm-1", headers=auth_header)
        assert resp.status_code == 200

    def test_remove_nonexistent_bookmark(self, client, auth_header):
        """删除不存在的收藏应返回 404"""
        with patch('api.routes.auth.db.remove_bookmark', return_value=False):
            resp = client.delete("/api/auth/bookmarks/nonexistent", headers=auth_header)
        assert resp.status_code == 404

    def test_list_bookmarks(self, client, auth_header):
        """GET /api/auth/bookmarks 应返回分页列表"""
        mock_data = {
            "items": [{"id": "bm-1", "articles": {"title": "Test"}}],
            "total": 1, "page": 1, "page_size": 20, "pages": 1
        }
        with patch('api.routes.auth.db.get_bookmarks', return_value=mock_data):
            resp = client.get("/api/auth/bookmarks", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
