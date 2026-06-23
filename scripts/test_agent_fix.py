#!/usr/bin/env python3
"""测试 Agent API 修复"""
import requests
import json

def test_agent_chat():
    """测试 Agent 对话接口"""
    url = "http://localhost:8000/api/agent-chat"

    # 测试 1: 简单对话（不需要工具）
    print("=" * 50)
    print("测试 1: 简单对话")
    print("=" * 50)
    try:
        r = requests.post(url, json={"message": "你好，介绍一下你自己"}, timeout=30)
        print(f"状态码: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"回复: {data['reply'][:100]}...")
            print(f"使用工具: {data.get('tool_used')}")
        else:
            print(f"错误: {r.text}")
    except Exception as e:
        print(f"请求失败: {e}")

    # 测试 2: 需要搜索知识库的问题
    print("\n" + "=" * 50)
    print("测试 2: 知识库搜索")
    print("=" * 50)
    try:
        r = requests.post(url, json={"message": "帮我搜索关于 AI 的资料"}, timeout=60)
        print(f"状态码: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"回复: {data['reply'][:100]}...")
            print(f"使用工具: {data.get('tool_used')}")
            print(f"工具结果: {data.get('tool_result', '')[:100]}...")
        else:
            print(f"错误: {r.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_agent_chat()
