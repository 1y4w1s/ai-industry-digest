"""
Agent 服务
实现 AI Agent 功能，支持工具调用
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Callable


class ToolDefinition:
    """工具定义"""
    
    def __init__(self, name: str, description: str, parameters: Dict, func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
    
    def to_dict(self) -> Dict:
        """转换为字典格式，用于传递给 LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class AgentService:
    """AI Agent 服务"""
    
    def __init__(self):
        self.tools: List[ToolDefinition] = []
        self._initialize_default_tools()
        
    def _initialize_default_tools(self):
        """初始化默认工具"""
        try:
            def search_knowledge_base(query: str, user_id: str = "default") -> str:
                """搜索知识库"""
                try:
                    from api.services.retrieval import get_retrieval_service
                    retrieval_service = get_retrieval_service()
                    results = asyncio.run(retrieval_service.search(query, user_id, limit=3))
                    if results:
                        summaries = []
                        for i, result in enumerate(results[:3], 1):
                            content = result.get("chunk", {}).get("content", "")[:100]
                            doc_name = result.get("document", {}).get("name", "")
                            summaries.append(f"{i}. [{doc_name}] {content}...")
                        return "\n".join(summaries)
                    return "知识库中未找到相关信息"
                except Exception as e:
                    return f"搜索失败: {e}"
            
            self.register_tool(
                name="search_knowledge_base",
                description="在知识库中搜索相关信息，用于回答用户关于文档、资料的问题",
                parameters={
                    "query": {"type": "string", "description": "搜索关键词"},
                    "user_id": {"type": "string", "description": "用户ID，可选，默认为default"}
                },
                func=search_knowledge_base
            )
            
        except Exception as e:
            print(f"[Agent] 初始化默认工具失败: {e}")
    
    def get_tools_description(self) -> str:
        """获取所有工具的描述（用于提示词）"""
        if not self.tools:
            return "无可用工具"
        
        tools_desc = []
        for tool in self.tools:
            params_desc = []
            for param_name, param_info in tool.parameters.items():
                params_desc.append(f'"{param_name}": {param_info["description"]}')
            
            tools_desc.append(f"""
工具名称: {tool.name}
描述: {tool.description}
参数: {{
    {", ".join(params_desc)}
}}
""")
        
        return "\n".join(tools_desc)
    
    def parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 响应中的工具调用
        
        期望格式:
        <function name="工具名称">
        {"参数": "值"}
        </function>
        """
        try:
            # 查找函数调用标记
            start_tag = response.find('<function name="')
            if start_tag == -1:
                return None
            
            end_tag = response.find('</function>')
            if end_tag == -1:
                return None
            
            # 提取工具名称
            name_start = start_tag + len('<function name="')
            name_end = response.find('">', name_start)
            tool_name = response[name_start:name_end]
            
            # 提取参数
            params_start = response.find('>', name_end + 2) + 1
            params_str = response[params_start:end_tag].strip()
            
            # 解析 JSON 参数
            params = json.loads(params_str)
            
            return {
                "tool_name": tool_name,
                "parameters": params
            }
        
        except Exception as e:
            print(f"[Agent] 解析工具调用失败: {e}")
            return None
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """调用指定工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    result = tool.func(**parameters)
                    print(f"[Agent] 工具 {tool_name} 调用成功")
                    return result
                except Exception as e:
                    print(f"[Agent] 工具 {tool_name} 调用失败: {e}")
                    return f"工具调用失败: {e}"
        
        return f"未找到工具: {tool_name}"
    
    def run(self, user_query: str, llm_service) -> str:
        """
        执行 Agent 推理流程
        
        流程:
        1. 构建包含工具信息的提示词
        2. 调用 LLM 获取响应
        3. 解析是否需要调用工具
        4. 执行工具调用
        5. 总结回答
        """
        print(f"[Agent] 用户查询: {user_query}")
        
        # 1. 构建提示词
        prompt = self._build_prompt(user_query)
        
        # 2. 调用 LLM
        response = llm_service.call_llm(prompt, model="deepseek-chat")
        print(f"[Agent] LLM 响应: {response}")
        
        # 3. 解析工具调用
        tool_call = self.parse_tool_call(response)
        
        if tool_call:
            # 4. 执行工具调用
            tool_name = tool_call["tool_name"]
            parameters = tool_call["parameters"]
            
            print(f"[Agent] 调用工具: {tool_name}, 参数: {parameters}")
            
            tool_result = self.call_tool(tool_name, parameters)
            
            # 5. 总结回答
            summary_prompt = self._build_summary_prompt(user_query, tool_name, parameters, tool_result)
            final_response = llm_service.call_llm(summary_prompt, model="deepseek-chat")
            
            return final_response
        
        # 不需要调用工具，直接返回响应
        return response
    
    def _build_prompt(self, user_query: str) -> str:
        """构建包含工具信息的提示词"""
        tools_desc = self.get_tools_description()
        
        prompt = f"""
你是一个智能助手，拥有调用外部工具的能力。

可用工具列表:
{tools_desc}

你的任务:
1. 分析用户的问题
2. 如果需要调用工具才能回答，使用 <function> 标签调用合适的工具
3. 如果不需要工具，可以直接回答用户

工具调用格式:
<function name="工具名称">
{{
    "参数名": "参数值"
}}
</function>

用户问题: {user_query}
"""
        return prompt
    
    def _build_summary_prompt(self, user_query: str, tool_name: str, 
                              parameters: Dict, tool_result: Any) -> str:
        """构建总结提示词"""
        prompt = f"""
你是一个智能助手，需要根据工具执行结果总结回答用户的问题。

用户问题: {user_query}

调用的工具: {tool_name}
工具参数: {parameters}
工具执行结果: {tool_result}

请用自然、友好的语言总结工具执行结果，回答用户的问题。
"""
        return prompt


# 单例
_agent_service = None

def get_agent_service() -> AgentService:
    """获取 Agent 服务单例"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
