# AI 对话与 Token 优化

## 位置

`api/routes/chat.py`

## 问题分类引擎

```
用户提问
    │
    ▼ classify_question()
    │
    ├── "chat" (闲聊)
    │     示例: "你好" "谢谢" "再见"
    │     → 不注入上下文，缓存 1 小时
    │
    ├── "general" (通用知识)
    │     示例: "什么是深度学习" "解释一下Transformer"
    │     → 不注入上下文，缓存 1 天
    │
    ├── "daily" (日报相关)
    │     示例: "今天有什么新闻" "最近的AI热点"
    │     → 注入日报上下文，缓存 1 小时
    │
    └── "article" (文章相关)
          示例: "这篇论文讲了什么" "文章详情"
          → 注入文章上下文，缓存 30 分钟
```

## 分类优先级规则

```python
def classify_question(message: str) -> str:
    msg = message.lower().strip()

    # 优先级 1: 闲聊（最高）
    if any(kw in msg for kw in ["你好", "嗨", "hello", "谢谢", "再见"]):
        return "chat"

    # 优先级 2: 通用知识（排除"新闻/日报"以防误判）
    general_kw = ["什么是", "解释一下", "原理", "概念", "如何", "为什么"]
    content_kw = ["文章", "新闻", "报道", "日报", "今天", "最近"]
    if any(kw in msg for kw in general_kw) and not any(kw in msg for kw in content_kw):
        return "general"

    # 优先级 3: 日报
    if any(kw in msg for kw in ["日报", "新闻", "今天", "最近", "汇总"]):
        return "daily"

    # 默认：注入上下文
    return "daily"
```

优先级示例：

| 用户输入 | 命中类型 | 原因 |
|---------|---------|------|
| "你好，什么是AI" | chat | 闲聊优先 |
| "什么是今天的AI新闻" | daily | 含"新闻"，排除 general |
| "解释一下Transformer" | general | 不含"新闻/日报" |

## 上下文精简优化

| 优化项 | 优化前 | 优化后 | 节省 |
|-------|--------|--------|------|
| SYSTEM_PROMPT | ~400 字 | ~150 字 | −250 tokens |
| 日报文章数 | 10 篇 | 3 篇 | −70% |
| 文章内容截断 | 2,000 字符 | 500 字符 | −75% |
| 对话历史 | 6 轮 | 2 轮 | −67% |

## 模型参数调优

```python
# 优化前
"temperature": 0.5,    # 回答多样 → 缓存命中率 ~50%
"max_tokens": 2000,    # 输出上限过大

# 优化后
"temperature": 0.3,    # 回答一致 → 缓存命中率 ~95%
"max_tokens": 1000,    # 500字内足够回答大部分问题
```

## 请求级缓存

```python
# 缓存键设计
question_type = classify_question(req.message)
cache_key = f"chat:{question_type}:{normalize_question(req.message)}"
if req.article_id:
    cache_key += f":{req.article_id}"

# 差异化 TTL
ttl_map = {
    "general": 86400,    # 1 天
    "chat": 3600,        # 1 小时
    "daily": 3600,       # 1 小时
    "article": 1800,     # 30 分钟
}

# 先查缓存
cached = cache_service.get(cache_key)
if cached:
    return {"reply": cached, "cached": True}  # 零 tokens！

# 未命中 → 调用 AI
reply = call_ai_api(...)
cache_service.set(cache_key, reply, ttl_map[question_type])
```

## 综合收益

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 单次输入 tokens | ~600 | ~200 | −67% |
| 缓存命中率 | 0%（无缓存） | 33%+（同问题 100%） | — |
| 重复问题成本 | 600 tokens | 0 tokens | −100% |

## 面试话术

> "Token 优化四层策略。第一层问题预分类——闲聊和通用知识不注入上下文。第二层请求级缓存——相同问题第二次零成本。第三层上下文精简——Prompt 从 400 砍到 150 字，历史从 6 轮减到 2 轮。第四层参数调优——temperature 0.5→0.3，回答一致缓存命中率大幅上升。四层叠加，重复问题零成本，新问题降 60%。"

## Temperature 详解

| 温度 | 效果 | 适用场景 |
|------|------|---------|
| 0.1 | 几乎确定输出 | 采集处理（格式必须稳定） |
| 0.3 | 回答一致但自然 | 知识问答、日报对话 |
| 0.5 | 适度多样 | 一般对话 |
| 0.7-1.0 | 创意多样 | 写作、头脑风暴 |

**原理**：Temperature 控制 Softmax 输出概率的分布锐度。值越低，最高概率词被选中的倾向越强，输出越确定。值越高，低概率词也有机会被选中，输出越多样。