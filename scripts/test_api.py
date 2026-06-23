#!/usr/bin/env python3
"""测试 Agent API"""

import requests

r = requests.post('http://localhost:8000/api/agent-chat', json={'message': '测试'})
print(f'Status: {r.status_code}')
print(f'Content: {r.text}')
