import requests

print("=== 测试优化后的 Agent 回答风格 ===\n")

BASE_URL = 'http://localhost:9001/api'

# 测试 1：基础对话（看语气是否更友好）
print("1. 测试基础对话（应该更友好）")
r = requests.post(f'{BASE_URL}/agent-chat', json={'message': '你好'})
print(f"   回复: {r.json()['reply']}\n")

# 测试 2：知识库搜索（空结果）
print("2. 测试知识库搜索（空结果处理）")
r = requests.post(f'{BASE_URL}/agent-chat', json={'message': '搜索一个不存在的关键词xyzabc123'})
print(f"   回复: {r.json()['reply']}")
print(f"   工具: {r.json().get('tool_used')}")
print(f"   工具结果: {r.json().get('tool_result', '')}\n")

# 测试 3：知识库搜索（正常查询）
print("3. 测试知识库搜索（正常查询）")
r = requests.post(f'{BASE_URL}/agent-chat', json={'message': '搜索AI相关资料'})
print(f"   回复: {r.json()['reply']}")
print(f"   工具: {r.json().get('tool_used')}")
