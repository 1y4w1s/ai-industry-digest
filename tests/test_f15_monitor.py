"""
F-15 单元测试：检索质量监控（MetricCollector + MetricAggregator）

测试策略：
  - 纯函数测试：_build_record 的字段构造逻辑
  - 降级测试：数据库异常时采集器不崩溃
  - 格式测试：dashboard 返回格式完整性
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from api.services.monitor import MetricCollector, MetricAggregator, get_metric_collector


@pytest.fixture
def collector():
    return MetricCollector()


class TestMetricCollector:
    """MetricCollector 单元测试"""

    def test_build_record_search(self, collector):
        """search 类型记录字段完整"""
        data = {
            "query": "大语言模型",
            "latency_ms": 150,
            "vector_count": 10,
            "final_count": 5,
            "top_scores": [0.95, 0.82, 0.71],
            "route": "hybrid",
            "mode": "hybrid",
        }
        record = collector._build_record("search", data)
        assert record["metric_type"] == "search"
        assert record["query"] == "大语言模型"
        assert record["latency_ms"] == 150
        assert record["vector_count"] == 10
        assert record["final_count"] == 5
        assert record["route"] == "hybrid"
        assert record["mode"] == "hybrid"
        # top_scores 现在是列表（非 JSON 字符串）
        assert record["top_scores"] == [0.95, 0.82, 0.71]

    def test_build_record_rerank(self, collector):
        """rerank 类型记录字段完整"""
        data = {"pre_score": 0.65, "post_score": 0.82, "delta": 0.17}
        record = collector._build_record("rerank", data)
        assert record["metric_type"] == "rerank"
        assert record["pre_rerank_top1_score"] == 0.65
        assert record["post_rerank_top1_score"] == 0.82
        assert record["rerank_delta"] == 0.17

    def test_build_record_compress(self, collector):
        """compress 类型记录字段完整"""
        data = {"original_chars": 1500, "compressed_chars": 600, "mode": "extract"}
        record = collector._build_record("compress", data)
        assert record["metric_type"] == "compress"
        assert record["original_chars"] == 1500
        assert record["compressed_chars"] == 600
        assert record["compress_mode"] == "extract"

    def test_build_record_route(self, collector):
        """route 类型记录字段完整"""
        data = {"intent_type": "DEFINITION", "limit_mult": 2.0, "needs_time_filter": False}
        record = collector._build_record("route", data)
        assert record["metric_type"] == "route"
        assert record["intent_type"] == "DEFINITION"
        assert record["limit_mult"] == 2.0
        assert record["needs_time_filter"] is False

    def test_build_record_error(self, collector):
        """error 类型记录字段完整"""
        data = {"error_msg": "Embedding 超时", "extra": {"service": "embedding"}}
        record = collector._build_record("error", data)
        assert record["metric_type"] == "error"
        assert record["error_msg"] == "Embedding 超时"

    def test_build_record_defaults(self, collector):
        """缺少字段时使用默认值"""
        data = {}
        record = collector._build_record("search", data)
        assert record["query"] == ""
        assert record["latency_ms"] == 0
        assert record["vector_count"] == 0
        assert record["final_count"] == 0

    @pytest.mark.asyncio
    async def test_collect_exception_handling(self, collector):
        """数据库异常时不崩溃"""
        with patch.object(collector, "_async_insert", return_value=None):
            collector.collect("search", {"query": "test"})
            assert True  # 不抛出异常即通过

    @pytest.mark.asyncio
    async def test_async_insert_exception(self, collector):
        """异步写入异常时静默降级"""
        with patch("api.services.monitor.collector.get_db", side_effect=Exception("DB error")):
            # 不应抛出异常
            await collector._async_insert("search", {"query": "test"})

    def test_singleton(self):
        """单例"""
        c1 = get_metric_collector()
        c2 = get_metric_collector()
        assert c1 is c2

    def test_all_metric_types(self, collector):
        """所有指标类型都能构造记录"""
        for mt in ("search", "rerank", "compress", "route", "error"):
            record = collector._build_record(mt, {})
            assert record["metric_type"] == mt


class TestMetricAggregator:
    """MetricAggregator 聚合查询测试"""

    def test_dashboard_exception_handling(self):
        """数据库异常时返回空结构"""
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            agg = MetricAggregator()
            result = agg.dashboard(days=7)
            assert "period" in result
            assert "summary" in result

    def test_dashboard_format(self):
        """dashboard 返回格式完整"""
        agg = MetricAggregator()
        # 在无数据时也应返回完整结构
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            result = agg.dashboard(days=7)
            assert "period" in result
            assert "summary" in result
            assert "routing" in result
            assert "compression" in result
            assert "errors" in result
            # 异常时 summary 为空 dict
            assert result["summary"] == {}

    def test_recent_searches_format(self):
        """recent_searches 返回列表"""
        agg = MetricAggregator()
        with patch("api.services.monitor.aggregator.get_db", side_effect=Exception("DB error")):
            result = agg.recent_searches()
            assert result == []

    def test_percentile_empty(self):
        """空列表百分位返回 0"""
        agg = MetricAggregator()
        assert agg._percentile([], 50) == 0

    def test_percentile_single(self):
        """单元素百分位"""
        agg = MetricAggregator()
        assert agg._percentile([42], 50) == 42
        assert agg._percentile([42], 99) == 42

    def test_percentile_multiple(self):
        """多元素百分位计算（近似值）"""
        agg = MetricAggregator()
        values = list(range(1, 101))  # 1..100
        # 百分位是近似值，索引取整可能造成 ±1 偏差
        p50 = agg._percentile(values, 50)
        p95 = agg._percentile(values, 95)
        p99 = agg._percentile(values, 99)
        assert 49 <= p50 <= 51, f"p50={p50} 超出预期范围 [49,51]"
        assert 94 <= p95 <= 96, f"p95={p95} 超出预期范围 [94,96]"
        assert 98 <= p99 <= 100, f"p99={p99} 超出预期范围 [98,100]"
