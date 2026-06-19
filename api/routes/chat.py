"""
Signal - AI 对话接口
支持文章级对话（带上下文）和全局对话，整合知识库功能
"""

import os
import httpx
import hashlib
import jieba
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from api.models.database import get_db
from api.services.tag_extractor import TagExtractor
from api.services.cache import cache, cache_key
from api.services.intent_classifier import classify_intent, get_classifier

router = APIRouter()
db = get_db()

# 对话上下文存储（生产环境建议用 Redis，这里用内存简化）
chat_contexts: dict = {}

# 统计信息（内存存储，生产环境建议用 Redis）
chat_stats = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_input_tokens": 0,
    "total_output_tokens": 0,
}


def count_tokens(text: str) -> int:
    """估算文本的 tokens 数量（粗略估算：1 token ≈ 4 字符）"""
    return len(text) // 4


# 日志文件路径
CHAT_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat.log")


def chat_log(msg: str):
    """写入聊天日志到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


# ── 知识库检索功能 ──────────────────────────

def search_kb_chunks(query: str, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    """在知识库切片中搜索相关内容"""
    try:
        # 步骤1：先获取用户有权限访问的文档ID列表
        # 公开文档 OR 用户自己的文档
        docs_result = db.client.table("kb_documents") \
            .select("id") \
            .or_(f"is_public.eq.true,user_id.eq.{user_id}") \
            .execute()
        
        doc_ids = set(doc["id"] for doc in (docs_result.data or []))
        
        if not doc_ids:
            chat_log("[KB] 没有可访问的文档")
            return []
        
        chat_log(f"[KB] 可访问文档数量: {len(doc_ids)}")
        
    except Exception as e:
        chat_log(f"[KB] 获取文档列表失败: {e}")
        return []
    
    # 预处理查询
    query_clean = query.lower().strip()
    
    # 检查是否是通用推荐请求
    recommend_keywords = ["推荐", "看看", "有什么", "什么内容", "内容", "文档", "资料"]
    is_recommend = any(keyword in query_clean for keyword in recommend_keywords)
    
    if is_recommend and len(query_clean) < 10:
        # 用户只是要求推荐，没有特定关键词
        # 返回最新的文档
        try:
            docs_result = db.client.table("kb_documents") \
                .select("id", "name", "file_type", "is_public", "user_id", "created_at") \
                .or_(f"is_public.eq.true,user_id.eq.{user_id}") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            result = []
            for doc in docs_result.data or []:
                # 获取该文档的第一个切片
                chunk_result = db.client.table("kb_chunks") \
                    .select("content") \
                    .eq("document_id", doc["id"]) \
                    .limit(1) \
                    .execute()
                
                content = chunk_result.data[0]["content"] if chunk_result.data else ""
                
                result.append({
                    "chunk": {"content": content, "document_id": doc["id"]},
                    "document": doc,
                    "score": 100  # 推荐模式给高分
                })
            
            chat_log(f"[KB] 推荐模式: 返回 {len(result)} 个最新文档")
            return result
            
        except Exception as e:
            chat_log(f"[KB] 推荐查询失败: {e}")
            return []
    
    # 有具体关键词的查询
    # 使用 jieba 分词，支持中英文混合
    # 例如："AI融资新闻" → ["ai", "融资", "新闻"]
    query_keywords = jieba.lcut(query_clean)
    # 过滤掉单字（通常没有意义）和停用词
    query_keywords = [w for w in query_keywords if len(w) > 1]
    
    chat_log(f"[KB] 分词结果: {query_keywords}")
    
    # 步骤2：查询所有切片，然后在代码层面过滤
    try:
        chunks_query = db.client.table("kb_chunks") \
            .select("*, kb_documents!inner(id, name, file_type, is_public, user_id)") \
            .order("created_at", desc=True) \
            .limit(200)  # 增加查询数量
        
        result = chunks_query.execute()
        all_chunks = result.data or []
        
        # 在代码层面过滤文档ID
        filtered_chunks = [chunk for chunk in all_chunks if chunk.get("document_id") in doc_ids]
        chat_log(f"[KB] 查询到 {len(filtered_chunks)} 个有权限的切片")
        
    except Exception as e:
        chat_log(f"[KB] 查询切片失败: {e}")
        return []
    
    # 智能关键词匹配
    scored_chunks = []
    
    # 增加常见AI领域关键词的同义词映射
    keyword_synonyms = {
        "ai": ["人工智能", "ai", "大模型", "机器学习", "深度学习"],
        "llm": ["llm", "大语言模型", "语言模型", "transformer"],
        "gpt": ["gpt", "chatgpt", "openai"],
        "融资": ["融资", "投资", "估值", "募资", "上市"],
        "芯片": ["芯片", "半导体", "gpu", "cpu"],
        "自动驾驶": ["自动驾驶", "智驾", "无人车"],
        "机器人": ["机器人", "具身智能", "人形机器人"],
        "量子": ["量子", "量子计算"],
        "微信": ["微信", "微信支付", "wechat"],
        "腾讯": ["腾讯", "tencent"],
        "字节": ["字节", "字节跳动", "bytedance"],
        "阿里": ["阿里", "阿里巴巴", "alibaba"],
        "百度": ["百度", "baidu"],
        "华为": ["华为", "huawei"],
        "微软": ["微软", "microsoft"],
        "谷歌": ["谷歌", "google"],
        "亚马逊": ["亚马逊", "amazon"],
        "spacex": ["spacex", "太空探索", "马斯克"],
    }
    
    for chunk in filtered_chunks:
        content = chunk.get("content", "").lower()
        doc = chunk.get("kb_documents", {})
        doc_name = doc.get("name", "").lower()
        
        # 计算匹配分数
        score = 0
        
        for keyword in query_keywords:
            # 检查同义词匹配
            matched = False
            
            # 先检查精确匹配
            if keyword in content:
                score += content.count(keyword) * 3
                matched = True
            if keyword in doc_name:
                score += 2
                matched = True
            
            # 检查同义词匹配
            for main_key, synonyms in keyword_synonyms.items():
                if keyword in synonyms:
                    for syn in synonyms:
                        if syn in content:
                            score += content.count(syn) * 2
                            matched = True
                        if syn in doc_name:
                            score += 1
                            matched = True
            
            # 如果是重要术语，额外加分
            important_terms = ["gpt", "llm", "transformer", "ai", "芯片", "融资"]
            if keyword in important_terms:
                score += 5
        
        if score > 0:
            scored_chunks.append({
                "chunk": chunk,
                "document": doc,
                "score": score
            })
    
    # 按分数排序并返回前N个结果
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    
    # 如果没有匹配结果，返回最新文档作为推荐
    if not scored_chunks:
        chat_log("[KB] 没有匹配结果，返回推荐")
        try:
            docs_result = db.client.table("kb_documents") \
                .select("id", "name", "file_type", "is_public", "user_id", "created_at") \
                .or_(f"is_public.eq.true,user_id.eq.{user_id}") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            for doc in docs_result.data or []:
                chunk_result = db.client.table("kb_chunks") \
                    .select("content") \
                    .eq("document_id", doc["id"]) \
                    .limit(1) \
                    .execute()
                
                content = chunk_result.data[0]["content"] if chunk_result.data else ""
                
                scored_chunks.append({
                    "chunk": {"content": content, "document_id": doc["id"]},
                    "document": doc,
                    "score": 50
                })
        except Exception as e:
            chat_log(f"[KB] 备用推荐失败: {e}")
    
    chat_log(f"[KB] 返回 {len(scored_chunks[:limit])} 个结果")
    return scored_chunks[:limit]


def log_chat_request(
    question_type: str,
    cache_hit: bool,
    input_tokens: int,
    output_tokens: int,
    article_id: Optional[str] = None,
    message_len: int = 0,
):
    """记录聊天请求日志到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "HIT" if cache_hit else "MISS"
    
    log_line = (
        f"[{timestamp}] [CHAT] {status} | "
        f"类型={question_type} | "
        f"文章ID={article_id or 'None'} | "
        f"输入={input_tokens} tokens | "
        f"输出={output_tokens} tokens | "
        f"消息长度={message_len}\n"
    )
    
    # 写入文件，确保日志持久化
    try:
        with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass  # 日志写入失败不阻塞
    
    # 更新统计
    chat_stats["total_requests"] += 1
    if cache_hit:
        chat_stats["cache_hits"] += 1
    else:
        chat_stats["cache_misses"] += 1
    chat_stats["total_input_tokens"] += input_tokens
    chat_stats["total_output_tokens"] += output_tokens


