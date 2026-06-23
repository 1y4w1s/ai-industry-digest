import requests
import json

# 测试简单对话
print("测试 1: 简单对话")
try:
    r = requests.post('http://localhost:8000/api/agent-chat', json={'message': '你好，介绍一下你自己'})
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Reply: {data.get("reply", "")[:100]}')
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'Exception: {e}')

# 测试知识库搜索
print("\n测试 2: 知识库搜索")
try:
    r = requests.post('http://localhost:8000/api/agent-chat', json={'message': '帮我搜索关于AI的资料'})
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print(f'Reply: {data.get("reply", "")[:100]}')
        print(f'Tool Used: {data.get("tool_used")}')
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'Exception: {e}')
