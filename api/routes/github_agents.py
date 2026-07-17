"""
Signal - GitHub AI Agent 高星项目 API（首页「今日 GitHub 推荐」卡片数据源）

轻量 JSON 端点，复用 processor.github_agents.fetch_github_agents：
- 走后端代理 GitHub Search API（避免前端暴露 token / 触发限流）
- 任何失败（网络/限流/异常）一律降级返回空 items + 200，不 500
- 可选 query 参数：range(week|month|quarter) / min_stars / sort(stars|trending) / limit
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query

from processor.github_agents import fetch_github_agents

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/github-agents", tags=["GitHub 推荐"])
async def github_agents(
    range: str = Query("week", description="时间范围：week|month|quarter"),
    min_stars: int = Query(100, ge=0, description="最低 star 数"),
    sort: str = Query("stars", description="排序：stars(降序)|trending(新星飙升)"),
    limit: int = Query(8, ge=1, le=30, description="返回条数"),
):
    """从 GitHub 拉取 AI Agent 相关高星仓库，供首页卡片展示。"""
    try:
        items = fetch_github_agents(
            range=range, min_stars=min_stars, sort=sort, limit=limit
        )
    except Exception as e:  # 任何意外都降级，绝不 500
        logger.warning("github-agents fetch failed: %s", e)
        return {
            "items": [],
            "range": range,
            "min_stars": min_stars,
            "sort": sort,
            "limit": limit,
            "count": 0,
            "error": "fetch_failed",
        }
    return {
        "items": items,
        "range": range,
        "min_stars": min_stars,
        "sort": sort,
        "limit": limit,
        "count": len(items),
    }
