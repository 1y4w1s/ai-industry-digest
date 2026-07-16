# -*- coding: utf-8 -*-
import urllib.request, json, base64

with open('D:\\MyPrograms\\ai-industry-digest\\screenshot_current.png', 'rb') as f:
    img = base64.b64encode(f.read()).decode()

body = {
    "model": "zai-org/glm-4.6v-flash",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "你是一个极其严苛的专业前端平面UI/UX设计师。请分析这个AI日报网站首页截图。找出所有视觉和布局问题，不要只说好话。\n\n从以下维度严格审查：\n1. 信息层级是否清晰\n2. 间距留白是否协调\n3. 金色对比度是否达标\n4. 元素对齐是否精确\n5. 移动端底部导航\n6. 侧栏金色高亮\n\n按高中低列出具体问题。"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
        ]
    }],
    "max_tokens": 1500
}

req = urllib.request.Request(
    "http://localhost:1234/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        r = json.loads(resp.read())
        print(r["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Vision Error: {e}")
