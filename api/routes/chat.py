"""
AI Industry Digest - AI 对话接口
支持文章级对话（带上下文）和全局对话
"""

import os
import httpx
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from api.models.database import DatabaseManager

router = APIRouter()
db = DatabaseManager()

# 对话上下文存储（生产环境建议用 Redis，这里用内存简化）
chat_contexts: dict = {}


class ChatRequest(BaseModel):
    message: str
    article_id: Optional[str] = None
    session_id: Optional[str] = None  # 用于保持对话上下文


class ChatResponse(BaseModel):
    reply: str
    session_id: str


from datetime import datetime

SYSTEM_PROMPT = f"""你是一个专业的 AI 行业分析师助手，帮助用户理解 AI 行业新闻和趋势。
当前日期: {datetime.now().strftime('%Y年%m月%d日')}

重要规则:
1. 你的知识截止于 2025 年初，但用户会提供最新的文章内容给你分析
2. 当用户问到关于文章中提到的具体事件、数据或新闻时，请基于用户提供的文章内容回答，不要用你的训练数据来反驳
3. 当回答一般性的 AI 行业趋势问题时，如果涉及近期事件，请优先引用用户提供的文章内容
4. 如果你不确定某个具体事件，请坦白说「我不确定，但根据你提供的文章...」

你可以：
1. 总结文章核心观点
2. 解释技术概念
3. 分析行业趋势
4. 对比不同观点
5. 回答关于 AI 行业的任何问题

回答要简洁、准确、有深度。使用中文回答。"""


ARTICLE_CONTEXT_PROMPT = """以下是用户当前正在阅读的一篇文章：

标题: {title}
来源: {source}
摘要: {summary}
标签: {tags}
原文内容概要: {content}

请基于这篇文章回答用户的问题。"""


@router.post("/chat", response_model=ChatResponse, tags=["AI 对话"])
async def chat(req: ChatRequest):
    """AI 对话接口（带文章上下文）"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI 服务未配置（缺少 DEEPSEEK_API_KEY）")

    session_id = req.session_id or f"session_{hash(str(req.article_id))}_{os.urandom(4).hex()}"

    # 构建消息上下文
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # 如果有关联文章，添加上下文
    if req.article_id:
        article = db.get_article_by_id(req.article_id)
        if article:
            context = ARTICLE_CONTEXT_PROMPT.format(
                title=article.get("title", ""),
                source=article.get("source_name", ""),
                summary=article.get("summary", ""),
                tags=", ".join(article.get("tags", []) or []),
                content=(article.get("raw_content", "") or "")[:2000],
            )
            messages.append({"role": "system", "content": context})

    # 添加历史上下文
    history = chat_contexts.get(session_id, [])
    for h in history[-6:]:  # 保留最近 6 轮
        messages.append(h)

    # 加当前消息
    messages.append({"role": "user", "content": req.message})

    # 调用 AI
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 2000,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {e}")

    # 保存上下文
    chat_contexts[session_id] = history + [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": reply},
    ]

    # 限制上下文大小
    if len(chat_contexts) > 1000:
        # 简单清理：删除最早的一半
        keys = list(chat_contexts.keys())[:500]
        for k in keys:
            del chat_contexts[k]

    return ChatResponse(reply=reply, session_id=session_id)
