"""
Signal - 今日主线聚类 API（改造计划 §2.1）
GET /api/main-thread?date=YYYY-MM-DD
  复用 processor.reporter.cluster_stories 的同一份聚类数据（与邮件简报同口径）。
  不强制 LLM / DB；DB 不可达时优雅降级返回空 stories。
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from api.models.database import get_db

router = APIRouter()


def _parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


@router.get("/main-thread", tags=["今日主线"])
async def main_thread(date: str = Query(..., description="简报日期 YYYY-MM-DD")):
    """今日主线（事件聚类结果）。

    - 取该日及前 3 天的文章，复用 cluster_stories 聚类，与邮件同口径。
    - DB 不可达时返回空 stories（前端模块自动隐藏），不影响其余接口。
    """
    try:
        report_date = _parse_date(date)
    except Exception:
        return {
            "report_date": date,
            "stories": [],
            "total_stories": 0,
            "error": "invalid date format, expected YYYY-MM-DD",
        }

    try:
        db = get_db()
        from_date = (report_date - timedelta(days=3)).isoformat()
        res = db.get_articles(
            page=1, page_size=300, date_from=from_date,
            sort_by="published_at", sort_order="desc", use_cache=False,
        )
        rows = (res.get("items") or [])
        # 复用 newsletter 的行->Article 转换，保证与邮件同口径
        from scripts.newsletter import _rows_to_articles
        articles = _rows_to_articles(rows)
        day = [a for a in articles
                if a.published_at and a.published_at.date() == report_date]
        if not day:
            day = articles[:20]
        from processor.reporter import cluster_stories
        return cluster_stories(day, report_date)
    except Exception as e:  # DB / 网络异常：降级为空，不影响整体可用性
        return {
            "report_date": date,
            "stories": [],
            "total_stories": 0,
            "error": str(e),
        }
