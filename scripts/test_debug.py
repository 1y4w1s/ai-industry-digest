import requests
import json

# 测试简单对话
print("测试 1: 简单对话")
try:
    r = requests.post('http://localhost:8081/api/agent-chat', json={'message': '你好，介绍一下你自己'})
    print(f'Status: {r.status_code}')
    print(f'Headers: {dict(r.headers) if r.headers else "None"}')
    print(f'Response: {r.text}')
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()

# 测试知识库搜索
print("\n测试 2: 知识库搜索")
try:
    r = requests.post('http://localhost:8081/api/agent-chat', json={'message': '帮我搜索关于AI的资料'})
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')
except Exception as e:
    print(f'Exception: {e}')
