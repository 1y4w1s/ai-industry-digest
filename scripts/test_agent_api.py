"""
测试 Agent 接口完整流程
"""

import sys
sys.path.insert(0, '/opt/ai-industry-digest')

import os
import httpx

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('/opt/ai-industry-digest/.env')

print("=" * 60)
print("    Agent 接口测试")
print("=" * 60)

# 1. 测试环境变量
print("\n1. 检查环境变量...")
api_key = os.getenv("DEEPSEEK_API_KEY")
if api_key:
    print(f"   ✅ DEEPSEEK_API_KEY: {api_key[:10]}...")
else:
    print("   ❌ 缺少 DEEPSEEK_API_KEY")
    sys.exit(1)

# 2. 测试 Agent 服务导入
print("\n2. 测试 Agent 服务导入...")
try:
    from api.services.agent import get_agent_service
    agent = get_agent_service()
    print(f"   ✅ Agent 服务初始化成功")
    print(f"   工具数量: {len(agent.tools)}")
except Exception as e:
    print(f"   ❌ Agent 服务初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试 LLM 调用
print("\n3. 测试 LLM 调用...")
try:
    tools_desc = agent.get_tools_description()
    prompt = f"""你是一个智能助手，拥有调用外部工具的能力。

可用工具:
{tools_desc}

你的任务:
1. 分析用户的问题
2. 如果需要调用工具才能回答，使用 <function> 标签调用合适的工具
3. 如果不需要工具，可以直接回答用户

工具调用格式:
<function name="工具名称">
{{"参数名": "参数值"}}
</function>

用户问题: 知识库中有什么内容？"""
    
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
                    {"role": "system", "content": "你是一个智能助手。"},
                    {"role": "user", "content": "知识库中有什么内容？"}
                ],
                "temperature": 0.1,
                "max_tokens": 500,
            },
        )
        print(f"   HTTP 状态码: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            llm_response = data["choices"][0]["message"]["content"].strip()
            print(f"   ✅ LLM 响应: {llm_response[:200]}...")
        else:
            print(f"   ❌ LLM 调用失败: {resp.text}")
except Exception as e:
    print(f"   ❌ LLM 调用异常: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试工具调用解析
print("\n4. 测试工具调用解析...")
test_response = '''<function name="search_knowledge_base">
{"query": "人工智能"}
</function>'''
tool_call = agent.parse_tool_call(test_response)
if tool_call:
    print(f"   ✅ 解析成功: {tool_call}")
else:
    print(f"   ❌ 解析失败")

# 5. 测试工具执行
print("\n5. 测试工具执行...")
try:
    result = agent.call_tool("search_knowledge_base", {"query": "人工智能", "user_id": "test-user-id"})
    print(f"   ✅ 工具执行结果: {result[:100]}...")
except Exception as e:
    print(f"   ❌ 工具执行失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("    测试完成")
print("=" * 60)
