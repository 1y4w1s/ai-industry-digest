import requests
import json

BASE_URL = 'http://localhost:9001/api'

print("=== Agent API 全面测试 ===\n")

# 测试 1: 基础对话
print("1. 基础对话测试（无需工具）")
r = requests.post(f'{BASE_URL}/agent-chat', json={'message': '你好'})
print(f"   状态: {r.status_code}")
data = r.json()
print(f"   回复: {data['reply'][:50]}...")
print(f"   工具: {data.get('tool_used')}")
print()

# 测试 2: 知识库搜索
print("2. 知识库搜索测试（调用工具）")
r = requests.post(f'{BASE_URL}/agent-chat', json={'message': '帮我搜索AI Agent相关资料'})
print(f"   状态: {r.status_code}")
data = r.json()
print(f"   回复: {data['reply'][:60]}...")
print(f"   工具: {data.get('tool_used')}")
print(f"   工具结果: {data.get('tool_result', '')[:50]}...")
print()

# 测试 3: 带用户 ID 的搜索
print("3. 带用户 ID 的知识库搜索")
r = requests.post(f'{BASE_URL}/agent-chat', json={'message': '搜索机器学习', 'user_id': 'test-user-123'})
print(f"   状态: {r.status_code}")
data = r.json()
print(f"   回复: {data['reply'][:60]}...")
print(f"   工具: {data.get('tool_used')}")
print(f"   Session ID: {data.get('session_id')}")
print()

print("=== 测试完成 ===")
print("✓ 如果所有测试返回 200 状态码，说明 Agent 功能正常")
