import os
import sys

# 检查环境变量
print("检查环境变量...")
api_key = os.getenv("DEEPSEEK_API_KEY")
print(f"DEEPSEEK_API_KEY: {'已设置' if api_key else '未设置'}")

# 测试导入
print("\n测试导入...")
try:
    from api.services.agent import get_agent_service
    print("✓ agent 模块导入成功")
    
    # 初始化 Agent 服务
    print("\n初始化 Agent 服务...")
    agent = get_agent_service()
    print(f"✓ Agent 服务初始化成功，已注册工具数: {len(agent.tools)}")
    
    # 测试工具描述
    desc = agent.get_tools_description()
    print(f"工具描述: {desc[:100]}...")
    
except Exception as e:
    print(f"✗ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
