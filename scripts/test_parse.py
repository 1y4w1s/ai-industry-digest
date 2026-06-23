import json

# 测试解析工具调用
response = '<function name="search_knowledge_base">\n{"query": "AI"}\n</function>'
print(f"原始响应: {repr(response)}")

try:
    # 查找函数调用标记
    start_tag = response.find('<function name="')
    print(f"start_tag: {start_tag}")
    
    end_tag = response.find('</function>')
    print(f"end_tag: {end_tag}")
    
    # 提取工具名称
    name_start = start_tag + len('<function name="')
    name_end = response.find('">', name_start)
    print(f"name_start: {name_start}, name_end: {name_end}")
    tool_name = response[name_start:name_end]
    print(f"tool_name: {tool_name}")
    
    # 提取参数
    params_start = response.find('>', name_end + 2) + 1
    print(f"params_start: {params_start}")
    params_str = response[params_start:end_tag].strip()
    print(f"params_str: {repr(params_str)}")
    
    # 解析 JSON 参数
    params = json.loads(params_str)
    print(f"params: {params}")
    
    result = {
        "tool_name": tool_name,
        "parameters": params
    }
    print(f"解析结果: {result}")
    
except Exception as e:
    print(f"解析失败: {e}")
    import traceback
    traceback.print_exc()