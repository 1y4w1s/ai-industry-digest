"""
综合测试：检索服务核心逻辑

覆盖模块：
  - retrieval.py: rrf_fusion, _enrich_with_suggestions, rewrite_query, _log_search
  - compression.py: _extract_mode 纯逻辑
  - reranker.py: _fallback_rerank 纯逻辑
  - graph_retrieval.py: _extract_query_entities, _is_relation_query
  - monitor/router.py: FastAPI 端点响应格式

注意：所有 import 在 mock 环境变量后进行，避免模块级 get_db() 触发真实连接。
"""

import os
import sys
import json
import math
import pytest
from unittest.mock import patch, MagicMock

# 先 mock 环境变量再 import 服务模块（避免模块级 get_db() 触发数据库连接）
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key-12345")

# Mock supabase 客户端，阻止 import supabase 时触发真实连接
sys.modules["supabase"] = MagicMock()
sys.modules["supabase._sync"] = MagicMock()
sys.modules["supabase._sync.client"] = MagicMock()
sys.modules["supabase._sync.client.SupabaseException"] = Exception

# 现在可以安全 import
from api.services.retrieval import AdvancedRetrievalService
from api.services.compression import CompressionService
from api.services.reranker import RerankerService, RerankerConfig
from api.services.graph_retrieval import GraphRetrievalService
from api.services.document_tracker import DocumentTracker
from api.services.monitor import MetricCollector, MetricAggregator
from api.services.monitor import get_metric_collector, get_metric_aggregator


def make_chunk(chunk_id: str, content: str = "test content") -> dict:
    """构造测试用的 chunk 对象"""
    return {
        "chunk": {"id": chunk_id, "content": content, "document_id": f"doc-{chunk_id}"},
        "document": {"id": f"doc-{chunk_id}", "name": f"doc-{chunk_id}", "file_type": "md",
                      "is_public": True, "user_id": "user-1"},
        "score": 0.5,
    }


def make_item(content: str, chunk_id: str = "1") -> dict:
    """构造 reranker 测试用 item"""
    return {
        "chunk": {"id": chunk_id, "content": content, "document_id": "doc-1"},
        "document": {"id": "doc-1", "name": "test", "file_type": "md"},
        "score": 0.5, "fused_score": 0.5,
    }


def make_chunk_item(content: str) -> dict:
    """构造 compression 测试用 chunk"""
    return {"chunk": {"content": content}}


# ============================================================
# Part 1: retrieval.py — rrf_fusion
# ============================================================

