"""
Agent 演示脚本
展示如何使用 Agent 服务
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.agent import get_agent_service


def get_weather(city: str) -> str:
    """获取天气信息（模拟）"""
    weather_data = {
        "北京": "晴天，温度 25°C，湿度 40%",
        "上海": "多云，温度 28°C，湿度 60%",
        "广州": "雨天，温度 30°C，湿度 80%",
        "深圳": "阴天，温度 27°C，湿度 70%"
    }
    return weather_data.get(city, f"未找到 {city} 的天气信息")


def search_knowledge(query: str) -> str:
    """搜索知识库（模拟）"""
    knowledge_base = {
        "人工智能": "人工智能（AI）是计算机科学的一个分支，致力于研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。",
        "机器学习": "机器学习是人工智能的核心，是一门让计算机从数据中学习模式并做出预测的学科。",
        "深度学习": "深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。",
        "RAG": "检索增强生成（RAG）是一种AI技术，通过检索外部知识库来增强生成模型的回答能力。"
    }
    
    for key, value in knowledge_base.items():
        if key in query:
            return value
    
    return f"知识库中未找到关于 '{query}' 的信息"


def calculate(expression: str) -> str:
    """简单计算器"""
    try:
        allowed_chars = "0123456789+-*/(). "
        for char in expression:
            if char not in allowed_chars:
                return "不支持的运算符"
        
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


def main():
    """主函数"""
    print("=" * 60)
    print("    Agent 演示")
    print("=" * 60)
    
    agent = get_agent_service()
    
    agent.register_tool(
        name="get_weather",
        description="获取指定城市的天气信息",
        parameters={"city": {"type": "string", "description": "城市名称"}},
        func=get_weather
    )
    
    agent.register_tool(
        name="search_knowledge",
        description="在知识库中搜索相关信息",
        parameters={"query": {"type": "string", "description": "搜索关键词"}},
        func=search_knowledge
    )
    
    agent.register_tool(
        name="calculate",
        description="进行数学计算",
        parameters={"expression": {"type": "string", "description": "数学表达式"}},
        func=calculate
    )
    
    print("\n--- 测试工具调用 ---")
    
    print("\n1. 测试 get_weather 工具")
    result = agent.call_tool("get_weather", {"city": "北京"})
    print(f"   结果: {result}")
    
    print("\n2. 测试 search_knowledge 工具")
    result = agent.call_tool("search_knowledge", {"query": "人工智能"})
    print(f"   结果: {result[:50]}...")
    
    print("\n3. 测试 calculate 工具")
    result = agent.call_tool("calculate", {"expression": "2 + 3 * 4"})
    print(f"   结果: {result}")
    
    print("\n--- 工具列表 ---")
    print(agent.get_tools_description())


if __name__ == "__main__":
    main()
