"""
Signal - Redis 缓存服务
提供缓存层，减少数据库查询压力
"""

import os
import json
import hashlib
import time
from typing import Optional, Any, Dict, Callable
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("[Cache] redis 库未安装，缓存功能将降级")

from dotenv import load_dotenv

load_dotenv()


class CacheService:
    """Redis 缓存服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._redis = None
        self._available = False
        self._stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
        }

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        if not REDIS_AVAILABLE:
            print(f"[Cache] Redis 库不可用，缓存已禁用")
            return

        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            self._redis.ping()
            self._available = True
            print(f"[Cache] Redis 连接成功: {redis_url}")
        except Exception as e:
            print(f"[Cache] Redis 连接失败: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        """缓存是否可用"""
        return self._available and self._redis is not None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.available:
            return None

        try:
            value = self._redis.get(key)
            if value is not None:
                self._stats["hits"] += 1
                return json.loads(value)
            self._stats["misses"] += 1
            return None
        except Exception as e:
            self._stats["errors"] += 1
            print(f"[Cache] 获取缓存失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值（会被 JSON 序列化）
            ttl: 过期时间（秒），默认 5 分钟
        """
        if not self.available:
            return False

        try:
            self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            self._stats["errors"] += 1
            print(f"[Cache] 设置缓存失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.available:
            return False

        try:
            self._redis.delete(key)
            return True
        except Exception as e:
            self._stats["errors"] += 1
            print(f"[Cache] 删除缓存失败: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有缓存

        Args:
            pattern: 匹配模式，如 "articles:*"

        Returns:
            删除的键数量
        """
        if not self.available:
            return 0

        try:
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except Exception as e:
            self._stats["errors"] += 1
            print(f"[Cache] 批量删除缓存失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0

        result = {
            "available": self.available,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "errors": self._stats["errors"],
            "hit_rate": round(hit_rate, 2),
        }

        if self.available:
            try:
                info = self._redis.info("memory")
                result["used_memory"] = info.get("used_memory_human", "N/A")
                result["keys"] = self._redis.dbsize()
            except Exception:
                pass

        return result

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {"hits": 0, "misses": 0, "errors": 0}


# 全局缓存实例
cache = CacheService()


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键

    Args:
        prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        格式化的缓存键，如 "articles:page:1:abc123"
    """
    # 将参数序列化为字符串
    key_parts = [prefix]
    
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))
    
    # 对 kwargs 进行排序并序列化
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = "&".join(f"{k}={v}" for k, v in sorted_kwargs if v is not None)
        if kwargs_str:
            # 对较长的参数进行 hash
            if len(kwargs_str) > 50:
                kwargs_str = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
            key_parts.append(kwargs_str)

    return ":".join(key_parts)


def with_cache(key_prefix: str, ttl: int = 300):
    """缓存装饰器

    用法:
        @with_cache("articles", ttl=300)
        def get_articles(page, page_size):
            return db.query(...)

    Args:
        key_prefix: 缓存键前缀
        ttl: 缓存过期时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache_key(key_prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached = cache.get(key)
            if cached is not None:
                return cached

            # 执行原函数
            result = func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                cache.set(key, result, ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """使缓存失效

    Args:
        pattern: 缓存键模式，如 "articles:*"

    Returns:
        删除的键数量
    """
    return cache.delete_pattern(pattern)
