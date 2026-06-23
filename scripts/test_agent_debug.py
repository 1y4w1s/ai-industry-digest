import sys
sys.path.insert(0, '/opt/ai-industry-digest')

import os
import asyncio
from dotenv import load_dotenv
load_dotenv('/opt/ai-industry-digest/.env')

async def main():
    print("测试 Agent 服务初始化...")
    try:
        from api.services.agent import get_agent_service
        
        agent = get_agent_service()
        print(f"✓ Agent 服务初始化成功")
        print(f"  已注册工具: {[t.name for t in agent.tools]}")
        
        # 测试工具描述
        desc = agent.get_tools_description()
        print(f"✓ 工具描述获取成功")
        
        # 测试解析工具调用
        llm_response = '''为了了解知识库中具体包含哪些内容，我需要先搜索一下相关信息。

<function name="search_knowledge_base">
{"query": "知识库内容概述", "user_id": "default"}
</function>'''
        
        tool_call = agent.parse_tool_call(llm_response)
        print(f"✓ 工具调用解析成功: {tool_call}")
        
        # 测试异步工具调用
        print("\n测试工具调用...")
        result = await agent.call_tool('search_knowledge_base', {'query': 'test', 'user_id': 'default'})
        print(f"✓ 工具调用成功: {result[:50]}...")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())