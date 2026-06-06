"""
Signal - 个性化推荐接口
基于用户标签画像，推荐今日日报中的文章
"""

import os
import jwt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from api.models.database import DatabaseManager

router = APIRouter()
db = DatabaseManager()

# Demo 用户配置（与 auth.py 保持一致）
DEMO_USER_ID = "demo-user"
DEMO_USER_UUID = "00000000-0000-0000-0000-000000000001"

# 重要性权重
IMPORTANCE_WEIGHTS = {"high": 3, "medium": 2, "low": 1}


def _resolve_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """从 Header 中解析用户 ID，未登录返回 None"""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    if token == DEMO_USER_ID:
        return DEMO_USER_UUID
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub", token)
    except Exception:
        return token


@router.get("/recommend", tags=["推荐"])
async def get_recommendations(
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    authorization: Optional[str] = Header(None),
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

    # 3. 评分：标签匹配度 × 重要性权重
    scored = []
    for article in candidates:
        article_tags = article.get("tags", []) or []
        importance = article.get("importance", "low") or "low"
        imp_weight = IMPORTANCE_WEIGHTS.get(importance, 1)

        score = 0
        matched_tags = []
        for tag in article_tags:
            if tag in tag_weights:
                match_weight = tag_weights[tag]
                score += match_weight * imp_weight
                matched_tags.append(tag)

        # 即使没有匹配标签也给一个基础分（保证覆盖度）
        if score == 0:
            score = imp_weight * 0.1

        scored.append((score, article, matched_tags))

    # 4. 排序取 top N
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    # 5. 多样性调节：如果前 5 名标签过于集中，替换 1 篇
    used_tags = set()
    for _, article, matched in top:
        for t in matched:
            used_tags.add(t)

    # 如果匹配标签少于 2 种且还有候选文章，从后面选一篇不同标签的
    if len(used_tags) < 2 and len(scored) > limit:
        for score, article, matched in scored[limit:]:
            article_tags = set(article.get("tags", []) or [])
            if not article_tags.issubset(used_tags):
                top[-1] = (score, article, matched)
                break

    # 6. 构建响应
    items = []
    for score, article, matched_tags in top:
        tag_hints = matched_tags[:3] if matched_tags else article.get("tags", [])[:2]
        reason = f"基于你对 {'、'.join(tag_hints[:2])} 话题的关注" if tag_hints else "你可能感兴趣"

        items.append({
            "id": article.get("id", ""),
            "title": article.get("title", ""),
            "summary": (article.get("summary", "") or "")[:200],
            "tags": article.get("tags", []) or [],
            "importance": article.get("importance", "low"),
            "source_name": article.get("source_name", ""),
            "score": round(score, 1),
            "reason": reason,
        })

    return {"items": items, "strategy": "tag_weighted"}
