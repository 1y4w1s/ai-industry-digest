"""
P1 覆盖补齐 — WebSocket / 图片提取 / 缓存 / JWT 验证

覆盖缺口：
  - websocket_manager.py（39% → 95%+）
  - image_extractor.py（48% → 90%+）
  - cache.py（66% → 95%+）
  - jwt_verify.py（76% → 95%+）
"""

import os
import sys
import json
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key-12345")
sys.modules["supabase"] = MagicMock()
sys.modules["supabase._sync"] = MagicMock()
sys.modules["supabase._sync.client"] = MagicMock()
sys.modules["supabase._sync.client.SupabaseException"] = Exception

from api.services.websocket_manager import ConnectionManager, MessageType
from api.services.image_extractor import ImageExtractor
from api.services.cache import CacheService, cache_key, invalidate_cache
from api.services.jwt_verify import verify_token, _get_supabase_client, _decode_jwt_without_verification


# ============================================================
# Part A — WebSocket ConnectionManager
# ============================================================

class TestWebSocketManager:

    def make_ws(self):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        await mgr.connect(ws, "user-1")
        assert mgr.is_connected("user-1")
        ws.accept.assert_awaited_once()
        assert mgr.get_online_count() == 1
        assert mgr._stats["total_connections"] == 1
        assert ws in mgr._last_heartbeat

    @pytest.mark.asyncio
    async def test_connect_multi_session(self):
        mgr = ConnectionManager()
        ws1, ws2 = self.make_ws(), self.make_ws()
        await mgr.connect(ws1, "user-1")
        await mgr.connect(ws2, "user-1")
        assert len(mgr._connections["user-1"]) == 2

    @pytest.mark.asyncio
    async def test_disconnect(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        await mgr.connect(ws, "user-1")
        mgr.disconnect(ws, "user-1")
        assert not mgr.is_connected("user-1")

    @pytest.mark.asyncio
    async def test_disconnect_last_user_removes_entry(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        await mgr.connect(ws, "user-1")
        mgr.disconnect(ws, "user-1")
        assert "user-1" not in mgr._connections
        assert ws not in mgr._last_heartbeat

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        await mgr.connect(ws, "user-1")
        ok = await mgr.send_to_user("user-1", {"type": "test", "data": "hello"})
        assert ok
        ws.send_text.assert_awaited_once()
        assert mgr._stats["messages_sent"] == 1

    @pytest.mark.asyncio
    async def test_send_to_user_no_connection(self):
        mgr = ConnectionManager()
        ok = await mgr.send_to_user("user-1", {"type": "test"})
        assert not ok

    @pytest.mark.asyncio
    async def test_send_to_user_exception_cleans_up(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        ws.send_text.side_effect = Exception("send fail")
        await mgr.connect(ws, "user-1")
        ok = await mgr.send_to_user("user-1", {"type": "test"})
        assert not ok

    @pytest.mark.asyncio
    async def test_broadcast(self):
        mgr = ConnectionManager()
        ws1, ws2 = self.make_ws(), self.make_ws()
        await mgr.connect(ws1, "u1")
        await mgr.connect(ws2, "u2")
        n = await mgr.broadcast({"type": "announce"})
        assert n == 2
        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_empty(self):
        mgr = ConnectionManager()
        n = await mgr.broadcast({"type": "x"})
        assert n == 0

    @pytest.mark.asyncio
    async def test_broadcast_skips_disconnected(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        ws.send_text.side_effect = Exception("gone")
        await mgr.connect(ws, "u1")
        n = await mgr.broadcast({"type": "x"})
        assert n == 0  # disconnected, so 0 sent successfully
        # 连接应该已被清理
        assert not mgr.is_connected("u1")

    def test_update_heartbeat(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        mgr._last_heartbeat[ws] = time.time() - 100
        mgr.update_heartbeat(ws)
        assert mgr._last_heartbeat[ws] > time.time() - 1

    def test_is_connected(self):
        mgr = ConnectionManager()
        ws = self.make_ws()
        assert not mgr.is_connected("user-1")
        mgr._connections["user-1"] = {ws}
        assert mgr.is_connected("user-1")

    def test_get_online_count(self):
        mgr = ConnectionManager()
        mgr._connections["u1"] = {1}
        mgr._connections["u2"] = {2, 3}
        assert mgr.get_online_count() == 2

    def test_get_stats(self):
        mgr = ConnectionManager()
        mgr._connections["u1"] = {1}
        mgr._stats["total_connections"] = 5
        mgr._stats["messages_sent"] = 10
        s = mgr.get_stats()
        assert s["online_users"] == 1
        assert s["total_connections"] == 5
        assert s["messages_sent"] == 10

    def test_message_type_constants(self):
        assert MessageType.BOOKMARK_ADDED == "bookmark_added"
        assert MessageType.PONG == "pong"


# ============================================================
# Part B — ImageExtractor
# ============================================================

class TestImageExtractorPDF:

    def test_pdf_success(self, tmp_path):
        """mock PyMuPDF 覆盖完整 PDF 提取路径"""
        # mock fitz
        fake_fitz = MagicMock()
        fake_page = MagicMock()
        fake_page.get_text.return_value = " 页面内容 "
        fake_page.get_images.return_value = [(0, 1, 2, 3, 4, 5, 6, 7)]

        fake_doc = MagicMock()
        fake_doc.__len__.return_value = 1
        fake_doc.__getitem__.return_value = fake_page
        fake_doc.extract_image.return_value = {"image": b"\x89PNG\r\n\x1a\n", "ext": "png"}
        fake_fitz.open.return_value = fake_doc  # fitz.open() 不是上下文管理器

        ext = ImageExtractor(output_dir=str(tmp_path))
        with patch.dict("sys.modules", {"fitz": fake_fitz}):
            r = ext.extract_from_pdf("dummy.pdf", "doc-1")

        assert len(r) == 1
        assert r[0]["page"] == 1
        assert r[0]["format"] == "png"

    def test_pdf_import_error(self, tmp_path):
        ext = ImageExtractor(output_dir=str(tmp_path))
        r = ext.extract_from_pdf("dummy.pdf", "doc-1")
        assert r == []

    def test_pdf_generic_exception(self, tmp_path):
        fake_fitz = MagicMock()
        fake_fitz.open.side_effect = Exception("corrupt PDF")
        ext = ImageExtractor(output_dir=str(tmp_path))
        with patch.dict("sys.modules", {"fitz": fake_fitz}):
            r = ext.extract_from_pdf("bad.pdf", "doc-1")
        assert r == []


class TestImageExtractorDOCX:

    def make_fake_docx(self):
        """创建模拟的 python-docx Document"""
        import types
        fake_docx = types.ModuleType("docx")
        fake_docx.Document = MagicMock()

        # 构建 mock document
        fake_doc = MagicMock()
        # 空的 rels
        fake_doc.part.rels = {}
        # 一个段落，包含带 drawing 的 run
        fake_run = MagicMock()
        fake_drawing = MagicMock()
        fake_blip = MagicMock()
        fake_blip.get.return_value = "rId1"
        fake_drawing.findall.return_value = [fake_blip]

        # run._element.findall 返回 drawing 元素
        fake_run._element.findall.return_value = [fake_drawing]

        fake_para = MagicMock()
        fake_para.text = "  段落文本  "
        fake_para.runs = [fake_run]
        fake_doc.paragraphs = [fake_para]

        fake_docx.Document.return_value = fake_doc
        return fake_docx, fake_doc

    def test_docx_success(self, tmp_path):
        fake_docx, fake_doc = self.make_fake_docx()
        ext = ImageExtractor(output_dir=str(tmp_path))
        with patch.dict("sys.modules", {"docx": fake_docx, "docx.opc.constants": MagicMock(), "io": MagicMock()}):
            r = ext.extract_from_docx("dummy.docx", "doc-1")
        assert r == []  # 因为没有配置 image rels

    def test_docx_with_image_rels(self, tmp_path):
        """测试 DOCX 包含图片 rel 的情况"""
        import types
        fake_docx = types.ModuleType("docx")
        fake_docx.Document = MagicMock()

        fake_image_part = MagicMock()
        fake_image_part.blob = b"\x89PNG\r\n\x1a\n"

        fake_rel = MagicMock()
        fake_rel.reltype = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        fake_rel.target_part = fake_image_part

        fake_doc = MagicMock()
        fake_doc.part.rels = {"rId1": fake_rel}
        fake_doc.part.related_parts = {"rId1": fake_image_part}

        # 段落：包含 drawing 元素
        fake_blip = MagicMock()
        fake_blip.get.return_value = "rId1"

        fake_drawing = MagicMock()
        fake_drawing.findall.return_value = [fake_blip]

        fake_run = MagicMock()
        fake_run._element.findall.return_value = [fake_drawing]

        fake_para = MagicMock()
        fake_para.text = "图片段落"
        fake_para.runs = [fake_run]
        fake_doc.paragraphs = [fake_para]

        fake_docx.Document.return_value = fake_doc

        ext = ImageExtractor(output_dir=str(tmp_path))
        with patch.dict("sys.modules", {"docx": fake_docx, "docx.opc.constants": MagicMock(), "io": MagicMock()}):
            r = ext.extract_from_docx("img.docx", "doc-1")
        assert len(r) == 1

    def test_docx_import_error(self, tmp_path):
        ext = ImageExtractor(output_dir=str(tmp_path))
        r = ext.extract_from_docx("dummy.docx", "doc-1")
        assert r == []

    def test_docx_exception(self, tmp_path):
        import types
        fake_docx = types.ModuleType("docx")
        fake_docx.Document = MagicMock(side_effect=Exception("corrupt"))
        ext = ImageExtractor(output_dir=str(tmp_path))
        with patch.dict("sys.modules", {"docx": fake_docx, "docx.opc.constants": MagicMock(), "io": MagicMock()}):
            r = ext.extract_from_docx("bad.docx", "doc-1")
        assert r == []

    def test_docx_blip_without_embed(self, tmp_path):
        """blip 没有 embed 属性的情况"""
        import types
        fake_docx = types.ModuleType("docx")
        fake_docx.Document = MagicMock()

        fake_doc = MagicMock()
        fake_doc.part.rels = {}
        fake_doc.part.related_parts = {}

        # blip.get 返回 None（没有 embed 属性）
        fake_blip = MagicMock()
        fake_blip.get.return_value = None

        fake_drawing = MagicMock()
        fake_drawing.findall.return_value = [fake_blip]

        fake_run = MagicMock()
        fake_run._element.findall.return_value = [fake_drawing]

        fake_para = MagicMock()
        fake_para.text = "测试"
        fake_para.runs = [fake_run]
        fake_doc.paragraphs = [fake_para]

        fake_docx.Document.return_value = fake_doc

        ext = ImageExtractor(output_dir=str(tmp_path))
        with patch.dict("sys.modules", {"docx": fake_docx, "docx.opc.constants": MagicMock(), "io": MagicMock()}):
            r = ext.extract_from_docx("nodata.docx", "doc-1")
        assert r == []  # 没有 embed 属性，跳过


# ============================================================
# Part C — CacheService
# ============================================================

class TestCacheService:

    def setup_method(self):
        CacheService._instance = None

    def test_singleton(self):
        c1 = CacheService()
        c2 = CacheService()
        assert c1 is c2

    def test_init_initialized_once(self):
        c = CacheService()
        c._initialized = True  # 跳过重新初始化
        # 第二次 init 应直接返回
        assert c._initialized

    def test_available_property_false_when_no_redis(self):
        c = CacheService()
        c._initialized = True
        c._redis = None
        c._available = False
        assert not c.available

    def test_available_property_true(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._available = True
        assert c.available

    def test_get_when_not_available(self):
        c = CacheService()
        c._initialized = True
        c._redis = None
        c._available = False
        assert c.get("key") is None

    def test_get_hit(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.get.return_value = json.dumps({"val": 42})
        c._available = True
        assert c.get("key") == {"val": 42}
        assert c._stats["hits"] == 1

    def test_get_miss(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.get.return_value = None
        c._available = True
        assert c.get("key") is None
        assert c._stats["misses"] == 1

    def test_get_exception(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.get.side_effect = Exception("err")
        c._available = True
        assert c.get("key") is None
        assert c._stats["errors"] == 1

    def test_set_success(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._available = True
        assert c.set("k", {"a": 1}, ttl=60)
        c._redis.setex.assert_called_once()

    def test_set_not_available(self):
        c = CacheService()
        c._initialized = True
        c._available = False
        assert not c.set("k", "v")

    def test_set_exception(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.setex.side_effect = Exception("err")
        c._available = True
        assert not c.set("k", "v")
        assert c._stats["errors"] == 1

    def test_delete_success(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._available = True
        assert c.delete("k")
        c._redis.delete.assert_called_once_with("k")

    def test_delete_not_available(self):
        c = CacheService()
        c._initialized = True
        c._available = False
        assert not c.delete("k")

    def test_delete_exception(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.delete.side_effect = Exception("err")
        c._available = True
        assert not c.delete("k")
        assert c._stats["errors"] == 1

    def test_delete_pattern_success(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.keys.return_value = ["a", "b"]
        c._redis.delete.return_value = 2
        c._available = True
        assert c.delete_pattern("articles:*") == 2

    def test_delete_pattern_no_keys(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.keys.return_value = []
        c._available = True
        assert c.delete_pattern("articles:*") == 0

    def test_delete_pattern_not_available(self):
        c = CacheService()
        c._initialized = True
        c._available = False
        assert c.delete_pattern("x") == 0

    def test_delete_pattern_exception(self):
        c = CacheService()
        c._initialized = True
        c._redis = MagicMock()
        c._redis.keys.side_effect = Exception("err")
        c._available = True
        assert c.delete_pattern("x") == 0
        assert c._stats["errors"] == 1

    def test_get_stats(self):
        c = CacheService()
        c._initialized = True
        c._stats = {"hits": 80, "misses": 20, "errors": 5}
        c._available = True
        c._redis = MagicMock()
        c._redis.info.return_value = {"used_memory_human": "1.5M"}
        c._redis.dbsize.return_value = 100
        s = c.get_stats()
        assert s["hit_rate"] == 80.0
        assert s["available"]
        assert s["used_memory"] == "1.5M"
        assert s["keys"] == 100

    def test_get_stats_not_available(self):
        c = CacheService()
        c._initialized = True
        c._stats = {"hits": 0, "misses": 0, "errors": 0}
        c._available = False
        s = c.get_stats()
        assert s["hit_rate"] == 0
        assert not s["available"]

    def test_get_stats_info_exception(self):
        c = CacheService()
        c._initialized = True
        c._stats = {"hits": 10, "misses": 0, "errors": 0}
        c._available = True
        c._redis = MagicMock()
        c._redis.info.side_effect = Exception("info err")
        s = c.get_stats()
        assert s["hit_rate"] == 100.0
        # info 异常时不会报错

    def test_reset_stats(self):
        c = CacheService()
        c._initialized = True
        c._stats = {"hits": 10, "misses": 5, "errors": 1}
        c.reset_stats()
        assert c._stats == {"hits": 0, "misses": 0, "errors": 0}


class TestCacheKey:
    """cache_key 工具函数"""

    def test_simple_prefix(self):
        assert cache_key("articles") == "articles"

    def test_with_args(self):
        assert cache_key("articles", "page", 1) == "articles:page:1"

    def test_skip_none_args(self):
        assert cache_key("articles", None, 1) == "articles:1"

    def test_with_kwargs_short(self):
        key = cache_key("articles", page=1, size=20)
        assert "page=1" in key and "size=20" in key

    def test_with_kwargs_long_hashed(self):
        long_val = "x" * 60
        key = cache_key("articles", q=long_val)
        # 长参数会被哈希为 8 字符
        parts = key.split(":")
        assert len(parts) == 2
        assert len(parts[1]) == 8  # md5 前 8 位


class TestCacheDecorator:

    def test_with_cache_hit(self):
        """命中缓存时直接返回"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = "cached-value"
        mock_cache.available = True

        fn = MagicMock()
        from api.services.cache import with_cache, cache
        with patch("api.services.cache.cache", mock_cache):
            wrapped = with_cache("test-key", ttl=60)(fn)
            result = wrapped(1, x=2)
        assert result == "cached-value"
        fn.assert_not_called()

    def test_with_cache_miss(self):
        """未命中时执行原函数并存入缓存"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_cache.available = True

        fn = MagicMock(return_value="fresh")
        from api.services.cache import with_cache
        with patch("api.services.cache.cache", mock_cache):
            wrapped = with_cache("test-key")(fn)
            result = wrapped(42)
        assert result == "fresh"
        mock_cache.set.assert_called_once()

    def test_with_cache_none_result_not_cached(self):
        """原函数返回 None 时不存入缓存"""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_cache.available = True

        fn = MagicMock(return_value=None)
        from api.services.cache import with_cache
        with patch("api.services.cache.cache", mock_cache):
            wrapped = with_cache("test-key")(fn)
            result = wrapped()
        assert result is None
        mock_cache.set.assert_not_called()


class TestInvalidateCache:

    def test_invalidate(self):
        mock_cache = MagicMock()
        mock_cache.delete_pattern.return_value = 2

        with patch("api.services.cache.cache", mock_cache):
            n = invalidate_cache("articles:*")
        assert n == 2


# ============================================================
# Part D — JWT 验证
# ============================================================

class TestJwtVerify:

    def setup_method(self):
        # 清除 supabase 客户端缓存
        from api.services import jwt_verify
        jwt_verify._supabase_client = None

    def test_no_token_returns_none(self):
        assert verify_token("") is None
        assert verify_token(None) is None

    def test_demo_user(self):
        uid = verify_token("demo-user")
        assert uid == "00000000-0000-0000-0000-000000000001"

    def test_bearer_prefix_stripped(self):
        # Bearer 前缀被去掉后，剩余部分如果是 demo-user，应该返回 demo UUID
        uid = verify_token("Bearer demo-user")
        assert uid == "00000000-0000-0000-0000-000000000001"

    def test_supabase_success(self):
        """Supabase get_user 成功返回 user_id"""
        fake_supabase = MagicMock()
        fake_response = MagicMock()
        fake_response.user.id = "supabase-user-id"
        fake_supabase.auth.get_user.return_value = fake_response

        with patch("api.services.jwt_verify._get_supabase_client", return_value=fake_supabase):
            uid = verify_token("valid-jwt-token")
        assert uid == "supabase-user-id"

    def test_supabase_exception_then_fallback(self):
        """Supabase 异常时 fallback 到直接解码"""
        fake_supabase = MagicMock()
        fake_supabase.auth.get_user.side_effect = Exception("Supabase down")

        with patch("api.services.jwt_verify._get_supabase_client", return_value=fake_supabase):
            with patch("api.services.jwt_verify._decode_jwt_without_verification",
                       return_value={"sub": "fallback-user-id"}):
                uid = verify_token("some-token")
        assert uid == "fallback-user-id"

    def test_fallback_no_sub_returns_none(self):
        """Fallback 解码成功但 payload 无 sub"""
        fake_supabase = MagicMock()
        fake_supabase.auth.get_user.side_effect = Exception("err")

        with patch("api.services.jwt_verify._get_supabase_client", return_value=fake_supabase):
            with patch("api.services.jwt_verify._decode_jwt_without_verification",
                       return_value={"other": "data"}):
                uid = verify_token("some-token")
        assert uid is None

    def test_all_fail_returns_none(self):
        """全部验证失败返回 None"""
        fake_supabase = MagicMock()
        fake_supabase.auth.get_user.side_effect = Exception("err")

        with patch("api.services.jwt_verify._get_supabase_client", return_value=fake_supabase):
            with patch("api.services.jwt_verify._decode_jwt_without_verification",
                       return_value=None):
                uid = verify_token("bad-token")
        assert uid is None

    def test_decode_jwt_without_verification_success(self):
        with patch("jwt.decode", return_value={"sub": "decoded-id"}):
            payload = _decode_jwt_without_verification("tok")
        assert payload["sub"] == "decoded-id"

    def test_decode_jwt_without_verification_failure(self):
        with patch("jwt.decode", side_effect=Exception("bad token")):
            assert _decode_jwt_without_verification("bad") is None

    def test_get_supabase_client_creates_client(self):
        with patch("api.services.jwt_verify.create_client") as mc:
            mc.return_value = MagicMock()
            c = _get_supabase_client()
            assert c is not None

    def test_get_supabase_client_cached(self):
        with patch("api.services.jwt_verify.create_client") as mc:
            mc.return_value = "client1"
            c1 = _get_supabase_client()
            c2 = _get_supabase_client()
            assert c1 is c2  # 缓存引用
            mc.assert_called_once()  # 只创建一次
