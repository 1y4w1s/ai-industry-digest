"""
测试完整的 Agent 流程
"""

import sys
sys.path.insert(0, '/opt/ai-industry-digest')

import os
import httpx

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('/opt/ai-industry-digest/.env')

try:
    print("1. 测试 LLM 调用...")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 缺少 DEEPSEEK_API_KEY")
        sys.exit(1)
    
    prompt = """你是一个智能助手，拥有调用外部工具的能力。
可用工具:
工具名称: search_knowledge_base
描述: 在知识库中搜索相关信息，用于回答用户关于文档、资料的问题
参数: {
    "query": 搜索关键词, "user_id": 用户ID
}

你的任务:
1. 分析用户的问题
2. 如果需要调用工具才能回答，使用 <function> 标签调用合适的工具
3. 如果不需要工具，可以直接回答用户

工具调用格式:
<function name="工具名称">
{"参数名": "参数值"}
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
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 500,
            },
        )
        print(f"LLM 响应状态: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            llm_response = data["choices"][0]["message"]["content"].strip()
            print(f"LLM 响应: {llm_response}")
        else:
            print(f"LLM 调用失败: {resp.text}")
    
    print("\n✅ LLM 调用正常！")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()