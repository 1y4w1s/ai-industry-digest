import requests

# 测试知识库搜索
r = requests.post('http://localhost:9001/api/agent-chat', json={'message': '帮我搜索关于AI的资料'})
print('Status:', r.status_code)
print('Response:', r.text)