"""
F-11 单元测试：文档增量更新（DocumentTracker）

测试策略：
  - 纯函数测试：compute_hash 一致性、空内容、确定性
  - 数据结构测试：detect_change 返回格式
  - 边界测试：空文档、大文档、同内容重复上传

注：_sync_process_document 和 reupload_document 涉及数据库操作，
    只在集成测试中验证。单元测试仅覆盖 DocumentTracker 的纯逻辑。
"""

import hashlib
import pytest
from unittest.mock import MagicMock, patch
from api.services.document_tracker import DocumentTracker


@pytest.fixture
def tracker():
    return DocumentTracker()


class TestComputeHash:
    """compute_hash 纯函数测试"""

    def test_hash_consistency(self, tracker):
        """相同内容应产生相同哈希"""
        h1 = tracker.compute_hash("Hello World")
        h2 = tracker.compute_hash("Hello World")
        assert h1 == h2

    def test_hash_deterministic(self, tracker):
        """多次调用结果一致"""
        results = [tracker.compute_hash("test content") for _ in range(5)]
        assert len(set(results)) == 1

    def test_different_content_different_hash(self, tracker):
        """不同内容产生不同哈希"""
        h1 = tracker.compute_hash("content A")
        h2 = tracker.compute_hash("content B")
        assert h1 != h2

    def test_empty_string(self, tracker):
        """空字符串也产生合法 MD5"""
        h = tracker.compute_hash("")
        assert len(h) == 32  # MD5 是 32 位十六进制

    def test_unicode_content(self, tracker):
        """Unicode 内容正常处理"""
        h = tracker.compute_hash("人工智能（AI）🚀")
        assert len(h) == 32

    def test_hash_algorithm_md5(self, tracker):
        """验证使用 MD5 算法"""
        h = tracker.compute_hash("test")
        expected = hashlib.md5("test".encode("utf-8")).hexdigest()
        assert h == expected

    def test_long_content(self, tracker):
        """超长内容哈希性能稳定"""
        content = "a" * 100000
        h = tracker.compute_hash(content)
        assert len(h) == 32

    def test_binary_safe(self, tracker):
        """特殊字符安全"""
        content = "\x00\x01\x02\n\t\r\\"
        h = tracker.compute_hash(content)
        assert len(h) == 32


class TestDetectChange:
    """detect_change 逻辑测试（mock 数据库）"""

    def test_detect_change_document_not_found(self, tracker):
        """文档不存在时返回 changed=True"""
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            result = tracker.detect_change("non-existent-id", "new content")
            assert result["changed"] is True
            assert result["skip_reason"] == "document_not_found"

    def test_detect_change_unchanged(self, tracker):
        """内容无变更时返回 changed=False"""
        content = "same content"
        h = tracker.compute_hash(content)
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"content_hash": h, "version": 1}
            ]
            
            result = tracker.detect_change("doc-1", content)
            assert result["changed"] is False
            assert "无变更" in result["skip_reason"]
            assert result["current_version"] == 1
            assert result["old_hash"] == h
            assert result["new_hash"] == h

    def test_detect_change_changed(self, tracker):
        """内容变更时返回 changed=True"""
        old_content = "old content"
        new_content = "new content"
        old_h = tracker.compute_hash(old_content)
        new_h = tracker.compute_hash(new_content)
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"content_hash": old_h, "version": 2}
            ]
            
            result = tracker.detect_change("doc-1", new_content)
            assert result["changed"] is True
            assert result["old_hash"] == old_h
            assert result["new_hash"] == new_h

    def test_detect_change_first_time(self, tracker):
        """首次处理（content_hash 为空）应视为变更"""
        content = "new content"
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"content_hash": "", "version": 0}
            ]
            
            result = tracker.detect_change("doc-1", content)
            assert result["changed"] is True

    def test_detect_change_null_hash(self, tracker):
        """content_hash 为 None 时视为变更"""
        content = "some content"
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"content_hash": None, "version": 0}
            ]
            
            result = tracker.detect_change("doc-1", content)
            assert result["changed"] is True

    def test_detect_change_same_hash_different_version(self, tracker):
        """相同哈希不同版本 → 内容未变更"""
        h = tracker.compute_hash("stable content")
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"content_hash": h, "version": 5}
            ]
            
            result = tracker.detect_change("doc-1", "stable content")
            assert result["changed"] is False


