"""
Context Compression 服务：对检索结果做相关性压缩，减少 LLM token 消耗

支持三种压缩模式：
  - extract（默认）：从切片中提取与查询最相关的句子
  - summarize：调用 LLM 对所有结果生成摘要
  - truncate：简单截断（降级方案）

压缩目标：减少 40% 以上的字符/Token 数。
"""

import os
import re
import json
import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CompressionConfig:
    """Context Compression 配置"""
    max_chars: int = 1000          # 默认最大字符数
    mode: str = "extract"          # 默认模式: extract / summarize / truncate
    llm_model: str = "deepseek-chat"
    llm_timeout: float = 15.0      # LLM 调用超时（秒）
    compression_ratio: float = 0.40  # 目标压缩比


class CompressionService:
    """上下文压缩服务"""
    
    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()
    
    async def compress(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        *,
        max_chars: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> str:
        """
        压缩检索结果，保留与查询最相关的关键内容
        
        参数:
            query: 用户查询
            chunks: 检索到的切片列表（已排序，优先取前面的）
            max_chars: 压缩后的最大字符数（默认使用 config.max_chars）
            mode: 压缩模式（默认使用 config.mode）
                - "extract": 从每个切片中提取与查询相关的句子（默认）
                - "summarize": 基于所有切片生成摘要
                - "truncate": 简单截断至 max_chars
        
        返回:
            压缩后的文本字符串（长度 ≤ max_chars）
        """
        max_chars = max_chars if max_chars is not None else self.config.max_chars
        mode = mode if mode is not None else self.config.mode
        
        # 边界条件
        if not chunks or max_chars <= 0:
            return ""
        
        if not query.strip():
            raw = "".join(c["chunk"]["content"] for c in chunks)
            return raw[:max_chars]
        
        raw_text = "".join(c["chunk"]["content"] for c in chunks)
        if len(raw_text) <= max_chars:
            return raw_text
        
        # 按模式处理
        if mode == "truncate":
            return raw_text[:max_chars]
        
        if mode == "extract":
            return self._extract_mode(query, chunks, max_chars)
        
        if mode == "summarize":
            result = await self._summarize_mode(query, chunks, max_chars)
            # 如果 summarize 返回为空（LLM 调用失败），降级到 extract
            if not result:
                return self._extract_mode(query, chunks, max_chars)
            return result
        
        # 未知 mode，降级
        return raw_text[:max_chars]
    
    def _extract_mode(self, query: str, chunks: List[Dict[str, Any]], max_chars: int) -> str:
        """从切片中提取与查询最相关的句子"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # 关键术语列表（领域知识驱动）
        key_terms = [
            "大语言模型", "llm", "transformer", "rag", "检索增强",
            "神经网络", "自然语言", "微调", "fine-tuning", "gpt",
            "bert", "attention", "embedding", "token", "深度学习",
            "机器学习", "人工智能", "生成式", "预测练",
        ]
        
        # 拆分句子
        sentences = []
        for chunk_item in chunks:
            content = chunk_item["chunk"]["content"]
            parts = re.split(r"(?<=[。！？.!?])\s*", content)
            for part in parts:
                part = part.strip()
                if part:
                    sentences.append(part)
        
        if not sentences:
            return ""
        
        # 为每个句子评分
        scored_sentences = []
        for sent in sentences:
            sent_lower = sent.lower()
            sent_words = set(sent_lower.split())
            
            # 关键词重叠
            word_overlap = len(query_words & sent_words) / max(len(query_words), 1)
            
            # 关键术语命中
            term_hits = sum(1 for t in key_terms if t in sent_lower)
            term_score = min(term_hits / 2, 1.0)
            
            # 位置权重（前面的切片通常更相关）
            position_score = 0
            for i, chunk_item in enumerate(chunks):
                if sent in chunk_item["chunk"]["content"]:
                    position_score = max(0, 1.0 - i * 0.1)
                    break
            
            # 综合评分
            score = 0.35 * word_overlap + 0.45 * term_score + 0.20 * position_score
            scored_sentences.append((score, sent))
        
        # 按相关性降序排列
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        # 拼接结果，不超过 max_chars
        result = ""
        for _, sent in scored_sentences:
            if len(result) + len(sent) + 1 > max_chars:
                if not result:
                    # 连一个完整句子都放不下时，强制截断
                    result = sent[:max_chars]
                break
            if result:
                result += " "
            result += sent
        
        return result
    
    async def _summarize_mode(self, query: str, chunks: List[Dict[str, Any]], max_chars: int) -> str:
        """使用 LLM 对检索结果生成摘要"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("[Compression] 未配置 DEEPSEEK_API_KEY，降级到 extract 模式")
            return ""
        
        # 将切片内容拼接为上下文
        context_parts = []
        for i, item in enumerate(chunks[:5]):  # 最多取前 5 个切片
            context_parts.append(f"[片段 {i+1}]\n{item['chunk']['content']}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""你是一个检索结果压缩助手。请根据用户查询，从以下检索结果中提取最关键的信息。

用户查询：{query}

要求：
1. 只保留与查询高度相关的内容
2. 保持信息的准确性和完整性
3. 压缩后文本不超过 {max_chars} 个字符
4. 直接输出压缩结果，不要添加任何解释

检索结果：
{context}

压缩后的关键内容："""
        
        try:
            async with httpx.AsyncClient(timeout=self.config.llm_timeout) as client:
                resp = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.config.llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": min(max_chars * 2, 2048),
                    },
                )
                if resp.status_code == 200:
                    result = resp.json()["choices"][0]["message"]["content"].strip()
                    # 确保结果不超过 max_chars
                    if len(result) > max_chars:
                        result = result[:max_chars]
                    return result
                print(f"[Compression] LLM 调用失败: {resp.status_code}")
                return ""
        except httpx.TimeoutException:
            print(f"[Compression] LLM 调用超时（{self.config.llm_timeout}s），降级到 extract 模式")
            return ""
        except Exception as e:
            print(f"[Compression] LLM 摘要失败: {e}")
            return ""


# 单例
_compression_service = None


def get_compression_service(config: Optional[CompressionConfig] = None) -> CompressionService:
    """获取压缩服务单例"""
    global _compression_service
    if _compression_service is None:
        _compression_service = CompressionService(config or CompressionConfig())
    return _compression_service
