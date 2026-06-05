"""
Signal - 数据库层单元测试
测试收藏 (bookmarks) 和浏览历史 (history) 相关方法

运行: python -m pytest tests/test_database.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch
import pytest

from api.models.database import DatabaseManager


@pytest.fixture
def db():
    """模拟 DatabaseManager，不连接真实 Supabase"""
    with patch('api.models.database.create_client') as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client

        # 模拟表操作
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        # select().eq().execute() 链式调用
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.range.return_value = mock_select

        # delete().eq().execute()
        mock_delete = MagicMock()
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_delete

        db = DatabaseManager()
        yield db


class TestBookmarks:
    """收藏相关方法测试"""

    def test_add_bookmark(self, db):
        """添加收藏应调用 insert 并返回结果"""
        mock_result = MagicMock()
        mock_result.data = [{"id": "abc-123", "user_id": "user-1", "article_id": "art-1"}]
        db.client.table.return_value.insert.return_value.execute.return_value = mock_result

        result = db.add_bookmark("user-1", "art-1")

        db.client.table.assert_called_with("bookmarks")
        db.client.table().insert.assert_called_once()
        assert result["id"] == "abc-123"

    def test_remove_bookmark(self, db):
        """取消收藏应调用 delete + eq 并返回 True"""
        mock_result = MagicMock()
        mock_result.data = [{"id": "abc-123"}]
        db.client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = db.remove_bookmark("abc-123", "user-1")

        assert result is True

    def test_remove_bookmark_not_found(self, db):
        """取消不存在的收藏应返回 False"""
        mock_result = MagicMock()
        mock_result.data = []
        db.client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result

        result = db.remove_bookmark("nonexistent", "user-1")

        assert result is False

    def test_get_bookmarks_pagination(self, db):
        """获取收藏列表应支持分页"""
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "articles": {"title": "Test"}}]
        mock_result.count = 1
        db.client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        result = db.get_bookmarks("user-1", page=1, page_size=20)

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["page"] == 1
        assert result["pages"] == 1


class TestReadingHistory:
    """浏览历史相关方法测试"""

    def test_add_reading_history_new(self, db):
        """新的浏览记录应成功插入"""
        # 第一次查询：今天没有这条记录
        mock_empty = MagicMock()
        mock_empty.data = []
        # 第二次：插入完成
        mock_insert = MagicMock()
        mock_insert.data = [{"id": "hist-1"}]

        db.client.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.side_effect = [mock_empty, mock_insert]

        result = db.add_reading_history("user-1", "art-1")

        assert result is True

    def test_add_reading_history_duplicate(self, db):
        """同一天同一篇文章不应重复记录"""
        mock_existing = MagicMock()
        mock_existing.data = [{"id": "existing"}]
        db.client.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value = mock_existing

        result = db.add_reading_history("user-1", "art-1")

        assert result is False
        # 不应调用 insert
        db.client.table.return_value.insert.assert_not_called()

    def test_clear_reading_history(self, db):
        """清除历史应调用 delete + eq"""
        mock_result = MagicMock()
        mock_result.data = []
        db.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_result

        result = db.clear_reading_history("user-1")

        assert result is True
        db.client.table.assert_called_with("reading_history")
        db.client.table().delete.assert_called_once()
        db.client.table().delete().eq.assert_called_with("user_id", "user-1")

    def test_get_reading_history(self, db):
        """获取历史应返回分页数据"""
        mock_result = MagicMock()
        mock_result.data = [{"id": "h1", "articles": {"title": "Test"}}]
        mock_result.count = 1
        db.client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        result = db.get_reading_history("user-1", page=1, page_size=20)

        assert result["total"] == 1
        assert len(result["items"]) == 1

    def test_get_reading_history_empty(self, db):
        """无历史时返回空列表"""
        mock_result = MagicMock()
        mock_result.data = []
        mock_result.count = 0
        db.client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_result

        result = db.get_reading_history("user-1")

        assert result["total"] == 0
        assert result["items"] == []
