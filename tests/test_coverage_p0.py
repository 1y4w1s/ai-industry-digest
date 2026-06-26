"""
P0-P2 深度覆盖补齐 — v2：修复 mock 细节

覆盖：
  - reranker._rerank_with_model 模型推理路径
  - retrieval.rewrite_query LLM 同步 httpx 路径
  - retrieval.search() 各环节 except 降级
  - aggregator 全部内部方法
  - query_suggestion 主题推荐/相关查询
  - compression._summarize_mode 异步 LLM 路径
"""

import os
import sys
import asyncio
import math
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key-12345")
sys.modules["supabase"] = MagicMock()
sys.modules["supabase._sync"] = MagicMock()
sys.modules["supabase._sync.client"] = MagicMock()
sys.modules["supabase._sync.client.SupabaseException"] = Exception

from api.services.retrieval import AdvancedRetrievalService
from api.services.graph_retrieval import GraphRetrievalService
from api.services.reranker import RerankerService, RerankerConfig
from api.services.compression import CompressionService
from api.services.monitor import MetricCollector, MetricAggregator
from api.services.query_suggestion import QuerySuggestionService
from api.models.database import DatabaseManager


# ============================================================
# Helpers
# ============================================================

def make_chain(data=None, count_val=None):
    data = data or []
    count_val = count_val if count_val is not None else len(data)
    c = MagicMock()
    c.execute.return_value.data = data
    c.execute.return_value.count = count_val
    c.eq.return_value = c
    c.or_.return_value = c
    c.order.return_value = c
    c.limit.return_value = c
    c.in_.return_value = c
    c.gte.return_value = c
    c.contains.return_value = c
    c.ilike.return_value = c
    c.select.return_value = c
    c.not_.return_value = c
    return c


def make_tab(mapping=None):
    """table() 返回按表名分发的 mock"""
    mapping = mapping or {}
    t = MagicMock()
    t.insert.return_value = make_chain([])
    t.update.return_value = make_chain([])
    t.delete.return_value = make_chain([])

    def select_side(*args, **kwargs):
        name = args[0] if args else ""
        chain = mapping.get(name)
        if chain:
            return chain
        return make_chain([])

    t.select.side_effect = select_side
    return t


def make_retrieval_svc():
    with patch("api.services.retrieval.get_embedding_service") as m:
        f = MagicMock()
        f.get_embedding = AsyncMock(return_value=[0.1] * 1024)
        m.return_value = f
        svc = AdvancedRetrievalService()
        svc.embedding_service = f
        return svc


# ============================================================
# Part A — reranker: _rerank_with_model 真实路径
# ============================================================

class TestRerankerWithModel:
    def make_items(self, n=3):
        return [{
            "chunk": {"id": f"c{i}", "content": f"test {i}", "document_id": "d1"},
            "document": {"id": "d1", "name": "doc1", "file_type": "md"},
            "score": 0.5 + i * 0.1, "fused_score": 0.5 + i * 0.1,
        } for i in range(n)]

    def test_predict_produces_sigmoid_scores(self):
        svc = RerankerService(RerankerConfig(force_fallback=False))
        mc = MagicMock()
        mc.predict.return_value = [[2.0], [1.0], [0.5]]
        with patch.object(svc, "_model", mc):
            with patch.object(svc, "_load_model", return_value=True):
                r = asyncio.run(svc.rerank("q", self.make_items(3), top_k=3))
        assert len(r) == 3
        assert abs(r[0]["re_score"] - 1 / (1 + math.exp(-2))) < 0.01
        assert abs(r[1]["re_score"] - 1 / (1 + math.exp(-1))) < 0.01
        assert "re_raw_score" in r[0]

    def test_flat_list_scores(self):
        svc = RerankerService(RerankerConfig(force_fallback=False))
        mc = MagicMock()
        mc.predict.return_value = [3.0, 2.0, 1.0]
        with patch.object(svc, "_model", mc):
            with patch.object(svc, "_load_model", return_value=True):
                r = asyncio.run(svc.rerank("q", self.make_items(3), top_k=3))
        assert abs(r[0]["re_score"] - 1 / (1 + math.exp(-3))) < 0.01

    def test_top_k_respected(self):
        svc = RerankerService(RerankerConfig(force_fallback=False))
        mc = MagicMock()
        mc.predict.return_value = [[1.0], [2.0], [3.0]]
        with patch.object(svc, "_model", mc):
            with patch.object(svc, "_load_model", return_value=True):
                r = asyncio.run(svc.rerank("q", self.make_items(3), top_k=2))
        assert len(r) == 2

    def test_tolist_conversion(self):
        class Fake:
            def tolist(self):
                return [[2.0], [1.0]]
        svc = RerankerService(RerankerConfig(force_fallback=False))
        mc = MagicMock()
        mc.predict.return_value = Fake()
        with patch.object(svc, "_model", mc):
            with patch.object(svc, "_load_model", return_value=True):
                r = asyncio.run(svc.rerank("q", self.make_items(2), top_k=2))
        assert len(r) == 2