def normalize_question(message: str) -> str:
    """
    问题归一化处理 - 将相似问题映射到相同的标准化形式，提升缓存命中率
    
    处理步骤:
    1. 转小写
    2. 去除标点符号（保留中文标点）
    3. 去除多余空格
    4. 同义词替换
    """
    import re
    
    message_lower = message.lower().strip()
    
    # 去除英文标点
    message_lower = re.sub(r'[!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~]', '', message_lower)
    
    # 去除多余空格
    message_lower = re.sub(r'\s+', '', message_lower)
    
    # 同义词/句式归一化
    synonym_map = {
        "有什么新闻": "今日新闻",
        "今天有什么": "今日新闻",
        "最近有什么": "今日新闻",
        "最新新闻": "今日新闻",
        "今天新闻": "今日新闻",
        "今日新闻": "今日新闻",
        "新闻汇总": "今日新闻",
        "看看新闻": "今日新闻",
        "有哪些新闻": "今日新闻",
        "有什么ai新闻": "今日新闻",
        "ai新闻": "今日新闻",
        "今日ai新闻": "今日新闻",
        "今天的新闻": "今日新闻",
        "今天有什么新闻": "今日新闻",
        "最近有什么新闻": "今日新闻",
        "最新的新闻": "今日新闻",
        "你好": "问候",
        "嗨": "问候",
        "哈喽": "问候",
        "hello": "问候",
        "hi": "问候",
        "谢谢": "感谢",
        "感谢": "感谢",
        "再见": "告别",
        "拜拜": "告别",
    }
    
    # 检查是否匹配已知模式
    for pattern, normalized in synonym_map.items():
        if pattern in message_lower:
            return normalized
    
    # 如果问题很短（<=5字），直接返回作为缓存键
    if len(message_lower) <= 5:
        return message_lower
    
    # 对于较长的问题，提取关键特征作为缓存键
    # 使用前3个关键词 + 后2个关键词
    chars = list(message_lower)
    key_features = ''.join(chars[:3] + chars[-2:])
    
    return key_features


