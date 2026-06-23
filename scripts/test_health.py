import requests
import json

# 测试简单对话
print("测试 1: 简单对话")
try:
    r = requests.post('http://localhost:8082/api/agent-chat', json={'message': '你好，介绍一下你自己'})
    print(f'Status: {r.status_code}')
    print(f'Full Response: {r.text}')
    
    # 尝试解析 JSON
    try:
        data = r.json()
        print(f'JSON Response: {data}')
    except:
        print('Not JSON response')
        
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()

# 测试健康检查
print("\n测试 3: 健康检查")
try:
    r = requests.get('http://localhost:8082/health')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')
except Exception as e:
    print(f'Exception: {e}')
