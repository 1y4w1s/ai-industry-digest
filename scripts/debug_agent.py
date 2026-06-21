"""
Agent 调试脚本
"""

import sys
sys.path.insert(0, '/opt/ai-industry-digest')

try:
    print("1. 导入 Agent 服务...")
    from api.services.agent import get_agent_service
    
    print("2. 获取 Agent 服务...")
    agent = get_agent_service()
    
    print("3. 获取工具列表...")
    tools = agent.get_tools_description()
    print(f"工具列表:\n{tools}")
    
    print("4. 测试工具调用...")
    result = agent.call_tool("search_knowledge_base", {"query": "人工智能", "user_id": "test"})
    print(f"工具调用结果: {result}")
    
    print("\n✅ Agent 服务正常！")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()