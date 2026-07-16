# -*- coding: utf-8 -*-
import base64, json, urllib.request

with open('D:\\MyPrograms\\ai-industry-digest\\screenshot_current.png', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

body = {
    "model": "zai-org/glm-4.6v-flash",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "你是一个极其严苛的专业前端平面UI/UX设计师。请分析这个AI日报网站的首页截图，找出所有视觉和布局问题。严格要求自己，不能放过任何一个细节问题。请从以下几个维度分析：\n\n1. 信息层级\n2. 间距与留白\n3. 色彩与对比度\n4. 对齐与一致性\n5. 移动端底部导航\n6. 侧栏金色高亮\n\n列出至少5个具体问题，按严重程度排序（高/中/低）。"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]
    }],
    "max_tokens": 2000
}

req = urllib.request.Request(
    "http://localhost:1234/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        r = json.loads(resp.read())
        print(r["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error: {e}")
