"""
Signal - 个性化推荐接口
基于用户标签画像，推荐今日日报中的文章
"""

import os
from typing import Optional
from fastapi import APIRouter, Header, Query
from api.models.database import get_db
from api.services.jwt_verify import verify_token, DEMO_USER_UUID

router = APIRouter()
db = get_db()

# 重要性权重
IMPORTANCE_WEIGHTS = {"high": 3, "medium": 2, "low": 1}


def _resolve_user_id(authorization: str = Header(None)) -> Optional[str]:
    """从 Header 中解析用户 ID，未登录返回 None（使用标准 JWT 验证链路）"""
    if not authorization:
        return None
    return verify_token(authorization)


@router.get("/recommend", tags=["推荐"])
async def get_recommendations(
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    authorization: str = Header(None),
):
    """获取个性化推荐文章（基于用户标签画像）"""
    user_id = _resolve_user_id(authorization)

    # 未登录用户返回空
    if not user_id:
        return {"items": [], "reason": "请登录后获取个性化推荐"}

    # 1. 获取用户标签权重
    user_tags = db.get_user_tags(user_id)
    tag_weights = {t["tag"]: t["weight"] for t in user_tags}

    if not tag_weights:
        return {"items": [], "reason": "暂无足够的阅读数据，继续浏览以获取个性化推荐"}

    # 2. 获取今日日报文章作为候选池
    reports = db.get_reports(page=1, page_size=1)
    candidates = []
    if reports.get("items"):
        latest = reports["items"][0]
        report_date = latest.get("report_date", "")
        report_detail = db.get_report_by_date(report_date)
        if report_detail:
            article_groups = report_detail.get("articles", {})
            if isinstance(article_groups, dict):
                for priority in ("high", "medium", "low"):
                    for article in article_groups.get(priority, []):
                        candidates.append(article)

    if not candidates:
        return {"items": [], "reason": "今日暂无可推荐的文章"}

    # 3. 评分：标签匹配度 x 重要性权重
    scored = []

    for article in candidates:
        article_tags = set(article.get("tags", []) or [])
        score = 0.0

        # 标签匹配度（核心因子）
        for tag, weight in tag_weights.items():
            if tag in article_tags:
                score += weight * 2.0  # 匹配标签：权重翻倍

        # 重要性权重（辅助因子）
        importance = article.get("importance", "medium")
        score += IMPORTANCE_WEIGHTS.get(importance, 2) * 0.5

        if score > 0:
            scored.append((score, article))

    # 4. 排序取 Top-N
    scored.sort(key=lambda x: -x[0])
    items = [a for _, a in scored[:limit]]

    return {"items": items, "total": len(items)}
