"""
Signal - 管理员 API 路由
包含缓存统计、系统监控等管理功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta

from api.services.cache import cache
from api.services.jwt_verify import verify_token
from api.models.database import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()
db = get_db()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """获取当前用户 ID"""
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return user_id


# ── 系统统计 ─────────────────────────────────


@router.get("/stats/overview")
async def get_stats_overview() -> Dict[str, Any]:
    """获取系统概览统计"""
    # 文章总数
    article_count = db.get_article_count()
    
    # 用户总数
    users_result = db.client.table("user_profiles").select("id", count="exact").execute()
    total_users = users_result.count or 0
    
    # 收藏总数
    bookmarks_result = db.client.table("bookmarks").select("id", count="exact").execute()
    total_bookmarks = bookmarks_result.count or 0
    
    # 阅读记录总数
    history_result = db.client.table("reading_history").select("id", count="exact").execute()
    total_reads = history_result.count or 0
    
    # 今日活跃用户（今天有阅读记录的用户）
    today = datetime.now().date().isoformat()
    active_result = db.client.table("reading_history") \
        .select("user_id", count="exact") \
        .gte("read_at", today) \
        .execute()
    daily_active = len(set(row["user_id"] for row in (active_result.data or [])))
    
    # 本周新增文章
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    week_result = db.client.table("articles") \
        .select("id", count="exact") \
        .gte("created_at", week_ago) \
        .execute()
    articles_this_week = week_result.count or 0
    
    return {
        "total_users": total_users,
        "total_articles": article_count,
        "total_bookmarks": total_bookmarks,
        "total_reads": total_reads,
        "daily_active_users": daily_active,
        "articles_this_week": articles_this_week,
    }


@router.get("/stats/users")
async def get_user_stats(period: str = "30d") -> Dict[str, Any]:
    """获取用户增长趋势"""
    # 解析时间范围
    days = int(period.replace("d", ""))
    start_date = datetime.now() - timedelta(days=days)
    
    # 按日期统计新用户
    result = db.client.table("user_profiles") \
        .select("created_at") \
        .gte("created_at", start_date.isoformat()) \
        .execute()
    
    # 按日期分组
    daily_counts = {}
    for row in result.data or []:
        date_str = row.get("created_at", "")[:10]
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
    
    # 转换为列表
    trend = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
        trend.append({
            "date": date,
            "count": daily_counts.get(date, 0)
        })
    
    return {"period": period, "trend": trend}


@router.get("/stats/articles")
async def get_article_stats() -> Dict[str, Any]:
    """获取文章统计"""
    # 来源分布
    sources = db.get_sources()
    source_dist = []
    for source in sources:
        result = db.client.table("articles") \
            .select("id", count="exact") \
            .eq("source_name", source) \
            .execute()
        source_dist.append({
            "source": source,
            "count": result.count or 0
        })
    
    # 按重要性分布
    importance_dist = {"high": 0, "medium": 0, "low": 0}
    for imp in importance_dist.keys():
        result = db.client.table("articles") \
            .select("id", count="exact") \
            .eq("importance", imp) \
            .execute()
        importance_dist[imp] = result.count or 0
    
    return {
        "source_distribution": source_dist,
        "importance_distribution": importance_dist,
        "total_sources": len(sources),
    }


@router.get("/stats/articles/popular")
async def get_popular_articles(limit: int = 10) -> List[Dict[str, Any]]:
    """获取热门文章（按阅读次数）"""
    # 统计每篇文章的阅读次数
    result = db.client.table("reading_history") \
        .select("article_id, articles(id, title, source_name)") \
        .execute()
    
    # 统计阅读次数
    read_counts = {}
    for row in result.data or []:
        article = row.get("articles")
        if article:
            article_id = article.get("id")
            if article_id:
                read_counts[article_id] = read_counts.get(article_id, 0) + 1
    
    # 排序并取前 N
    sorted_articles = sorted(read_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    # 获取文章详情
    popular = []
    for article_id, count in sorted_articles:
        article = db.get_article_by_id(article_id)
        if article:
            popular.append({
                "id": article_id,
                "title": article.get("title"),
                "source": article.get("source_name"),
                "read_count": count,
            })
    
    return popular


# ── 缓存管理 ─────────────────────────────────


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return cache.get_stats()


@router.post("/cache/clear")
async def clear_cache(pattern: str = "*", user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """清除缓存"""
    deleted = cache.delete_pattern(pattern)
    return {"deleted": deleted}


@router.post("/cache/reset-stats")
async def reset_cache_stats(user_id: str = Depends(get_current_user)) -> Dict[str, str]:
    """重置缓存统计"""
    cache.reset_stats()
    return {"status": "ok"}
