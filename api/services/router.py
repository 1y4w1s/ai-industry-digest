"""
查询意图路由服务：根据查询类型自动选择最优检索策略

支持的查询类型与对应策略：
  - recommend（推荐类）：按时间排序，返回最新文档
  - definition（定义类）：混合检索 + 精排，保障精度
  - time_based（时间筛选类）：向量检索 + 时间过滤，缩小范围
  - comparison（比较类）：混合检索 + 精排，宽召回
  - general（通用类）：混合检索（默认兜底）
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class QueryIntent(Enum):
    """查询意图类型"""
    RECOMMEND = "recommend"       # 推荐类：有什么文档、推荐
    DEFINITION = "definition"     # 定义类：什么是、解释一下
    TIME_BASED = "time_based"     # 时间筛选类：2024年、最近
    COMPARISON = "comparison"     # 比较类：区别、对比
    GENERAL = "general"           # 通用类（兜底）


@dataclass
class RouteStrategy:
    """检索策略配置"""
    intent: QueryIntent
    intent_label: str             # 中文描述（用于日志）
    use_rewrite: bool = True       # 是否 Query 改写
    use_hybrid: bool = True        # 是否混合检索
    use_reranker: bool = True      # 是否精排
    limit_multiplier: float = 2.0  # 召回倍数（m 倍取 top K）
    needs_time_filter: bool = False  # 是否需要时间过滤
    time_field: str = "created_at"   # 时间字段名


# ── 意图识别规则 ──────────────────────────

# 定义类模式：带疑问词的定义/解释请求
_DEFINITION_PATTERNS = [
    # 中文固定句式
    r"什么是\S{1,20}", r"\S{1,20}是什么",
    r"解释一下\S{0,20}", r"介绍一下\S{0,20}",
    r"说明一下\S{0,20}", r"阐述.*概念",
    r"简述\S{0,20}", r"描述\S{0,20}",
    r"\S{1,20}的定义", r"\S{1,20}的含义",
    r"\S{1,20}的意思", r"什么叫",
    # What/Explain 英文
    r"^what (is|are|does) ", r"^explain ",
    r"^describe ", r"^define ",
]

# 时间筛选类模式：包含时间范围的查询
_TIME_PATTERNS = [
    r"\d{4}年", r"\d{4}-\d{1,2}",
    r"最近\S{0,5}", r"近期", r"本月", r"上周", r"今年",
    r"近\S{0,4}天", r"近\S{0,4}周", r"近\S{0,4}月",
    r"\d{1,2}月\d{1,2}日", r"\d{1,2}月份",
    r"202[0-9]年", r"20[2-9]\d年",
    r"since ", r"recent ", r"last \d+",
]

# 比较类模式：对比/比较的查询
_COMPARISON_PATTERNS = [
    r"\S{1,20}和\S{1,20}的区别", r"\S{1,20}与\S{1,20}的区别",
    r"\S{1,20}和\S{1,20}的对比", r"\S{1,20}与\S{1,20}的对比",
    r"\S{1,20}vs\S{1,20}", r"\S{1,20} VS \S{1,20}",
    r"对比\S{1,20}", r"比较\S{1,20}",
    r"\S{1,20}更好", r"哪个更好",
    r"difference between", r" vs\.? ",
]


class QueryRouterService:
    """查询意图路由服务"""
    
    CLASSIFICATION_RULES = (
        (QueryIntent.COMPARISON, _COMPARISON_PATTERNS),
        (QueryIntent.DEFINITION, _DEFINITION_PATTERNS),
        (QueryIntent.TIME_BASED, _TIME_PATTERNS),
    )
    
    # 推荐类关键词（核心关键词 + 短句检测）
    RECOMMEND_KEYWORDS = [
        "推荐", "看看", "有什么", "什么内容", "内容",
        "文档", "资料", "文章", "列表", "浏览",
        "最近更新", "新文章", "新文档", "最新",
        "recommend", "latest", "new",
    ]
    
    def classify(self, query: str) -> QueryIntent:
        """
        对查询进行分类
        
        优先级：
          1. 推荐类（关键词 + 短句子）
          2. 比较类（包含对比句式）
          3. 定义类（包含定义句式）
          4. 时间筛选类（包含时间表达式）
          5. 通用类（兜底）
        """
        q = query.strip().lower()
        
        # 1. 推荐类检测：短查询 + 推荐关键词
        if self._is_recommend(q):
            return QueryIntent.RECOMMEND
        
        # 2. 按规则匹配
        for intent, patterns in self.CLASSIFICATION_RULES:
            for pattern in patterns:
                if re.search(pattern, q):
                    return intent
        
        # 3. 兜底
        return QueryIntent.GENERAL
    
    def _is_recommend(self, query: str) -> bool:
        """检测是否是推荐类查询"""
        # 短查询 + 含有推荐关键词
        if len(query) < 10:
            # 如果包含时间表达式，应属于时间筛选类而非推荐类
            for pattern in _TIME_PATTERNS:
                if re.search(pattern, query):
                    return False
            for kw in self.RECOMMEND_KEYWORDS:
                if kw in query:
                    return True
        return False
    
    def route(self, query: str) -> RouteStrategy:
        """
        根据查询意图返回最优检索策略配置
        
        策略映射：
          - RECOMMEND:  不改写、不混合，按时间排序
          - DEFINITION: 改写 + 混合 + 精排（最高精度）
          - TIME_BASED: 改写 + 向量检索 + 时间过滤
          - COMPARISON: 改写 + 混合 + 精排 + 宽召回（3 倍）
          - GENERAL:    改写 + 混合（默认）
        """
        intent = self.classify(query)
        
        strategy_map = {
            QueryIntent.RECOMMEND: RouteStrategy(
                intent=QueryIntent.RECOMMEND,
                intent_label="推荐类",
                use_rewrite=False,
                use_hybrid=False,
                use_reranker=False,
            ),
            QueryIntent.DEFINITION: RouteStrategy(
                intent=QueryIntent.DEFINITION,
                intent_label="定义类",
                use_rewrite=True,
                use_hybrid=True,
                use_reranker=True,
                limit_multiplier=2.0,
            ),
            QueryIntent.TIME_BASED: RouteStrategy(
                intent=QueryIntent.TIME_BASED,
                intent_label="时间筛选类",
                use_rewrite=True,
                use_hybrid=True,
                use_reranker=True,
                needs_time_filter=True,
                limit_multiplier=2.0,
            ),
            QueryIntent.COMPARISON: RouteStrategy(
                intent=QueryIntent.COMPARISON,
                intent_label="比较类",
                use_rewrite=True,
                use_hybrid=True,
                use_reranker=True,
                limit_multiplier=3.0,  # 宽召回
            ),
            QueryIntent.GENERAL: RouteStrategy(
                intent=QueryIntent.GENERAL,
                intent_label="通用类",
                use_rewrite=True,
                use_hybrid=True,
                use_reranker=True,
                limit_multiplier=2.0,
            ),
        }
        
        return strategy_map.get(intent, strategy_map[QueryIntent.GENERAL])


# 单例
_router_service = None


def get_router_service() -> QueryRouterService:
    """获取路由器单例"""
    global _router_service
    if _router_service is None:
        _router_service = QueryRouterService()
    return _router_service