def classify_question(message: str) -> str:
    """
    分类用户问题，决定是否需要注入上下文
    
    使用配置化的意图分类器，支持：
    1. 规则 + 权重打分
    2. 置信度判断
    3. 兜底策略（不确定时返回 daily）
    
    返回值:
    - "chat": 闲聊对话，不需要上下文
    - "general": 通用知识问题，查知识库
    - "daily": 日报/新闻相关，需要注入日报上下文
    - "article": 特定文章相关，需要注入文章上下文
    - "kb": 知识库查询，需要注入知识库上下文
    """
    # 使用新的意图分类器
    result = classify_intent(message)
    
    # 如果分类器返回 None（置信度太低），默认返回 daily
    if result is None:
        return "daily"
    
    return result


class ChatRequest(BaseModel):
    message: str
    article_id: Optional[str] = None
    session_id: Optional[str] = None  # 用于保持对话上下文


class ChatResponse(BaseModel):
    reply: str
    session_id: str


SYSTEM_PROMPT = """你是一个专业的 AI 行业分析师助手，帮助用户理解 AI 行业新闻、趋势和知识库内容。

规则:
1. 你的知识截止于 2026 年初，用户提供的最新文章内容和知识库内容优先于你的训练数据
2. 不确定的具体事件请坦白说「我不确定，但根据你提供的资料...」
3. 回答简洁、准确、有深度，使用中文
4. 引用文章时使用 Markdown 链接格式：[文章标题](/?article=文章ID)
5. 引用知识库文档时使用格式：[文档名称](/knowledge?doc=文档ID)"""

KB_CONTEXT_PROMPT = """以下是知识库中的相关内容：

{kb_content}

请参考知识库内容回答用户问题。引用文档时使用格式：[文档名称](/knowledge?doc=文档ID)"""

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

