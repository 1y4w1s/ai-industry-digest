import requests
import json

# 测试简单对话
print("测试 Agent API...")
try:
    r = requests.post('http://localhost:9000/api/agent-chat', json={'message': '你好'})
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type")}')
    print(f'Full Response: {r.text}')
    
    # 尝试解析为 JSON
    try:
        data = r.json()
        print(f'JSON: {data}')
    except:
        print('Not JSON')
        
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()

# 测试健康检查
print("\n测试健康检查...")
try:
    r = requests.get('http://localhost:9000/health')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')
except Exception as e:
    print(f'Exception: {e}')

# 测试其他 API
print("\n测试 Reports API...")
try:
    r = requests.get('http://localhost:9000/api/reports')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:200]}')
except Exception as e:
    print(f'Exception: {e}')
