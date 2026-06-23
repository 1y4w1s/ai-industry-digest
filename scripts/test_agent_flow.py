import sys
sys.path.insert(0, '/opt/ai-industry-digest')

import os
import httpx
from dotenv import load_dotenv
load_dotenv('/opt/ai-industry-digest/.env')

print("测试 Agent API 执行流程...")

# 步骤 1: 检查环境变量
api_key = os.getenv("DEEPSEEK_API_KEY")
print(f"1. 环境变量 - DEEPSEEK_API_KEY: {'已设置' if api_key else '未设置'}")

# 步骤 2: 测试 LLM 调用
print("\n2. 测试 LLM 调用...")
try:
    prompt = "你好，介绍一下你自己"
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 500,
            },
        )
        print(f"   LLM 响应状态: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            llm_response = data["choices"][0]["message"]["content"].strip()
            print(f"   LLM 响应: {llm_response[:50]}...")
        else:
            print(f"   LLM 调用失败: {resp.text}")
except Exception as e:
    print(f"   LLM 调用异常: {e}")

# 步骤 3: 测试 Agent 服务初始化
print("\n3. 测试 Agent 服务初始化...")
try:
    from api.services.agent import get_agent_service
    agent = get_agent_service()
    print(f"   Agent 服务初始化成功")
    print(f"   已注册工具: {[t.name for t in agent.tools]}")
except Exception as e:
    print(f"   Agent 服务初始化失败: {e}")

# 步骤 4: 测试工具调用
print("\n4. 测试工具调用...")
try:
    import asyncio
    async def test_call():
        result = await agent.call_tool('search_knowledge_base', {'query': 'test', 'user_id': 'default'})
        return result
    
    result = asyncio.run(test_call())
    print(f"   工具调用成功: {result[:50]}...")
except Exception as e:
    print(f"   工具调用失败: {e}")

# 步骤 5: 测试完整流程
print("\n5. 测试完整流程...")
try:
    from api.routes.agent_router import SYSTEM_PROMPT
    
    tools_desc = agent.get_tools_description()
    prompt = SYSTEM_PROMPT.format(tools_description=tools_desc)
    
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
                    {"role": "user", "content": "你好"}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
            },
        )
        print(f"   完整流程 LLM 响应状态: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            llm_response = data["choices"][0]["message"]["content"].strip()
            print(f"   LLM 响应: {llm_response[:100]}...")
            
            # 解析工具调用
            tool_call = agent.parse_tool_call(llm_response)
            print(f"   工具调用解析: {tool_call}")
except Exception as e:
    print(f"   完整流程失败: {e}")
    import traceback
    traceback.print_exc()