请基于以上日报文章回答用户的问题。直接引用文章内容，不要说你没有最新信息。"""


@router.post("/chat", response_model=ChatResponse, tags=["AI 对话"])
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
):
    """AI 对话接口（带文章上下文和知识库支持）
    
    上下文来源（按注入顺序）：
      1. SYSTEM_PROMPT — 角色设定
      2. 当前文章（如果 article_id 有值）
      3. 今日日报文章列表（如果 article_id 为空）
      4. 知识库相关文档（智能检索）
      5. 最近 2 轮对话历史
    """
    from api.services.jwt_verify import verify_token, DEMO_USER_UUID
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI 服务未配置（缺少 DEEPSEEK_API_KEY）")

    # 认证
    raw = authorization or token
    user_id = verify_token(raw) if raw else DEMO_USER_UUID
    if not user_id:
        user_id = DEMO_USER_UUID

    session_id = req.session_id or f"session_{hash(str(req.article_id))}_{os.urandom(4).hex()}"
    
    # 分类问题（用于缓存键和日志）
    question_type = classify_question(req.message)
    
    # 问题归一化处理 - 提升缓存命中率
    normalized_message = normalize_question(req.message)
    
    # 生成缓存键（基于问题类型和归一化后的消息）
    cache_key_str = cache_key("chat", question_type, normalized_message, req.article_id)
    cache_hit = False
    input_tokens = 0
    output_tokens = 0

    # 检查缓存
    cached_result = cache.get(cache_key_str)
    if cached_result:
        cache_hit = True
        reply = cached_result
        chat_log(f"[CHAT] 缓存命中: {cache_key_str[:50]}...")
    else:
        # 构建消息上下文
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # 如果有关联文章，添加上下文（优先级最高）
        if req.article_id:
            article = db.get_article_by_id(req.article_id)
            if article:
                context = ARTICLE_CONTEXT_PROMPT.format(
                    title=article.get("title", ""),
                    source=article.get("source_name", ""),
                    summary=article.get("summary", ""),
                    tags=", ".join(article.get("tags", []) or []),
                    content=(article.get("raw_content", "") or "")[:500],  # 减少内容长度
                    article_id=article.get("id", req.article_id),
                )
                messages.append({"role": "system", "content": context})
                chat_log(f"[CHAT] 注入文章上下文: {article.get('title', '')[:30]}...")
        else:
            # 首页对话：根据问题分类决定是否注入日报上下文
            # 只有日报相关问题才注入日报上下文
            if question_type in ("daily", "article"):
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
                            article_items = flat[:3]  # 减少注入文章数量（从10篇到3篇）
                            if article_items:
                                articles_text = "\n".join([
                                    f"- [{a.get('title','')}](/?article={a.get('id','')})（来源: {a.get('source_name','')}）\n  {str(a.get('summary',''))[:100]}"
                                    for a in article_items
                                ])
                                daily_context = DAILY_CONTEXT_PROMPT.format(
                                    report_date=report_date,
                                    articles=articles_text,
                                )
                                messages.append({"role": "system", "content": daily_context})
                                chat_log(f"[CHAT] 注入日报上下文: {report_date}, {len(article_items)} 篇文章")
                            else:
                                messages.append({"role": "system", "content": f"今日日期（日报日期）: {report_date}"})
                        else:
                            messages.append({"role": "system", "content": f"今日日期（日报日期）: {report_date}"})
            else:
                chat_log(f"[CHAT] 问题类型={question_type}，跳过日报上下文注入")
        
        # ── 知识库上下文注入 ──
        # 检测知识库相关关键词（如"文档"、"知识库"、"指南"等）
        kb_keywords = ["知识库", "文档", "指南", "手册", "资料", "文档内容", "知识"]
        message_lower = req.message.lower()
        if any(keyword in message_lower for keyword in kb_keywords) or question_type == "general":
            # 搜索知识库相关内容
            kb_chunks = search_kb_chunks(req.message, user_id, limit=3)
            if kb_chunks:
                kb_parts = []
                for item in kb_chunks:
                    chunk = item["chunk"]
                    doc = item["document"]
                    kb_parts.append(
                        f"文档：{doc.get('name', '未知文档')} (ID: {doc.get('id', '')})\n"
                        f"内容：{chunk.get('content', '')[:300]}\n"
                    )
                kb_context = KB_CONTEXT_PROMPT.format(kb_content="\n".join(kb_parts))
                messages.append({"role": "system", "content": kb_context})
                chat_log(f"[CHAT] 注入知识库上下文: {len(kb_chunks)} 个相关切片")
            else:
                chat_log(f"[CHAT] 知识库检索无结果")

        # 添加历史上下文（保留最近 2 轮，减少 tokens 消耗）
        history = chat_contexts.get(session_id, [])
        history_count = min(len(history), 2)
        for h in history[-2:]:  # 从6轮减少到2轮
            messages.append(h)
        chat_log(f"[CHAT] 注入历史上下文: {history_count} 轮")

        # 加当前消息
        messages.append({"role": "user", "content": req.message})

        # 计算输入 tokens
        input_tokens = sum(count_tokens(msg["content"]) for msg in messages)
        chat_log(f"[CHAT] 输入 tokens 估算: {input_tokens}")

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
                        "temperature": 0.3,  # 低温度保证回答一致，提升缓存命中率
                        "max_tokens": 1000,  # 大部分回答 500 字以内，1000 足够
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
                
                # 获取实际消耗的 tokens（如果 API 返回）
                if "usage" in data:
                    input_tokens = data["usage"].get("prompt_tokens", input_tokens)
                    output_tokens = data["usage"].get("completion_tokens", count_tokens(reply))
                else:
                    output_tokens = count_tokens(reply)
                chat_log(f"[CHAT] API 返回 tokens - 输入: {input_tokens}, 输出: {output_tokens}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"AI 服务调用失败: {e}")

        # 保存到缓存（根据问题类型设置不同 TTL）
        ttl_map = {
            "general": 86400,  # 通用知识问题缓存1天
            "chat": 3600,      # 闲聊缓存1小时
            "daily": 3600,     # 日报问题缓存1小时（日报更新后会失效）
            "article": 1800,   # 特定文章问题缓存30分钟
        }
        ttl = ttl_map.get(question_type, 3600)
        cache.set(cache_key_str, reply, ttl)
        chat_log(f"[CHAT] 缓存已保存，TTL: {ttl}秒")

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

    # 记录日志
    log_chat_request(
        question_type=question_type,
        cache_hit=cache_hit,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        article_id=req.article_id,
        message_len=len(req.message),
    )

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
