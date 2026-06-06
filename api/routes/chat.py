"""
Signal - AI 对话接口
支持文章级对话（带上下文）和全局对话
"""

import os
import httpx
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from api.models.database import get_db
from api.services.tag_extractor import TagExtractor

router = APIRouter()
db = get_db()

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

回答要简洁、准确、有深度。使用中文回答。

重要输出格式规则：
- 当推荐或引用某篇文章时，请使用 Markdown 链接格式输出： [文章标题](/?article=文章ID)
- 例如：[GPT-5 发布引发行业震动](/?article=abc-123)
- 不要只写文章标题不加链接，每篇推荐的文章都必须附带可点击的链接
- 链接目标必须是本站路由 /?article=文章ID"""

# ⚠️ 安全隔离：知识库内容不由本接口注入
# 知识库文档内容仅在 /knowledge 页面独立对话中使用
# 不在全局 AI 助手的 context 中注入 KB 内容，防止 prompt injection 扩散
# 如需为全局助手增加 KB 感知能力，请在独立接口中实现（如 /api/kb/chat）

ARTICLE_CONTEXT_PROMPT = """以下是用户当前正在阅读的一篇文章：

标题: {title}
来源: {source}
摘要: {summary}
标签: {tags}
文章ID: {article_id}
原文内容概要: {content}

请基于这篇文章回答用户的问题。
如需引用/推荐本站文章，请使用 Markdown 链接格式：[文章标题](/?article=文章ID)"""

DAILY_CONTEXT_PROMPT = """以下为今天的 AI 行业日报内容（{report_date}）：
{articles}

请基于以上今日日报中的文章回答用户的问题。
如果用户问"有什么新闻"、"今天有什么"这类问题，直接引用上面日报中的文章来回答。
不要说你没有最新的文章内容——上面就是最新的。"""


@router.post("/chat", response_model=ChatResponse, tags=["AI 对话"])
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
):
    """AI 对话接口（带文章上下文）
    
    上下文来源（按注入顺序）：
      1. SYSTEM_PROMPT — 角色设定
      2. 当前文章（如果 article_id 有值）
      3. 今日日报文章列表（如果 article_id 为空）
      4. 最近 6 轮对话历史
      
    ⚠️ 注意：本接口不注入知识库内容。知识库对话隔离在 /kb 独立上下文中。
    """
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
                article_id=article.get("id", req.article_id),
            )
            messages.append({"role": "system", "content": context})
    else:
        # 首页对话：自动注入今日日报文章作为上下文
        reports = db.get_reports(page=1, page_size=1)
        if reports.get("items"):
            latest = reports["items"][0]
            report_date = latest.get("report_date", "")
            # 获取日报详情（含文章列表）
            report_detail = db.get_report_by_date(report_date)
            if report_detail:
                article_groups = report_detail.get("articles", {})
                if isinstance(article_groups, dict):
                    # Flatten grouped articles into a single list, high first
                    flat = []
                    for priority in ("high", "medium", "low"):
                        flat.extend(article_groups.get(priority, []))
                    article_items = flat[:10]
                    if article_items:
                        articles_text = "\n".join([
                            f"- [{a.get('importance','')}] [{a.get('title','')}](/?article={a.get('id','')})（来源: {a.get('source_name','')}，ID: {a.get('id','')}）\n  {str(a.get('summary',''))[:200]}"
                            for a in article_items
                        ])
                        daily_context = DAILY_CONTEXT_PROMPT.format(
                            report_date=report_date,
                            articles=articles_text,
                        )
                        messages.append({"role": "system", "content": daily_context})
                    else:
                        messages.append({"role": "system", "content": f"今日日期（日报日期）: {report_date}"})
                else:
                    messages.append({"role": "system", "content": f"今日日期（日报日期）: {report_date}"})

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

    # 异步提取标签（不阻塞响应）
    _schedule_tag_extraction(background_tasks, authorization, req.message, db)

    return ChatResponse(reply=reply, session_id=session_id)


def _schedule_tag_extraction(
    background_tasks: BackgroundTasks,
    authorization: Optional[str],
    message: str,
    db_instance,
):
    """调度标签提取任务（仅在用户已登录时执行）"""
    if not authorization:
        return

    token = authorization.replace("Bearer ", "")
    # Demo 用户的标签不落库（共享账户无意义）
    if token == "demo-user":
        return

    # 尝试解析 user_id
    user_id = token
    try:
        import jwt as pyjwt
        decoded = pyjwt.decode(token, options={"verify_signature": False})
        user_id = decoded.get("sub", token)
    except Exception:
        pass

    background_tasks.add_task(_extract_tags, user_id, message, db_instance)


def _extract_tags(user_id: str, message: str, db_instance):
    """后台任务：从消息中提取标签并写入 user_tags"""
    try:
        extractor = TagExtractor.from_database(db_instance)
        matched_tags = extractor.extract(message)
        for tag in matched_tags:
            db_instance.upsert_user_tag(user_id, tag, source='chat')
        if matched_tags:
            print(f"  [TAG] 用户 {user_id[:8]}... 匹配到标签: {matched_tags}")
    except Exception as e:
        print(f"  [TAG] 提取失败（不阻塞）: {e}")
