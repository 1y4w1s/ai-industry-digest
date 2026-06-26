"""
F-15 MetricCollector — 指标采集器

设计原则：
  - 零侵入：采集代码不修改检索核心逻辑
  - 异步写入：使用 asyncio.create_task 避免阻塞
  - 静默降级：所有异常被捕获并忽略
  - 可推送到 WebSocket：采集后可选择广播到在线客户端

指标类型:
  search    : 检索指标（查询、结果数、分数、延迟）
  rerank    : 重排序指标（精排前后分差）
  compress  : 压缩指标（压缩比、模式）
  route     : 路由指标（意图类型、参数）
  error     : 错误记录
"""

import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from api.models.database import get_db


class MetricCollector:
    """指标采集器"""

    def collect(self, metric_type: str, data: Dict[str, Any]) -> None:
        """
        采集一条指标（异步写入，不阻塞调用方）

        参数:
            metric_type: search / rerank / compress / route / error
            data: 指标数据（见各个 record_* 方法的参数）
        """
        # 安全创建异步任务：仅在事件循环运行时使用 create_task
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._async_insert(metric_type, data))
        except RuntimeError:
            # 无运行中的事件循环（如 Celery 任务、同步测试），同步写入
            asyncio.run(self._async_insert(metric_type, data))

    async def _async_insert(self, metric_type: str, data: dict) -> None:
        """异步写入数据库"""
        try:
            db = get_db()
            record = self._build_record(metric_type, data)
            db.client.table("kb_metrics").insert(record).execute()
        except Exception as e:
            # 静默降级：采集失败不影响主流程
            pass

    def _build_record(self, metric_type: str, data: dict) -> dict:
        """构建数据库记录"""
        base = {
            "metric_type": metric_type,
            "query": data.get("query", ""),
            "user_id": data.get("user_id", ""),
            "latency_ms": data.get("latency_ms", 0),
        }

        if metric_type == "search":
            base.update({
                "vector_count": data.get("vector_count", 0),
                "keyword_count": data.get("keyword_count", 0),
                "graph_count": data.get("graph_count", 0),
                "final_count": data.get("final_count", 0),
                "top_scores": data.get("top_scores", []),
                "route": data.get("route", ""),
                "mode": data.get("mode", ""),
            })
        elif metric_type == "rerank":
            base.update({
                "pre_rerank_top1_score": data.get("pre_score", 0),
                "post_rerank_top1_score": data.get("post_score", 0),
                "rerank_delta": data.get("delta", 0),
            })
        elif metric_type == "compress":
            base.update({
                "original_chars": data.get("original_chars", 0),
                "compressed_chars": data.get("compressed_chars", 0),
                "compress_mode": data.get("mode", ""),
            })
        elif metric_type == "route":
            base.update({
                "intent_type": data.get("intent_type", ""),
                "limit_mult": data.get("limit_mult", 1.0),
                "needs_time_filter": data.get("needs_time_filter", False),
            })
        elif metric_type == "error":
            base.update({
                "error_msg": data.get("error_msg", ""),
                "extra": json.dumps(data.get("extra", {})),
            })

        return base


# 单例
_collector = None


def get_metric_collector() -> MetricCollector:
    global _collector
    if _collector is None:
        _collector = MetricCollector()
    return _collector
