"""
Signal - 文章评论区（改造计划 §3.2）
=====================================

只开放，不主动运营。匿名/登录均可发表评论。
基础防线：关键词过滤（防垃圾） + 举报机制。

约束遵守：
  - 不动现有 user 系统 / auth / newsletter / bookmark 等模块。
  - 不引入新依赖。
  - 评论审核默认通过，被举报后审核标记隐藏；管理员可事后处理。
  - 匿名评论不要求用户登录，仅需可选展示名。
"""

import os
import re
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from api.models.database import get_db
from api.services.jwt_verify import verify_token
from api.services.cache import invalidate_cache

router = APIRouter()


# ── 敏感词列表（内置基础防垃圾） ──────────────
# 关键词匹配：含这些词（完整或子串）的评论将被自动拒绝。
# 不依赖外部 API / 词典，仅覆盖最基础的垃圾 / 广告 / 恶意内容。
# 如需扩展，直接在列表末尾追加即可。
_SPAM_KEYWORDS: List[str] = [
    "加微信", "加V", "加我微信", "微信号",
    "QQ群", "加QQ", "扣扣",
    "兼职", "刷单", "日赚",
    "赌博", "赌场", "彩票",
    "色情", "裸聊", "援交",
    "代开发票", "办证",
    "点击链接", "免费领取",
]


def _check_spam(content: str) -> bool:
    """检查评论内容是否含敏感词。返回 True=含垃圾/恶意内容。"""
    lower = content.lower()
    for kw in _SPAM_KEYWORDS:
        if kw.lower() in lower:
            return True
    return False


def get_optional_user_id(authorization: str = Header(None)) -> Optional[str]:
    """从 Authorization Header 可选地提取用户 ID。
    未登录用户返回 None（可以匿名评论）。"""
    if not authorization:
        return None
    try:
        return verify_token(authorization)
    except Exception:
        return None


# ── 请求/响应模型 ──────────────────────────────


class CommentCreate(BaseModel):
    article_id: str
    content: str
    author_name: str = ""  # 匿名展示名（可选）
    parent_id: Optional[str] = None  # 回复的父评论 ID


class ReportCreate(BaseModel):
    comment_id: str
    reason: str
    reporter_token: str = ""  # 匿名举报者标识


# ── 评论操作 ──────────────────────────────────


@router.post("/comments", tags=["评论"])
async def create_comment(
    req: CommentCreate,
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """发表评论（匿名/登录均可）。

    自动防垃圾检查：含敏感词返回 400。
    登录用户：author_name 可选（不走 DB profile，防隐私泄露）。
    匿名用户：author_name 可选。
    """
    content = (req.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    if len(content) > 2000:
        raise HTTPException(status_code=400, detail="评论内容过长（最多 2000 字）")

    # 防垃圾
    if _check_spam(content):
        raise HTTPException(status_code=400, detail="评论内容包含违规关键词，请修改后重试")

    author_name = (req.author_name or "").strip()
    if author_name and len(author_name) > 50:
        raise HTTPException(status_code=400, detail="展示名过长（最多 50 字）")

    # 匿名默认展示名
    if not author_name:
        author_name = "匿名读者"

    data = {
        "article_id": req.article_id,
        "content": content,
        "author_name": author_name,
        "parent_id": req.parent_id,
        "user_id": user_id,
    }

    db = get_db()

    # 检查父评论存在
    if req.parent_id:
        try:
            parent = db.client.table("article_comments") \
                .select("id") \
                .eq("id", req.parent_id) \
                .execute()
            if not parent.data:
                raise HTTPException(status_code=404, detail="回复的父评论不存在")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail="评论系统异常")

    try:
        result = db.client.table("article_comments").insert(data).execute()
        comment = result.data[0] if result.data else {}
        # 清除该文章评论缓存（若以后加缓存）
        invalidate_cache(f"comments:{req.article_id}")
        return comment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="发表评论失败")


@router.get("/comments/{article_id}", tags=["评论"])
async def get_comments(article_id: str):
    """获取指定文章的所有**已审核**评论（含回复的嵌套结构）。

    只返回 is_approved=True 的评论（被举报后隐藏）。
    按 created_at DESC 排列（最新在前），无分页（每篇评论量不大）。
    """
    try:
        db = get_db()
        # 查出所有已审核根评论
        rows = db.client.table("article_comments") \
            .select("*") \
            .eq("article_id", article_id) \
            .eq("is_approved", True) \
            .order("created_at", desc=True) \
            .execute()

        comments = rows.data or []

        # 按 parent_id 组织为嵌套结构
        # 第一遍：收集所有 ID → 映射
        all_comments = {c["id"]: {**c, "replies": []} for c in comments}

        root_comments = []
        for c in all_comments.values():
            pid = c.get("parent_id")
            if pid and pid in all_comments:
                all_comments[pid]["replies"].append(c)
            else:
                root_comments.append(c)

        # 回复按 created_at 升序（旧→新，对话流）
        for rc in root_comments:
            rc["replies"].sort(key=lambda x: x.get("created_at") or "")

        return {"comments": root_comments, "total": len(comments)}
    except Exception as e:
        # 降级：DB 不可达返回空列表
        return {"comments": [], "total": 0}


@router.post("/comments/report", tags=["评论"])
async def report_comment(req: ReportCreate):
    """举报一条评论。

    匿名举报者可选传 reporter_token 标识（防同一人重复举报同一评论）。
    被举报后评论的 is_reported=True 且 is_approved=False（前台隐藏，等待管理员审核）。
    """
    if not req.comment_id:
        raise HTTPException(status_code=400, detail="请提供评论 ID")
    reason = (req.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="请填写举报原因")
    if len(reason) > 500:
        raise HTTPException(status_code=400, detail="举报原因过长（最多 500 字）")

    token = (req.reporter_token or "").strip() or "anonymous"

    db = get_db()

    try:
        # 检查评论是否存在
        existing = db.client.table("article_comments") \
            .select("id, is_reported") \
            .eq("id", req.comment_id) \
            .execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="该评论不存在")

        # 写入举报记录（UNIQUE 防重复）
        db.client.table("comment_reports").insert({
            "comment_id": req.comment_id,
            "reason": reason,
            "reporter_token": token,
        }).execute()

        # 标记评论为"已举报 + 待审核隐藏"
        db.client.table("article_comments") \
            .update({"is_reported": True, "is_approved": False, "updated_at": datetime.now(timezone.utc).isoformat()}) \
            .eq("id", req.comment_id) \
            .execute()

        invalidate_cache(f"comments:*")
        return {"success": True, "message": "举报已提交，编辑部将尽快处理"}
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        if "duplicate key" in err_msg.lower() or "unique" in err_msg.lower() or "already exists" in err_msg.lower():
            return {"success": True, "message": "你已举报过该评论"}
        raise HTTPException(status_code=500, detail="举报提交失败")
