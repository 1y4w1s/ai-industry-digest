"""
F-15 监控路由

提供仪表盘 API 端点
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from api.services.monitor import get_metric_aggregator

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/dashboard")
async def get_dashboard(days: int = Query(7, ge=1, le=90)):
    """仪表盘概览"""
    aggregator = get_metric_aggregator()
    return aggregator.dashboard(days=days)


@router.get("/metrics")
async def get_recent_metrics(limit: int = Query(20, ge=1, le=100)):
    """最近检索记录"""
    aggregator = get_metric_aggregator()
    return aggregator.recent_searches(limit=limit)
