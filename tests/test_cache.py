"""
Signal - 缓存服务测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

# 由于 Redis 可能未安装，使用 mock 测试
class TestCacheService:
    """缓存服务测试"""

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        from api.services.cache import cache_key

        # 简单参数
        key1 = cache_key("articles", 1, 20)
        assert key1 == "articles:1:20"

        # 带 kwargs
        key2 = cache_key("articles", 1, 20, tag="AI", source="arxiv")
        assert key2.startswith("articles:1:20")

        # 长参数会被 hash
        long_value = "a" * 100
        key3 = cache_key("articles", long_value)
        assert len(key3) < 100  # 应该被 hash 缩短

    @patch('api.services.cache.redis')
    def test_cache_get_hit(self, mock_redis):
        """测试缓存命中"""
        from api.services.cache import CacheService

        # 模拟 Redis 返回
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = json.dumps({"test": "data"})
        mock_redis.from_url.return_value = mock_client

        cache = CacheService()
        cache._initialized = False
        cache.__init__()

        result = cache.get("test_key")
        assert result == {"test": "data"}
        assert cache._stats["hits"] == 1

    @patch('api.services.cache.redis')
    def test_cache_get_miss(self, mock_redis):
        """测试缓存未命中"""
        from api.services.cache import CacheService

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_redis.from_url.return_value = mock_client

        cache = CacheService()
        cache._initialized = False
        cache.__init__()

        result = cache.get("missing_key")
        assert result is None
        assert cache._stats["misses"] == 1

    @patch('api.services.cache.redis')
    def test_cache_set(self, mock_redis):
        """测试缓存设置"""
        from api.services.cache import CacheService

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.from_url.return_value = mock_client

        cache = CacheService()
        cache._initialized = False
        cache.__init__()

        success = cache.set("test_key", {"data": "value"}, ttl=300)
        assert success is True
        mock_client.setex.assert_called_once()

    @patch('api.services.cache.redis')
    def test_cache_delete_pattern(self, mock_redis):
        """测试批量删除缓存"""
        from api.services.cache import CacheService

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = ["articles:1", "articles:2"]
        mock_client.delete.return_value = 2
        mock_redis.from_url.return_value = mock_client

        cache = CacheService()
        cache._initialized = False
        cache.__init__()

        deleted = cache.delete_pattern("articles:*")
        assert deleted == 2

    @patch('api.services.cache.redis')
    def test_cache_stats(self, mock_redis):
        """测试缓存统计"""
        from api.services.cache import CacheService

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.info.return_value = {"used_memory_human": "1.2M"}
        mock_client.dbsize.return_value = 100
        mock_redis.from_url.return_value = mock_client

        cache = CacheService()
        cache._initialized = False
        cache.__init__()
        cache._stats = {"hits": 80, "misses": 20, "errors": 0}

        stats = cache.get_stats()
        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["hit_rate"] == 80.0
        assert stats["available"] is True

    def test_cache_unavailable_graceful_degradation(self):
        """测试缓存不可用时的降级"""
        from api.services.cache import CacheService

        # 模拟 Redis 不可用
        with patch('api.services.cache.REDIS_AVAILABLE', False):
            cache = CacheService()
            cache._initialized = False
            cache.__init__()

            # 所有操作应该安全返回
            assert cache.get("key") is None
            assert cache.set("key", "value") is False
            assert cache.delete("key") is False


class TestCacheIntegration:
    """缓存集成测试（与 DatabaseManager）"""

    @patch('api.services.cache.redis')
    def test_get_articles_with_cache(self, mock_redis):
        """测试文章查询使用缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = json.dumps({
            "items": [{"id": 1, "title": "Test"}],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "pages": 1
        })
        mock_redis.from_url.return_value = mock_client

        from api.services.cache import CacheService
        cache = CacheService()
        cache._initialized = False
        cache.__init__()

        # 缓存命中时应该直接返回
        result = cache.get("articles:1:20")
        assert result["items"][0]["title"] == "Test"
