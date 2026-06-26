"""
F-15 检索质量监控

模块划分：
  - collector.py:    MetricCollector — 指标采集器（同步写入 kb_metrics）
  - aggregator.py:   MetricAggregator — 聚合查询（返回仪表盘 API 所需格式）
  - router.py:       FastAPI router — 暴露监控 API 端点
"""
from .collector import MetricCollector, get_metric_collector
from .aggregator import MetricAggregator, get_metric_aggregator