class TestBumpVersion:
    """bump_version 逻辑测试（mock 数据库）"""

    def test_bump_version_increments(self, tracker):
        """版本号应递增"""
        content = "test content"
        h = tracker.compute_hash(content)
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"version": 3}
            ]
            
            new_version = tracker.bump_version("doc-1", content)
            
            assert new_version == 4
            update_call = mock_db.client.table.return_value.update
            update_call.assert_called_once()
            update_kwargs = update_call.call_args[0][0]
            assert update_kwargs["version"] == 4
            assert update_kwargs["content_hash"] == h

    def test_bump_version_from_zero(self, tracker):
        """从未处理过的文档（version=0）第一次递增到 1"""
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"version": 0}
            ]
            
            new_version = tracker.bump_version("doc-1", "content")
            assert new_version == 1

    def test_bump_version_no_existing_version(self, tracker):
        """没有 version 字段时视为 0，递增到 1"""
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {}
            ]
            
            new_version = tracker.bump_version("doc-1", "content")
            assert new_version == 1


class TestInitDocument:
    """init_document 逻辑测试"""

    def test_init_sets_version_one(self, tracker):
        """初始化时版本号应为 1"""
        content = "new document"
        h = tracker.compute_hash(content)
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            result = tracker.init_document("new-doc", content)
            
            assert result is True
            update_call = mock_db.client.table.return_value.update
            update_call.assert_called_once()
            kwargs = update_call.call_args[0][0]
            assert kwargs["version"] == 1
            assert kwargs["content_hash"] == h

    def test_init_empty_content(self, tracker):
        """空内容也能初始化"""
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            result = tracker.init_document("doc-empty", "")
            assert result is True


class TestEdgeCases:
    """边界情况测试"""

    def test_md5_format(self, tracker):
        """MD5 应为 32 位小写十六进制"""
        h = tracker.compute_hash("test")
        assert len(h) == 32
        assert h == h.lower()
        assert all(c in "0123456789abcdef" for c in h)

    def test_detect_change_result_format(self, tracker):
        """detect_change 返回格式检查"""
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"content_hash": "abc", "version": 1}
            ]
            
            result = tracker.detect_change("doc-1", "test")
            required_keys = {"changed", "old_hash", "new_hash", "current_version", "skip_reason"}
            assert set(result.keys()) == required_keys

    def test_bump_version_updates_hash(self, tracker):
        """bump_version 应更新哈希到最新内容"""
        old_content = "old"
        new_content = "new content with significant changes"
        new_h = tracker.compute_hash(new_content)
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"version": 2}
            ]
            
            tracker.bump_version("doc-1", new_content)
            update_kwargs = mock_db.client.table.return_value.update.call_args[0][0]
            assert update_kwargs["content_hash"] == new_h
            assert update_kwargs["content_hash"] != tracker.compute_hash(old_content)

    def test_get_document_info_not_found(self, tracker):
        """不存在的文档返回 None"""
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            info = tracker.get_document_info("nonexistent")
            assert info is None

    def test_get_document_info_found(self, tracker):
        """存在的文档返回信息"""
        doc_data = {"id": "doc-1", "name": "test.md", "version": 3, "content_hash": "abc123", "status": "completed", "chunks_count": 10}
        
        with patch("api.services.document_tracker.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [doc_data]
            
            info = tracker.get_document_info("doc-1")
            assert info["id"] == "doc-1"
            assert info["version"] == 3
