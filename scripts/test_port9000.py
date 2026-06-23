import requests

# 测试简单对话
r = requests.post('http://localhost:9000/api/agent-chat', json={'message': '你好，介绍一下你自己'})
print('Status:', r.status_code)
print('Response:', r.text[:500])