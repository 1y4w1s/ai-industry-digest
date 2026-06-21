"""
Agent 对话路由
展示如何将 Agent 集成到现有系统中
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict

from api.models.database import get_db
from api.services.agent import get_agent_service
from api.services.jwt_verify import verify_token, DEMO_USER_UUID

router = APIRouter()
db = get_db()


class AgentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_used: Optional[str] = None
    tool_result: Optional[str] = None


SYSTEM_PROMPT = """
你是一个智能助手，拥有调用外部工具的能力。

可用工具:
{tools_description}

你的任务:
1. 分析用户的问题
2. 如果需要调用工具才能回答，使用 <function> 标签调用合适的工具
3. 如果不需要工具，可以直接回答用户

工具调用格式:
<function name="工具名称">
{"参数名": "参数值"}
</function>

回答格式要求:
- 如果调用工具，只输出工具调用标签，不要输出其他内容
- 如果不调用工具，直接回答用户的问题
"""


@router.post("/agent-chat", response_model=AgentChatResponse, tags=["Agent 对话"])
async def agent_chat(
    req: AgentChatRequest,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
):
    """
    Agent 对话接口（支持工具调用）
    
    流程:
    1. 分析用户问题
    2. 决定是否调用工具
    3. 执行工具调用
    4. 总结回答
    
    可用工具:
    - search_knowledge_base: 搜索知识库
    """
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI 服务未配置")

    # 认证
    raw = authorization or token
    user_id = verify_token(raw) if raw else DEMO_USER_UUID
    if not user_id:
        user_id = DEMO_USER_UUID

    # 获取 Agent 服务
    agent = get_agent_service()
    
    # 获取工具描述
    tools_desc = agent.get_tools_description()
    
    # 构建提示词
    prompt = SYSTEM_PROMPT.format(tools_description=tools_desc)
    
    # 添加用户消息
    full_prompt = f"{prompt}\n\n用户问题: {req.message}"
    
    # 第一步：调用 LLM 判断是否需要调用工具
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
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": req.message}
                    ],
                    "temperature": 0.1,  # 低温度保证一致性
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            llm_response = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}")
    
    # 解析工具调用
    tool_call = agent.parse_tool_call(llm_response)
    
    tool_used = None
    tool_result = None
    
    if tool_call:
        # 执行工具调用
        tool_name = tool_call["tool_name"]
        parameters = tool_call["parameters"]
        
        # 添加 user_id 到参数
        if "user_id" not in parameters:
            parameters["user_id"] = user_id
        
        tool_used = tool_name
        tool_result = agent.call_tool(tool_name, parameters)
        
        # 第二步：总结回答
        summary_prompt = f"""
        用户问题: {req.message}
        
        调用的工具: {tool_name}
        工具参数: {parameters}
        工具执行结果: {tool_result}
        
        请用自然、友好的语言总结工具执行结果，回答用户的问题。
        如果工具返回了多个结果，请选择最相关的进行总结。
        """
        
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
                        "messages": [
                            {"role": "system", "content": "你是一个总结助手，帮助用户理解工具执行结果。"},
                            {"role": "user", "content": summary_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # 如果总结失败，直接返回工具结果
            reply = f"工具执行结果:\n{tool_result}"
    else:
        # 不需要调用工具，直接使用 LLM 响应
        reply = llm_response
    
    # 生成 session_id
    session_id = req.session_id or f"agent_session_{os.urandom(8).hex()}"
    
    return AgentChatResponse(
        reply=reply,
        session_id=session_id,
        tool_used=tool_used,
        tool_result=tool_result
    )
