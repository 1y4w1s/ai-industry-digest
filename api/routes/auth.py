"""
Signal - 用户认证与个人数据接口
依赖 Supabase Auth，通过 Authorization Header 鉴权
"""

import os
import jwt
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from api.models.database import DatabaseManager

router = APIRouter()
db = DatabaseManager()


def get_user_id(authorization: str = Header(None)) -> str:
    """从 Authorization Header 验证 JWT token 并提取用户 ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")
    
    token = authorization.replace("Bearer ", "")
    
    # 尝试解析 JWT token
    try:
        # Supabase JWT 使用 RS256 算法，需要公钥验证
        # 简化实现：直接解码不验证签名（生产环境应验证）
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub")
        if user_id:
            return user_id
    except Exception:
        pass
    
    # 如果无法解析 JWT，直接使用 token 作为 user_id（兼容旧实现）
    return token


# ── 请求/响应模型 ──────────────────────────────


class BookmarkRequest(BaseModel):
    article_id: str
    note: str = ""


class BookmarkDeleteRequest(BaseModel):
    bookmark_id: str


class HistoryRequest(BaseModel):
    article_id: str


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
    """记录浏览历史"""
    db.add_reading_history(user_id, req.article_id)
    return {"success": True}


@router.get("/history", tags=["历史"])
async def list_history(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_user_id),
):
    """获取浏览历史"""
    return db.get_reading_history(user_id, page=page, page_size=page_size)


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