# ============================================================
# Part B — retrieval: rewrite_query（同步 httpx）
# ============================================================

class TestRewriteQuery:
    def test_no_api_key_returns_original(self):
        svc = make_retrieval_svc()
        with patch.dict(os.environ, {}, clear=True):
            assert svc.rewrite_query("test") == "test"

    def test_success(self):
        svc = make_retrieval_svc()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.Client") as mc:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"choices": [{"message": {"content": "改写结果"}}]}
                mc.return_value.__enter__.return_value.post.return_value = resp
                assert svc.rewrite_query("test") == "改写结果"

    def test_empty_response_returns_original(self):
        svc = make_retrieval_svc()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.Client") as mc:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"choices": [{"message": {"content": ""}}]}
                mc.return_value.__enter__.return_value.post.return_value = resp
                assert svc.rewrite_query("test") == "test"

    def test_http_500_returns_original(self):
        svc = make_retrieval_svc()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.Client") as mc:
                resp = MagicMock()
                resp.status_code = 500
                mc.return_value.__enter__.return_value.post.return_value = resp
                assert svc.rewrite_query("test") == "test"

    def test_exception_returns_original(self):
        svc = make_retrieval_svc()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.Client") as mc:
                mc.return_value.__enter__.return_value.post.side_effect = Exception("err")
                assert svc.rewrite_query("test") == "test"

    def test_with_history(self):
        svc = make_retrieval_svc()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.Client") as mc:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"choices": [{"message": {"content": "改写结果"}}]}
                mc.return_value.__enter__.return_value.post.return_value = resp
                assert svc.rewrite_query("test", history=[{"role": "user", "content": "你好"}]) == "改写结果"


# ============================================================
# Part C — retrieval: search() except 降级
# ============================================================

