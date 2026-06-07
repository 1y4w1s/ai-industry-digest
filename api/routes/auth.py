"""
Signal - 用户认证与个人数据接口
依赖 Supabase Auth，通过 Authorization Header 鉴权
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from api.models.database import get_db
from api.services.jwt_verify import verify_token

router = APIRouter()
db = get_db()


def get_user_id(authorization: str = Header(None)) -> str:
    """从 Authorization Header 验证 JWT token 并提取用户 ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")
    
    user_id = verify_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证凭证")
    
    return user_id


# ── 请求/响应模型 ──────────────────────────────


class BookmarkRequest(BaseModel):
    article_id: str
    note: str = ""


class BookmarkDeleteRequest(BaseModel):
    bookmark_id: str


class HistoryRequest(BaseModel):
    article_id: str
    read_percent: Optional[float] = None
    duration_sec: Optional[int] = None


class FeedbackRequest(BaseModel):
    article_id: str
    feedback: str  # thumbs_up / thumbs_down


class ProfileResponse(BaseModel):
    id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


# ── 用户资料 ──────────────────────────────────


@router.get("/me", tags=["用户"])
async def get_profile(user_id: str = Depends(get_user_id)):
    """获取当前用户信息"""
    profile = db.get_or_create_profile(user_id)
    return profile


# ── 收藏 ─────────────────────────────────────


@router.post("/bookmarks", tags=["收藏"])
async def add_bookmark(
    req: BookmarkRequest,
    user_id: str = Depends(get_user_id),
):
    """添加收藏"""
    return db.add_bookmark(user_id, req.article_id, req.note)


@router.delete("/bookmarks/{bookmark_id}", tags=["收藏"])
async def remove_bookmark(
    bookmark_id: str,
    user_id: str = Depends(get_user_id),
):
    """取消收藏"""
    ok = db.remove_bookmark(bookmark_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="收藏不存在")
    return {"success": True}


@router.get("/bookmarks", tags=["收藏"])
async def list_bookmarks(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_user_id),
):
    """获取收藏列表"""
    return db.get_bookmarks(user_id, page=page, page_size=page_size)


# ── 浏览历史 ─────────────────────────────────


@router.post("/history", tags=["历史"])
async def add_history(
    req: HistoryRequest,
    user_id: str = Depends(get_user_id),
):
    """记录浏览历史（带阅读深度）"""
    db.add_reading_history(
        user_id,
        req.article_id,
        read_percent=req.read_percent,
        duration_sec=req.duration_sec,
    )
    return {"success": True}


@router.get("/history", tags=["历史"])
async def list_history(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_user_id),
):
    """获取浏览历史"""
    return db.get_reading_history(user_id, page=page, page_size=page_size)


@router.delete("/history", tags=["历史"])
async def clear_history(user_id: str = Depends(get_user_id)):
    """清除所有浏览历史"""
    db.clear_reading_history(user_id)
    return {"success": True}


# ── 文章反馈 ─────────────────────────────────


@router.post("/feedback", tags=["反馈"])
async def submit_feedback(
    req: FeedbackRequest,
    user_id: str = Depends(get_user_id),
):
    """提交文章反馈 👍/👎"""
    try:
        return db.submit_feedback(user_id, req.article_id, req.feedback)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats", tags=["用户"])
async def get_user_stats(user_id: str = Depends(get_user_id)):
    """获取用户统计数据（阅读数、收藏数、连续天数、热力图、来源分布）"""
    return db.get_user_stats(user_id)


@router.get("/reading-trends", tags=["用户"])
async def get_reading_trends(user_id: str = Depends(get_user_id)):
    """获取阅读趋势（月度趋势、高峰时段、平均阅读字数）"""
    return db.get_reading_trends(user_id)
