"""
Signal - 内容接口路由
日报 + 文章查询 + 文章代理
"""

import httpx
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response
from api.models.database import get_db

router = APIRouter()
db = get_db()


@router.get("/reports", tags=["日报"])
async def list_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(7, ge=1, le=31, description="每页数量"),
):
    """日报列表（分页，按日期倒序）"""
    return db.get_reports(page=page, page_size=page_size)


@router.get("/reports/dates", tags=["日报"])
async def list_report_dates():
    """获取所有已有日报的日期列表（用于归档日历）"""
    return {"dates": db.get_report_dates()}


@router.get("/reports/{report_date}", tags=["日报"])
async def get_report(report_date: str):
    """单日报详情（包含文章列表）"""
    report = db.get_report_by_date(report_date)
    if not report:
        raise HTTPException(status_code=404, detail="日报不存在")
    return report


@router.get("/articles", tags=["文章"])
async def list_articles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="标题关键词搜索"),
    tag: Optional[str] = Query(None, description="标签过滤"),
    source: Optional[str] = Query(None, description="来源过滤"),
    importance: Optional[str] = Query(None, description="重要性过滤"),
    date_from: Optional[str] = Query(None, description="起始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    sort_by: str = Query("published_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向 asc/desc"),
):
    """文章搜索/过滤（分页）"""
    return db.get_articles(
        page=page,
        page_size=page_size,
        keyword=keyword,
        tag=tag,
        source=source,
        importance=importance,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/articles/{article_id}", tags=["文章"])
async def get_article(article_id: str):
    """单篇文章详情"""
    article = db.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


@router.get("/proxy", tags=["代理"])
async def proxy_article(url: str = Query(..., description="目标 URL")):
    """代理获取文章内容（绕过 CORS/X-Frame 限制）"""
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="无效的 URL")

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                }
            )
            content_type = resp.headers.get("content-type", "text/html")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={"X-Frame-Options": "ALLOWALL"}
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="代理请求超时")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"代理请求失败: {e}")


@router.get("/sources", tags=["元数据"])
async def list_sources():
    """所有信息来源列表"""
    return {"sources": db.get_sources()}


@router.get("/tags", tags=["元数据"])
async def list_tags():
    """所有标签列表"""
    return {"tags": db.get_tags()}


@router.get("/stats", tags=["元数据"])
async def get_stats():
    """系统统计信息"""
    return {
        "total_articles": db.get_article_count(),
        "sources": db.get_sources(),
        "tags": db.get_tags(),
    }


@router.get("/home", tags=["首页"])
async def get_home():
    """首页聚合接口：返回报告列表 + 元数据（日报详情由前端按需加载）"""
    reports = db.get_reports(page=1, page_size=7)
    sources = db.get_sources()
    tags = db.get_tags()
    return {
        "reports": reports,
        "sources": sources,
        "tags": tags,
    }
