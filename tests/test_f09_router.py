"""
F-09 单元测试：查询意图路由（QueryRouterService）

测试 QueryRouterService.classify() 和 route() 方法对各类查询的分类准确性。
不依赖数据库、外部 API，仅测试模式匹配逻辑。
"""

import pytest
from api.services.router import QueryRouterService, QueryIntent


@pytest.fixture
def router():
    return QueryRouterService()


class TestQueryClassification:
    """查询意图分类测试"""

    # ── 推荐类 ──

    def test_recommend_典型(self, router):
        assert router.classify("有什么文档") == QueryIntent.RECOMMEND

    def test_recommend_推荐(self, router):
        assert router.classify("推荐") == QueryIntent.RECOMMEND

    def test_recommend_看看(self, router):
        assert router.classify("看看有哪些文档") == QueryIntent.RECOMMEND

    def test_recommend_最新(self, router):
        assert router.classify("最新文档") == QueryIntent.RECOMMEND

    def test_recommend_英文(self, router):
        assert router.classify("latest") == QueryIntent.RECOMMEND

    # ── 定义类 ──

    def test_definition_什么是(self, router):
        assert router.classify("什么是大语言模型") == QueryIntent.DEFINITION

    def test_definition_是什么(self, router):
        assert router.classify("RAG是什么") == QueryIntent.DEFINITION

    def test_definition_解释(self, router):
        assert router.classify("解释一下 Transformer 架构") == QueryIntent.DEFINITION

    def test_definition_介绍(self, router):
        assert router.classify("介绍一下机器学习") == QueryIntent.DEFINITION

    def test_definition_定义(self, router):
        assert router.classify("LLM的定义") == QueryIntent.DEFINITION

    def test_definition_含义(self, router):
        assert router.classify("微调的含义") == QueryIntent.DEFINITION

    def test_definition_英文_what_is(self, router):
        assert router.classify("what is a large language model") == QueryIntent.DEFINITION

    def test_definition_英文_explain(self, router):
        assert router.classify("explain attention mechanism") == QueryIntent.DEFINITION

    def test_definition_什么叫(self, router):
        assert router.classify("什么叫知识蒸馏") == QueryIntent.DEFINITION

    # ── 比较类 ──

    def test_comparison_区别(self, router):
        assert router.classify("GPT和BERT的区别") == QueryIntent.COMPARISON

    def test_comparison_对比(self, router):
        assert router.classify("PyTorch与TensorFlow的对比") == QueryIntent.COMPARISON

    def test_comparison_vs(self, router):
        assert router.classify("Transformer vs RNN") == QueryIntent.COMPARISON

    def test_comparison_哪个好(self, router):
        assert router.classify("哪个模型更好") == QueryIntent.COMPARISON

    def test_comparison_比较(self, router):
        assert router.classify("比较LoRA和全量微调") == QueryIntent.COMPARISON

    def test_comparison_英文(self, router):
        assert router.classify("difference between CNN and RNN") == QueryIntent.COMPARISON

    # ── 时间筛选类 ──

    def test_time_年份(self, router):
        assert router.classify("2024年关于LLM的文章") == QueryIntent.TIME_BASED

    def test_time_最近(self, router):
        assert router.classify("最近有关Agent的文章") == QueryIntent.TIME_BASED

    def test_time_本月(self, router):
        assert router.classify("本月发布的论文") == QueryIntent.TIME_BASED

    def test_time_近30天(self, router):
        assert router.classify("近30天的行业动态") == QueryIntent.TIME_BASED

    def test_time_英文_recent(self, router):
        assert router.classify("recent papers on transformers") == QueryIntent.TIME_BASED

    # ── 通用类（兜底） ──

    def test_general_复杂查询(self, router):
        assert router.classify("如何用Python实现一个简单的聊天机器人") == QueryIntent.GENERAL

    def test_general_混合查询(self, router):
        assert router.classify("大模型训练需要多少数据") == QueryIntent.GENERAL

    def test_general_英文(self, router):
        assert router.classify("how to train a neural network") == QueryIntent.GENERAL

    def test_general_短查询(self, router):
        assert router.classify("OpenAI") == QueryIntent.GENERAL

    def test_general_代码相关(self, router):
        assert router.classify("用LangChain实现RAG的代码示例") == QueryIntent.GENERAL


class TestRouteStrategy:
    """路由策略配置测试"""

    def test_recommend_strategy(self, router):
        strategy = router.route("有什么文档")
        assert strategy.intent == QueryIntent.RECOMMEND
        assert strategy.intent_label == "推荐类"
        assert strategy.use_rewrite is False
        assert strategy.use_hybrid is False
        assert strategy.use_reranker is False

    def test_definition_strategy(self, router):
        strategy = router.route("什么是大语言模型")
        assert strategy.intent == QueryIntent.DEFINITION
        assert strategy.intent_label == "定义类"
        assert strategy.use_rewrite is True
        assert strategy.use_hybrid is True
        assert strategy.use_reranker is True
        assert strategy.limit_multiplier == 2.0

    def test_comparison_strategy(self, router):
        strategy = router.route("GPT和BERT的区别")
        assert strategy.intent == QueryIntent.COMPARISON
        assert strategy.limit_multiplier == 3.0  # 宽召回

    def test_time_based_strategy(self, router):
        strategy = router.route("2024年的文章")
        assert strategy.intent == QueryIntent.TIME_BASED
        assert strategy.needs_time_filter is True

    def test_general_strategy(self, router):
        strategy = router.route("如何训练大模型")
        assert strategy.intent == QueryIntent.GENERAL
        assert strategy.limit_multiplier == 2.0


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_query(self, router):
        """空字符串"""
        result = router.classify("")
        assert result == QueryIntent.GENERAL

    def test_whitespace_only(self, router):
        """纯空白"""
        result = router.classify("   ")
        assert result == QueryIntent.GENERAL

    def test_special_characters(self, router):
        """特殊字符"""
        result = router.classify("@#$%^&*()")
        assert result == QueryIntent.GENERAL

    def test_very_long_query(self, router):
        """超长查询"""
        long_q = "大语言模型" * 100
        result = router.classify(long_q)
        assert result in (QueryIntent.GENERAL, QueryIntent.DEFINITION)

    def test_definition_priority_over_time(self, router):
        """定义类优先级高于时间筛选类"""
        result = router.classify("什么是2024年的LLM")
        assert result == QueryIntent.DEFINITION

    def test_comparison_priority_over_definition(self, router):
        """比较类优先级高于定义类"""
        result = router.classify("什么是GPT和BERT的区别")
        assert result == QueryIntent.COMPARISON

    def test_recommend_priority_over_all(self, router):
        """短查询+推荐关键词时优先级最高"""
        result = router.classify("推荐")
        assert result == QueryIntent.RECOMMEND
