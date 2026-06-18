# Redis 缓存层

## 位置

`api/models/cache.py`

## 两层缓存用途

```
CacheService
    │
    ├── 用途 1: 数据库查询缓存
    │       /api/home         → 5分钟
    │       /api/reports      → 30分钟
    │       文章详情          → 30分钟
    │
    └── 用途 2: AI 对话缓存
            general (通用知识) → 1天
            chat (闲聊)       → 1小时
            daily (日报)      → 1小时
            article (文章)    → 30分钟
```

## 核心实现：缓存降级

```python
class CacheService:
    def __init__(self):
        try:
            self._redis = Redis.from_url(REDIS_URL)
            self.available = True
        except Exception:
            self.available = False  # ← 自动降级！
            print("[Cache] Redis 不可用，使用降级模式")

    def get(self, key: str) -> Optional[Any]:
        if not self.available:
            return None  # 降级：假装没命中
        try:
            return json.loads(self._redis.get(key))
        except:
            return None

    def set(self, key: str, value: Any, ttl: int):
        if not self.available:
            return
        self._redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))

    def with_cache(self, key, ttl, fetch_func):
        """缓存装饰器模式"""
        cached = self.get(key)
        if cached is not None:
            return cached           # → 命中

        data = fetch_func()         # → 未命中，回源
        self.set(key, data, ttl)
        return data
```

## 差异化 TTL 策略

| 数据类型 | TTL | 原因 |
|---------|-----|------|
| 首页列表 | 5分钟 | 数据变化快 |
| 日报 | 30分钟 | 每天更新即可 |
| 通用知识回答 | 1天 | 答案不会变 |
| 闲聊回答 | 1小时 | 变化小 |
| 日报相关回答 | 1小时 | 日报每天更新 |
| 文章相关回答 | 30分钟 | 可能更新 |

## 面试话术

> "缓存层两个关键设计。第一是缓存降级——Redis 连接失败时自动回退数据库，核心服务不中断。第二是差异化 TTL——不同类型的数据设置不同的过期时间，通用知识缓存 1 天，闲聊缓存 1 小时，避免缓存雪崩的同时最大化命中率。AI 对话缓存是最核心的优化，同一问题第二次零 tokens 消耗。"

## 防缓存雪崩措施

1. **TTL 随机浮动**：300s ± 30s，防止同时过期
2. **降级兜底**：Redis 挂了直接查库
3. **熔断**：Redis 连续报错时自动暂停缓存使用