class TestRRFFusion:
    """RRF 三路融合测试"""

    def test_empty_inputs(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        assert svc.rrf_fusion([], []) == []

    def test_single_source(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        result = svc.rrf_fusion([make_chunk("a"), make_chunk("b")], [])
        assert result[0]["chunk"]["id"] == "a"

    def test_two_way_fusion(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        vec = [make_chunk("a"), make_chunk("b")]
        kw = [make_chunk("b"), make_chunk("c")]
        result = svc.rrf_fusion(vec, kw)
        ids = [r["chunk"]["id"] for r in result]
        assert "b" in ids and "a" in ids and "c" in ids

    def test_three_way_fusion(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        result = svc.rrf_fusion([make_chunk("a")], [make_chunk("b")], [make_chunk("c")])
        assert len(result) == 3

    def test_scores_range(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        result = svc.rrf_fusion([make_chunk("a"), make_chunk("b")], [make_chunk("c")])
        for r in result:
            assert 0 < r["fused_score"] < 1

    def test_k_parameter(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        r1 = svc.rrf_fusion([make_chunk("a")], [make_chunk("b")], k=10)
        r2 = svc.rrf_fusion([make_chunk("a")], [make_chunk("b")], k=100)
        assert r1[0]["fused_score"] != r2[0]["fused_score"]

    def test_weights_vector_dominant(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        vec = [make_chunk("a"), make_chunk("x")]
        kw = [make_chunk("b"), make_chunk("x")]
        graph = [make_chunk("c"), make_chunk("x")]
        result = svc.rrf_fusion(vec, kw, graph)
        scores = {r["chunk"]["id"]: r["fused_score"] for r in result}
        assert scores["a"] > scores["b"] > scores["c"]

    def test_dedup(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        assert len(svc.rrf_fusion([make_chunk("a")], [make_chunk("a")])) == 1

    def test_inf_rank_handling(self):
        """不在某路结果中的 chunk 排名为 inf"""
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        result = svc.rrf_fusion([make_chunk("a")], [make_chunk("b")])
        a = next(r for r in result if r["chunk"]["id"] == "a")
        b = next(r for r in result if r["chunk"]["id"] == "b")
        assert a["fused_score"] != b["fused_score"]


# ============================================================
# Part 2: retrieval.py — _enrich_with_suggestions
# ============================================================

class TestEnrichWithSuggestions:

    def test_no_real_suggestions(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        r = [make_chunk("a")]
        s = {"correction": None, "correction_confidence": 0.0, "topics": [], "related_queries": []}
        assert svc._enrich_with_suggestions(r, s) is r

    def test_with_correction(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        s = {"correction": "openai", "correction_confidence": 0.9, "topics": [], "related_queries": []}
        enriched = svc._enrich_with_suggestions([make_chunk("a")], s)
        assert enriched[0]["_suggestions"]["correction"] == "openai"

    def test_empty_with_correction(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        s = {"correction": "gpt", "correction_confidence": 0.8, "topics": [], "related_queries": []}
        enriched = svc._enrich_with_suggestions([], s)
        assert enriched[0]["chunk"]["id"] == "_suggestion_"

    def test_empty_with_topics(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        s = {"correction": None, "correction_confidence": 0.0, "topics": ["LLM"], "related_queries": []}
        enriched = svc._enrich_with_suggestions([], s)
        assert enriched[0]["_suggestions"]["topics"] == ["LLM"]

    def test_empty_with_related(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        s = {"correction": None, "correction_confidence": 0.0, "topics": [], "related_queries": ["LLM部署"]}
        enriched = svc._enrich_with_suggestions([], s)
        assert enriched[0]["_suggestions"]["related_queries"] == ["LLM部署"]


# ============================================================
# Part 3: retrieval.py — rewrite_query
# ============================================================

class TestRewriteQuery:

    def test_no_api_key_fallback(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        with patch.dict(os.environ, {}, clear=True):
            assert svc.rewrite_query("test") == "test"

    def test_api_failure_fallback(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "key"}):
            with patch("httpx.Client.post", side_effect=Exception("err")):
                assert svc.rewrite_query("test") == "test"

    def test_empty_response(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "key"}):
            mock = MagicMock()
            mock.status_code = 200
            mock.json.return_value = {"choices": [{"message": {"content": ""}}]}
            with patch("httpx.Client.post", return_value=mock):
                assert svc.rewrite_query("test") == "test"


# ============================================================
# Part 4: retrieval.py — _log_search
# ============================================================

class TestLogSearch:

    def test_writes_to_file(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        with patch("builtins.open", MagicMock()) as m:
            svc._log_search("q", "rw", True, True, "hybrid", [], vector_count=0, keyword_count=0, latency_ms=100)
            m.assert_called_once()

    def test_file_error_graceful(self):
        svc = AdvancedRetrievalService.__new__(AdvancedRetrievalService)
        with patch("builtins.open", side_effect=PermissionError("denied")):
            svc._log_search("q", "rw", True, True, "hybrid", [], latency_ms=100)


# ============================================================
# Part 5: compression.py — _extract_mode
# ============================================================

class TestCompressionExtractMode:

    def test_relevant_sentences(self):
        svc = CompressionService()
        chunks = [
            make_chunk_item("深度学习是机器学习的一个分支。Transformer 是一种神经网络架构。"),
            make_chunk_item("大语言模型基于 Transformer 架构。"),
        ]
        r = svc._extract_mode("Transformer 神经网络", chunks, 500)
        assert "Transformer" in r and "神经网络" in r

    def test_respect_max_chars(self):
        svc = CompressionService()
        r = svc._extract_mode("test", [make_chunk_item("A " * 500)], 100)
        assert len(r) <= 100

    def test_empty_chunks(self):
        svc = CompressionService()
        assert svc._extract_mode("q", [], 100) == ""

    def test_empty_content(self):
        svc = CompressionService()
        assert svc._extract_mode("q", [make_chunk_item("")], 100) == ""

    def test_key_term_boost(self):
        svc = CompressionService()
        chunks = [
            make_chunk_item("今天天气很好。大语言模型改变世界。"),
            make_chunk_item("这是一篇无关文章。"),
        ]
        r = svc._extract_mode("LLM 模型", chunks, 100)
        assert "大语言模型" in r

    def test_single_sentence_fits(self):
        """单个句子放得下时不截断"""
        svc = CompressionService()
        r = svc._extract_mode("test", [make_chunk_item("Hello world.")], 100)
        assert "Hello world" in r


# ============================================================
# Part 6: reranker.py — _fallback_rerank
# ============================================================

class TestRerankerFallback:

    def test_basic_scoring(self):
        svc = RerankerService(RerankerConfig(force_fallback=True))
        items = [make_item("Transformer 注意力机制详解", "a"), make_item("今天天气很好", "b")]
        r = svc._fallback_rerank("Transformer 注意力", items, 2)
        assert r[0]["chunk"]["id"] == "a"
        assert "re_score" in r[0]

    def test_empty_input(self):
        svc = RerankerService(RerankerConfig(force_fallback=True))
        assert svc._fallback_rerank("q", [], 5) == []

    def test_score_range(self):
        svc = RerankerService(RerankerConfig(force_fallback=True))
        r = svc._fallback_rerank("ML", [make_item("机器学习深度学习", "a")], 1)
        assert 0 <= r[0]["re_score"] <= 1

    def test_relevant_higher(self):
        svc = RerankerService(RerankerConfig(force_fallback=True))
        items = [
            make_item("RAG 技术原理详解，检索增强生成应用", "a"),
            make_item("今天天气很好，适合出去散步", "b"),
        ]
        r = svc._fallback_rerank("RAG 检索增强", items, 2)
        assert r[0]["chunk"]["id"] == "a"


# ============================================================
# Part 7: graph_retrieval.py — 纯逻辑方法
# ============================================================

class TestGraphExtractQueryEntities:

    def test_extract_simple(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        entities = svc._extract_query_entities("Transformer 架构")
        assert len(entities) > 0

    def test_extract_empty(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert svc._extract_query_entities("") == []

    def test_filter_stop_words(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        entities = svc._extract_query_entities("什么是的了的")
        assert len(entities) == 0

    def test_deduplication(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        entities = svc._extract_query_entities("Hello hello world")
        assert entities.count("hello") <= 1

    def test_pure_punctuation(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert svc._extract_query_entities("！？。，") == []


class TestGraphIsRelationQuery:

    def test_guanxi(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert svc._is_relation_query("OpenAI 与微软的关系")

    def test_investor(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert svc._is_relation_query("OpenAI的投资方")

    def test_founder(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert svc._is_relation_query("百度的创始人")

    def test_english_related(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert svc._is_relation_query("AI related to healthcare")

    def test_general_not_relation(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert not svc._is_relation_query("什么是大语言模型")

    def test_empty_not_relation(self):
        svc = GraphRetrievalService.__new__(GraphRetrievalService)
        assert not svc._is_relation_query("")


# ============================================================
# Part 8: monitor/router.py — FastAPI 端点
# ============================================================

from fastapi.testclient import TestClient
from api.main import app


class TestMonitorAPI:

    def test_dashboard_200(self):
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            resp = TestClient(app).get("/api/monitor/dashboard")
            assert resp.status_code == 200
            assert "period" in resp.json()

    def test_dashboard_days_30(self):
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            resp = TestClient(app).get("/api/monitor/dashboard?days=30")
            assert resp.status_code == 200

    def test_dashboard_invalid_days(self):
        resp = TestClient(app).get("/api/monitor/dashboard?days=-1")
        assert resp.status_code == 422

    def test_metrics_200(self):
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            resp = TestClient(app).get("/api/monitor/metrics")
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    def test_metrics_limit(self):
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            resp = TestClient(app).get("/api/monitor/metrics?limit=5")
            assert resp.status_code == 200


# ============================================================
# Part 9: 文档追踪器边界
# ============================================================

class TestDocumentTrackerBoundary:

    def test_empty_hash(self):
        assert DocumentTracker().compute_hash("") == "d41d8cd98f00b204e9800998ecf8427e"

    def test_hash_consistency(self):
        t = DocumentTracker()
        assert t.compute_hash("hello") == t.compute_hash("hello")

    def test_hash_different(self):
        assert DocumentTracker().compute_hash("a") != DocumentTracker().compute_hash("b")

    def test_hash_length(self):
        assert len(DocumentTracker().compute_hash("test")) == 32


# ============================================================
# Part 10: 监控采集器边界
# ============================================================

class TestMetricCollectorBoundary:

    def test_unknown_type(self):
        r = MetricCollector()._build_record("unknown", {"query": "test"})
        assert r["metric_type"] == "unknown"

    def test_error_with_extra(self):
        r = MetricCollector()._build_record("error", {"error_msg": "err", "extra": {"k": "v"}})
        assert r["error_msg"] == "err"

    def test_sync_context(self):
        c = MetricCollector()
        with patch.object(c, "_async_insert", return_value=None):
            c.collect("search", {"query": "test"})


# ============================================================
# Part 11: monitor/__init__.py
# ============================================================

class TestMonitorPackage:

    def test_imports(self):
        from api.services.monitor import MetricCollector, MetricAggregator
        assert MetricCollector is not None and MetricAggregator is not None

    def test_singletons(self):
        assert get_metric_collector() is get_metric_collector()
        assert get_metric_aggregator() is get_metric_aggregator()