class TestSearchExceptionPaths:
    def test_vector_search_exception_falls_back_to_keyword(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        chain = make_chain([{
            "id": "c1", "content": "test keyword", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "d1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }])
        tab = MagicMock()
        tab.select.return_value = chain
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab
        db.client.rpc = lambda n, p: (_ for _ in ()).throw(Exception("RPC fail"))

        svc.embedding_service.get_embedding = AsyncMock(return_value=[0.1] * 1024)

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_graph_retrieval_service") as mg:
                mg.return_value.graph_search.return_value = []
                r = asyncio.run(svc.search("test keyword", "user-1",
                                           use_routing=False, use_hybrid=True,
                                           use_reranker=False))
        assert len(r) > 0

    def test_reranker_exception_skipped(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        chain = make_chain([{
            "id": "c1", "content": "test", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "d1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }])
        tab = MagicMock()
        tab.select.return_value = chain
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab
        db.client.rpc = lambda n, p: make_chain([])

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_reranker_service") as mr:
                mr.return_value.rerank.side_effect = Exception("rerank fail")
                with patch("api.services.retrieval.get_graph_retrieval_service") as mg:
                    mg.return_value.graph_search.return_value = []
                    r = asyncio.run(svc.search("test", "user-1",
                                               use_routing=False, use_hybrid=True,
                                               use_reranker=True))
        assert isinstance(r, list)

    def test_graph_search_exception_skipped(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        chain = make_chain([{
            "id": "c1", "content": "test", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "d1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }])
        tab = MagicMock()
        tab.select.return_value = chain
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab
        db.client.rpc = lambda n, p: make_chain([])

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_graph_retrieval_service") as mg:
                mg.return_value.graph_search.side_effect = Exception("graph fail")
                r = asyncio.run(svc.search("test", "user-1",
                                           use_routing=False, use_hybrid=True,
                                           use_reranker=False))
        assert isinstance(r, list)

    def test_log_search_exception_does_not_break(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        tab = MagicMock()
        tab.select.return_value = make_chain([])
        tab.insert.side_effect = Exception("insert fail")
        db.client.table.return_value = tab

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_router_service") as mr:
                s = MagicMock()
                s.intent_label = "推荐类"
                s.intent.name = "RECOMMEND"
                s.use_rewrite = False; s.use_hybrid = False
                s.use_reranker = False; s.limit_multiplier = 1.0
                mr.return_value.route.return_value = s
                with patch("api.services.query_suggestion.get_query_suggestion_service") as ms:
                    ms.return_value.suggest.return_value = {"correction": None, "topics": ["AI"], "related_queries": []}
                    r = asyncio.run(svc.search("test", "user-1", use_routing=True))
        assert isinstance(r, list)


# ============================================================
# Part D — aggregator: 全部内部方法
# ============================================================

class TestAggregatorFull:
    def make_db_with_table(self, chain_for_table=None):
        """chain_for_table: {table_name: chain}"""
        chain_for_table = chain_for_table or {}
        db = MagicMock()
        db.client = MagicMock()

        def get_tbl(name):
            c = chain_for_table.get(name)
            if c is not None:
                return c
            t = MagicMock()
            t.select.return_value = make_chain([])
            t.insert = MagicMock()
            t.update = MagicMock()
            t.delete = MagicMock()
            return t

        db.client.table.side_effect = get_tbl
        return db

    # ── _count ──
    def test_count_normal(self):
        agg = MetricAggregator()
        c = make_chain([], count_val=42)
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._count(db, "search", "since") == 42

    def test_count_zero_result(self):
        agg = MetricAggregator()
        c = make_chain([], count_val=5)
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._count_zero_result(db, "since") == 5

    # ── _query_latencies ──
    def test_query_latencies_normal(self):
        agg = MetricAggregator()
        c = make_chain([{"latency_ms": 100}, {"latency_ms": 200}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._query_latencies(db, "since") == [100, 200]

    def test_query_latencies_skip_none(self):
        agg = MetricAggregator()
        c = make_chain([{"latency_ms": None}, {"latency_ms": 100}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._query_latencies(db, "since") == [100]

    def test_query_latencies_empty(self):
        agg = MetricAggregator()
        c = make_chain([])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._query_latencies(db, "since") == []

    # ── _percentile ──
    def test_percentile_empty(self):
        assert MetricAggregator()._percentile([], 50) == 0

    def test_percentile_single(self):
        assert MetricAggregator()._percentile([100], 95) == 100

    def test_percentile_normal(self):
        vals = list(range(1, 101))
        # p50: idx = int(100 * 50 / 100) = 50 → vals[50] = 51
        # p95: idx = int(100 * 95 / 100) = 95 → vals[95] = 96
        assert MetricAggregator()._percentile(vals, 50) == 51
        assert MetricAggregator()._percentile(vals, 95) == 96

    # ── _avg_top_score ──
    def test_avg_top_score_empty(self):
        agg = MetricAggregator()
        db = self.make_db_with_table({"kb_metrics": make_chain([])})
        assert agg._avg_top_score(db, "since") == 0.0

    def test_avg_top_score_list(self):
        agg = MetricAggregator()
        c = make_chain([{"top_scores": [0.8, 0.7]}, {"top_scores": [0.9, 0.6]}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert abs(agg._avg_top_score(db, "since") - 0.85) < 0.01

    def test_avg_top_score_string_compat(self):
        agg = MetricAggregator()
        c = make_chain([{"top_scores": "[0.8,0.7]"}, {"top_scores": [0.9, 0.6]}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert abs(agg._avg_top_score(db, "since") - 0.85) < 0.01

    def test_avg_top_score_skip_none(self):
        agg = MetricAggregator()
        c = make_chain([{"top_scores": None}, {"top_scores": [0.9]}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert abs(agg._avg_top_score(db, "since") - 0.9) < 0.01

    def test_avg_top_score_bad_string(self):
        agg = MetricAggregator()
        c = make_chain([{"top_scores": "bad-json"}, {"top_scores": [0.9]}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert abs(agg._avg_top_score(db, "since") - 0.9) < 0.01

    # ── _route_distribution ──
    def test_route_distribution(self):
        agg = MetricAggregator()
        # route_dist 查的是 kb_metrics, 不用 eq 过滤表名
        c = make_chain([{"route": "hybrid"}, {"route": "vector"}, {"route": "hybrid"}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._route_distribution(db, "since") == {"hybrid": 2, "vector": 1}

    def test_route_distribution_empty(self):
        agg = MetricAggregator()
        c = make_chain([])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._route_distribution(db, "since") == {}

    def test_route_distribution_unknown_default(self):
        agg = MetricAggregator()
        c = make_chain([{"route": None}, {"route": "hybrid"}])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._route_distribution(db, "since") == {"unknown": 1, "hybrid": 1}

    # ── _compression_stats ──
    def test_compression_stats_empty(self):
        agg = MetricAggregator()
        c = make_chain([])
        db = self.make_db_with_table({"kb_metrics": c})
        r = agg._compression_stats(db, "since")
        assert r["avg_ratio"] == 0 and r["avg_compressed_chars"] == 0

    def test_compression_stats_normal(self):
        agg = MetricAggregator()
        c = make_chain([
            {"original_chars": 1000, "compressed_chars": 400, "compress_mode": "extract"},
            {"original_chars": 500, "compressed_chars": 200, "compress_mode": "extract"},
        ])
        db = self.make_db_with_table({"kb_metrics": c})
        r = agg._compression_stats(db, "since")
        assert abs(r["avg_ratio"] - 0.4) < 0.01
        assert r["avg_compressed_chars"] == 300
        assert r["mode_distribution"]["extract"] == 2

    def test_compression_stats_skip_zero_orig(self):
        agg = MetricAggregator()
        c = make_chain([
            {"original_chars": 0, "compressed_chars": 100, "compress_mode": "x"},
            {"original_chars": 1000, "compressed_chars": 500, "compress_mode": "y"},
        ])
        db = self.make_db_with_table({"kb_metrics": c})
        r = agg._compression_stats(db, "since")
        assert abs(r["avg_ratio"] - 0.5) < 0.01

    # ── _top_errors ──
    def test_top_errors_normal(self):
        agg = MetricAggregator()
        c = make_chain([
            {"error_msg": "timeout"}, {"error_msg": "timeout"}, {"error_msg": "limit"},
        ])
        db = self.make_db_with_table({"kb_metrics": c})
        r = agg._top_errors(db, "since")
        assert r[0]["msg"] == "timeout" and r[0]["count"] == 2
        assert r[1]["count"] == 1

    def test_top_errors_empty(self):
        agg = MetricAggregator()
        c = make_chain([])
        db = self.make_db_with_table({"kb_metrics": c})
        assert agg._top_errors(db, "since") == []

    def test_top_errors_none_msg(self):
        agg = MetricAggregator()
        c = make_chain([{"error_msg": None}])
        db = self.make_db_with_table({"kb_metrics": c})
        r = agg._top_errors(db, "since")
        assert "未知错误" in r[0]["msg"]

    # ── recent_searches ──
    def test_recent_searches(self):
        agg = MetricAggregator()
        c = make_chain([{"query": "test", "user_id": "u1"}])
        db = self.make_db_with_table({"kb_metrics": c})
        with patch("api.services.monitor.aggregator.get_db", return_value=db):
            r = agg.recent_searches()
        assert len(r) == 1

    def test_recent_searches_exception(self):
        agg = MetricAggregator()
        db = MagicMock()
        db.client.table.side_effect = Exception("err")
        with patch("api.services.monitor.aggregator.get_db", return_value=db):
            assert agg.recent_searches() == []

    # ── dashboard ──
    def test_dashboard_exception_returns_default(self):
        agg = MetricAggregator()
        db = MagicMock()
        db.client.table.side_effect = Exception("err")
        with patch("api.services.monitor.aggregator.get_db", return_value=db):
            r = agg.dashboard(days=7)
        assert set(r) == {"period", "summary", "routing", "compression", "errors"}

    def test_dashboard_full(self):
        agg = MetricAggregator()
        with patch.object(agg, "_count", side_effect=[100, 5]):
            with patch.object(agg, "_count_zero_result", return_value=3):
                with patch.object(agg, "_query_latencies", return_value=[100, 200]):
                    with patch.object(agg, "_avg_top_score", return_value=0.8):
                        with patch.object(agg, "_route_distribution", return_value={"hybrid": 1}):
                            with patch.object(agg, "_compression_stats",
                                              return_value={"avg_ratio": 0.3, "mode_distribution": {}, "avg_compressed_chars": 300}):
                                with patch.object(agg, "_top_errors", return_value=[{"msg": "t", "count": 1}]):
                                    r = agg.dashboard(7)
        assert r["summary"]["total_searches"] == 100
        assert r["summary"]["total_errors"] == 5
        assert r["summary"]["error_rate"] == 0.05
        assert r["summary"]["zero_result_rate"] == 0.03
        assert r["summary"]["avg_latency_ms"] == 150
        assert r["summary"]["p95_latency_ms"] == 200
        assert r["summary"]["avg_top_score"] == 0.8
        assert r["routing"]["hybrid"] == 1


# ============================================================
# Part E — query_suggestion 高级路径
# ============================================================

class TestQuerySuggestionAdvanced:
    def test_suggest_exception_returns_partial(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        svc._find_spelling_candidates = MagicMock(return_value=[])
        svc._suggest_topics = MagicMock(side_effect=Exception("topic err"))
        svc._suggest_related_queries = MagicMock(return_value=[])
        r = svc.suggest("test", "user-1")
        assert "correction" in r and "topics" in r and "related_queries" in r

    def test_find_spelling_candidates_empty_keywords(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        svc._extract_keywords = MagicMock(return_value=[])
        assert svc._find_spelling_candidates("的") == []

    def test_suggest_topics_db_exception(self):
        """DB 异常时 fallback 到基于关键词的推荐"""
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        db = MagicMock()
        db.client.table.side_effect = Exception("DB err")
        with patch("api.services.query_suggestion.get_db", return_value=db):
            r = svc._suggest_topics("AI", "user-1", 5)
        # fallback 返回关键词本身
        assert "ai" in r

    def test_suggest_topics_with_data(self):
        """DB 有数据时返回实体类型主题"""
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        db = MagicMock()
        db.client = MagicMock()
        c1 = make_chain([{"type": "company"}, {"type": "technology"}])
        c2 = make_chain([{"name": "OpenAI", "count": 10}, {"name": "GPT", "count": 5}])
        tab = MagicMock()

        def select_side(*args, **kwargs):
            cols = args[0] if args else ""
            if cols == "type":
                return c1
            return c2

        tab.select.side_effect = select_side
        db.client.table.return_value = tab
        with patch("api.services.query_suggestion.get_db", return_value=db):
            r = svc._suggest_topics("AI", "user-1", 5)
        assert len(r) > 0

    def test_suggest_related_queries_db_exception(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        db = MagicMock()
        db.client.table.side_effect = Exception("DB err")
        with patch("api.services.query_suggestion.get_db", return_value=db):
            assert svc._suggest_related_queries("AI", "user-1", 5) == []

    def test_suggest_related_queries_with_data(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        db = MagicMock()
        db.client = MagicMock()
        c = make_chain([{"name": "AI是什么.md"}, {"name": "AI应用.md"}])
        tab = MagicMock()
        tab.select.return_value = c
        db.client.table.return_value = tab
        with patch("api.services.query_suggestion.get_db", return_value=db):
            r = svc._suggest_related_queries("AI", "user-1", 5)
        assert len(r) == 2
        assert "AI是什么" in r


# ============================================================
# Part F — compression: _summarize_mode（异步 httpx）
# ============================================================

class TestCompressionSummarizeMode:
    def test_no_api_key_returns_empty(self):
        svc = CompressionService()
        with patch.dict(os.environ, {}, clear=True):
            assert asyncio.run(svc._summarize_mode("q", [], 500)) == ""

    def test_llm_success(self):
        svc = CompressionService()
        chunks = [{"chunk": {"content": "A" * 100}}]
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.AsyncClient") as mc:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"choices": [{"message": {"content": "摘要文本"}}]}
                inst = MagicMock()
                inst.__aenter__.return_value.post.return_value = resp
                mc.return_value = inst
                r = asyncio.run(svc._summarize_mode("LLM", chunks, 500))
        assert "摘要文本" in r

    def test_llm_timeout(self):
        svc = CompressionService()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.AsyncClient") as mc:
                inst = MagicMock()
                inst.__aenter__.return_value.post.side_effect = asyncio.TimeoutError("timeout")
                mc.return_value = inst
                assert asyncio.run(svc._summarize_mode("q", [{"chunk": {"content": "t"}}], 500)) == ""

    def test_llm_exception(self):
        svc = CompressionService()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.AsyncClient") as mc:
                inst = MagicMock()
                inst.__aenter__.return_value.post.side_effect = Exception("err")
                mc.return_value = inst
                assert asyncio.run(svc._summarize_mode("q", [{"chunk": {"content": "t"}}], 500)) == ""

    def test_truncates_long_result(self):
        svc = CompressionService()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.AsyncClient") as mc:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"choices": [{"message": {"content": "B" * 300}}]}
                inst = MagicMock()
                inst.__aenter__.return_value.post.return_value = resp
                mc.return_value = inst
                r = asyncio.run(svc._summarize_mode("q", [{"chunk": {"content": "t"}}], max_chars=100))
        assert len(r) == 100

    def test_http_500_returns_empty(self):
        svc = CompressionService()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch("httpx.AsyncClient") as mc:
                resp = MagicMock()
                resp.status_code = 500
                inst = MagicMock()
                inst.__aenter__.return_value.post.return_value = resp
                mc.return_value = inst
                assert asyncio.run(svc._summarize_mode("q", [{"chunk": {"content": "t"}}], 500)) == ""

    def test_compress_delegates_to_summarize(self):
        svc = CompressionService()
        # 内容必须超过 max_chars 才能进入模式分支
        chunks = [{"chunk": {"content": "大语言模型是一种深度学习模型。"}}]
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
            with patch.object(svc, "_summarize_mode", return_value="摘要结果"):
                r = asyncio.run(svc.compress("LLM", chunks, max_chars=5, mode="summarize"))
        assert r == "摘要结果"


# ============================================================
# Part G — retrieval: keyword_search 内部打分循环
# ============================================================

class TestKeywordSearchScoring:
    def _setup_db(self, chunks):
        db = MagicMock()
        db.client = MagicMock()
        doc_chain = make_chain([{"id": "d1"}, {"id": "d2"}])
        chunk_chain = make_chain(chunks)
        tab = MagicMock()
        tab.select.side_effect = [doc_chain, chunk_chain]
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab
        return db

    def make_chunk(self, cid, content, doc_id="d1", doc_name="测试文档"):
        return {
            "id": cid, "content": content, "document_id": doc_id,
            "kb_documents": {"id": doc_id, "name": doc_name, "file_type": "md",
                             "is_public": True, "user_id": "user-1"},
        }

    def test_keyword_in_content_scores(self):
        svc = make_retrieval_svc()
        db = self._setup_db([self.make_chunk("c1", "AI AI AI 技术")])
        with patch("api.services.retrieval.jieba.lcut", return_value=["ai"]):
            with patch("api.services.retrieval.db", db):
                r = svc.keyword_search("AI", "user-1")
        assert len(r) == 1
        assert r[0]["score"] == 9  # 3 * 3

    def test_keyword_in_doc_name_scores(self):
        svc = make_retrieval_svc()
        chunk = self.make_chunk("c1", "无关内容", doc_name="AI文档")
        db = self._setup_db([chunk])
        with patch("api.services.retrieval.jieba.lcut", return_value=["ai"]):
            with patch("api.services.retrieval.db", db):
                r = svc.keyword_search("AI", "user-1")
        assert len(r) == 1
        assert r[0]["score"] == 2

    def test_keyword_in_both_accumulates(self):
        svc = make_retrieval_svc()
        chunk = self.make_chunk("c1", "AI 技术", doc_name="AI文档")
        db = self._setup_db([chunk])
        with patch("api.services.retrieval.jieba.lcut", return_value=["ai"]):
            with patch("api.services.retrieval.db", db):
                r = svc.keyword_search("AI", "user-1")
        assert len(r) == 1
        assert r[0]["score"] == 5  # content 1*3 + doc_name 2

    def test_keyword_multiple_words(self):
        svc = make_retrieval_svc()
        chunk = self.make_chunk("c1", "发展", doc_name="AI文档")
        db = self._setup_db([chunk])
        with patch("api.services.retrieval.jieba.lcut", return_value=["ai", "发展"]):
            with patch("api.services.retrieval.db", db):
                r = svc.keyword_search("AI 发展", "user-1")
        assert len(r) == 1
        assert r[0]["score"] == 5  # 发展(content 3) + AI(doc_name 2)

    def test_no_matching_keywords_returns_empty(self):
        svc = make_retrieval_svc()
        chunk = self.make_chunk("c1", "其他内容")
        db = self._setup_db([chunk])
        with patch("api.services.retrieval.jieba.lcut", return_value=["关键字"]):
            with patch("api.services.retrieval.db", db):
                r = svc.keyword_search("关键字", "user-1")
        assert r == []

    def test_no_doc_ids_returns_empty(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        db.client.table.return_value.select.return_value = make_chain([])
        with patch("api.services.retrieval.db", db):
            assert svc.keyword_search("test", "user-1") == []

    def test_db_exception_returns_empty(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client.table.side_effect = Exception("DB down")
        with patch("api.services.retrieval.db", db):
            assert svc.keyword_search("test", "user-1") == []

    def test_results_sorted_by_score_desc(self):
        svc = make_retrieval_svc()
        chunks = [
            self.make_chunk("c1", "AI AI", doc_name="文档1"),
            self.make_chunk("c2", "AI AI AI", doc_name="文档2"),
        ]
        db = self._setup_db(chunks)
        with patch("api.services.retrieval.jieba.lcut", return_value=["ai"]):
            with patch("api.services.retrieval.db", db):
                r = svc.keyword_search("AI", "user-1")
        assert r[0]["chunk"]["id"] == "c2"
        assert r[1]["chunk"]["id"] == "c1"


# ============================================================
# Part H — retrieval: RECOMMEND 模式完整路径
# ============================================================

class TestRecommendMode:
    def test_recommend_with_data(self):
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        items = [{"content": "推荐内容", "document_id": "d1", "id": "c1",
                  "name": "doc1", "file_type": "md", "is_public": True, "user_id": "u1"}]
        tab = MagicMock()
        tab.select.return_value = make_chain(items)
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab
        from api.services.router import QueryIntent
        router = MagicMock()
        s = MagicMock()
        s.intent = QueryIntent.RECOMMEND
        s.intent_label = "推荐类"
        s.use_rewrite = False; s.use_hybrid = False
        s.use_reranker = False; s.limit_multiplier = 1.0
        router.route.return_value = s
        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_router_service", return_value=router):
                with patch.object(svc, "_log_search"):
                    r = asyncio.run(svc.search("推荐", "user-1", use_routing=True))
        assert r[0]["chunk"]["content"] == "推荐内容"

    def test_recommend_without_data_uses_suggest(self):
        from api.services.router import QueryIntent
        svc = make_retrieval_svc()
        db = MagicMock()
        db.client = MagicMock()
        tab = MagicMock()
        tab.select.return_value = make_chain([])
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab
        router = MagicMock()
        s = MagicMock()
        s.intent = QueryIntent.RECOMMEND
        s.intent_label = "推荐类"
        s.use_rewrite = False; s.use_hybrid = False
        s.use_reranker = False; s.limit_multiplier = 1.0
        router.route.return_value = s
        fake_suggester = MagicMock()
        fake_suggester.suggest.return_value = {"correction": "纠错", "topics": ["AI"], "related_queries": []}
        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_router_service", return_value=router):
                with patch.object(svc, "_log_search"):
                    with patch("api.services.query_suggestion.get_query_suggestion_service", return_value=fake_suggester):
                        r = asyncio.run(svc.search("推荐", "user-1", use_routing=True))
        assert r[0].get("_suggestions", {}).get("correction") == "纠错"


# ============================================================
# Part I — query_suggestion: 降级 + Jaccard + 内部方法
# ============================================================

class TestQuerySuggestionFallbackMethods:
    def test_fallback_topics_returns_keywords(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        r = svc._fallback_topics("", ["AI", "的", "a", "技术"], 3)
        assert "AI" in r and "技术" in r
        assert "的" not in r and "a" not in r

    def test_fallback_topics_respects_limit(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        assert len(svc._fallback_topics("", ["AI", "技术", "发展"], 2)) == 2

    def test_char_jaccard_exact_match(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        assert svc._char_jaccard("openai", "openai") == 1.0

    def test_char_jaccard_empty_returns_zero(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        assert svc._char_jaccard("", "test") == 0.0
        assert svc._char_jaccard("test", "") == 0.0

    def test_char_jaccard_partial(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        score = svc._char_jaccard("abc", "ab")
        assert 0.4 < score < 0.5

    def test_load_known_terms_cached(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        svc._cached_terms = ["cached"]
        assert svc._load_known_terms() == ["cached"]

    def test_load_known_terms_from_db(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        db = MagicMock()
        db.client = MagicMock()
        ec = make_chain([{"name": "OpenAI"}, {"name": "GPT"}])
        dc = make_chain([{"name": "AI是什么.md"}, {"name": "文档.txt"}])
        tab = MagicMock()
        tab.select.side_effect = [ec, dc]
        db.client.table.return_value = tab
        with patch("api.services.query_suggestion.get_db", return_value=db):
            terms = svc._load_known_terms()
        assert "OpenAI" in terms and "GPT" in terms
        assert "AI是什么" in terms and "文档" in terms

    def test_load_known_terms_db_exception(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        db = MagicMock()
        db.client.table.side_effect = Exception("DB err")
        with patch("api.services.query_suggestion.get_db", return_value=db):
            assert svc._load_known_terms() == []

    def test_suggest_low_confidence_no_correction(self):
        svc = QuerySuggestionService.__new__(QuerySuggestionService)
        svc._find_spelling_candidates = MagicMock(return_value=[{"term": "x", "score": 0.3}])
        svc._suggest_topics = MagicMock(return_value=[])
        svc._suggest_related_queries = MagicMock(return_value=[])
        r = svc.suggest("x", "u1")
        assert r["correction"] is None
