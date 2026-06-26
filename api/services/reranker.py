"""
Re-ranker 服务：使用 Cross-encoder 对检索结果做二次精排

使用 sentence-transformers 的 Cross-encoder 模型，
对候选切片进行更精确的相关性评分，改善 RRF 粗排后的排序质量。

默认模型：cross-encoder/ms-marco-MiniLM-L-6-v2（~80MB，适合 CPU 推理）
降级方案：模型不可用时使用关键词 + 术语匹配的轻量评分
"""

import os
import time
import asyncio
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass


@dataclass
class RerankerConfig:
    """Re-ranker 配置"""
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    timeout: float = 2.0           # 单次推理超时（秒）
    batch_size: int = 8            # 批处理大小
    top_k: int = 5                 # 返回 TopN 结果
    device: str = "cpu"            # 推理设备
    fallback_on_timeout: bool = True  # 超时后降级
    force_fallback: bool = False   # 强制使用降级方案（测试用）


class RerankerService:
    """Cross-encoder 精排服务"""
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()
        self._model = None
        self._model_loaded = False
        self._load_error = None
    
    def _load_model(self):
        """懒加载 Cross-encoder 模型"""
        if self._model_loaded:
            return True
        if self._load_error:
            return False
        if self.config.force_fallback:
            self._load_error = "force_fallback"
            return False
        
        try:
            from sentence_transformers import CrossEncoder
            print(f"[Re-ranker] 加载模型: {self.config.model_name}")
            self._model = CrossEncoder(
                self.config.model_name,
                device=self.config.device,
                max_length=512,
            )
            self._model_loaded = True
            print(f"[Re-ranker] 模型加载完成")
            return True
        except Exception as e:
            self._load_error = str(e)
            print(f"[Re-ranker] 模型加载失败（将使用降级评分）: {e}")
            return False
    
    async def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        *,
        top_k: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        对检索结果做二次精排
        
        参数:
            query: 用户查询
            chunks: 候选切片列表，每个元素包含 chunk/document 字段
            top_k: 返回结果数（默认使用 config.top_k）
            timeout: 超时时间（秒，默认使用 config.timeout）
        
        返回:
            精排后的结果列表（按 re_score 从高到低），每个元素增加 re_score 字段
        
        异常处理:
            - 模型未加载：使用轻量评分作为降级
            - 超时：按原有 fused_score 排序返回
            - 空输入或单元素：直接返回
        """
        top_k = top_k if top_k is not None else self.config.top_k
        timeout = timeout if timeout is not None else self.config.timeout
        
        if not chunks:
            return []
        
        if len(chunks) == 1:
            chunks[0]["re_score"] = chunks[0].get("fused_score", chunks[0].get("score", 0))
            return chunks
        
        # 尝试加载模型（如果尚未加载）
        model_available = self._load_model()
        
        if model_available:
            try:
                return await self._rerank_with_model(query, chunks, top_k, timeout)
            except asyncio.TimeoutError:
                print(f"[Re-ranker] 超时（{timeout}s），降级为原始排序")
                return self._fallback_rerank(query, chunks, top_k)
            except Exception as e:
                print(f"[Re-ranker] 推理失败: {e}，降级为轻量评分")
                return self._fallback_rerank(query, chunks, top_k)
        else:
            return self._fallback_rerank(query, chunks, top_k)
    
    async def _rerank_with_model(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int,
        timeout: float,
    ) -> List[Dict[str, Any]]:
        """使用 Cross-encoder 模型做精排"""
        loop = asyncio.get_running_loop()
        
        # 1. 构建 (query, passage) 对
        pairs = [(query, item["chunk"]["content"]) for item in chunks]
        
        # 2. 在线程池中运行模型推理（避免阻塞事件循环）
        def predict():
            self._model.max_length = 512
            scores = self._model.predict(
                pairs,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
            )
            return scores
        
        # 3. 带超时的异步执行
        scores = await asyncio.wait_for(
            loop.run_in_executor(None, predict),
            timeout=timeout,
        )
        
        # 4. 处理预测结果
        if hasattr(scores, 'tolist'):
            scores = scores.tolist()
        
        scores_list = list(scores) if isinstance(scores, (list, tuple)) else [scores[0]]
        
        # 5. 将 Cross-encoder 分数映射到 [0, 1] 范围
        # Cross-encoder 通常输出 sigmoid 之前的 logits，范围不定
        # 这里用 sigmoid-like 映射：1 / (1 + exp(-score))
        import math
        scored = []
        for item, raw_score in zip(chunks, scores_list):
            if isinstance(raw_score, (list, tuple)):
                raw_score = raw_score[0]
            re_score = 1.0 / (1.0 + math.exp(-float(raw_score)))
            item["re_score"] = re_score
            item["re_raw_score"] = float(raw_score)
            scored.append(item)
        
        scored.sort(key=lambda x: x["re_score"], reverse=True)
        return scored[:top_k]
    
    def _fallback_rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        降级精排：使用关键词 + 关键术语匹配的轻量评分
        
        当 Cross-encoder 模型不可用或超时时使用。
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # 关键术语列表（可根据业务扩展）
        key_terms = [
            "大语言模型", "llm", "transformer", "神经网络", "自然语言",
            "机器学习", "深度学习", "人工智能", "rag", "检索增强",
            "gpt", "bert", "attention", "embedding", "token",
        ]
        
        scored = []
        for item in chunks:
            content_lower = item["chunk"]["content"].lower()
            
            # 关键词重叠比例
            content_words = set(content_lower.split())
            word_overlap = len(query_words & content_words) / max(len(query_words), 1) if query_words else 0.5
            
            # 关键术语命中
            term_hits = sum(1 for term in key_terms if term in content_lower)
            term_score = min(term_hits / 3, 1.0)
            
            # 加权融合（模拟 Cross-encoder 的语义匹配效果）
            relevance = 0.4 * word_overlap + 0.6 * term_score
            relevance = max(0.0, min(1.0, relevance))
            
            item["re_score"] = relevance
            scored.append(item)
        
        scored.sort(key=lambda x: x["re_score"], reverse=True)
        return scored[:top_k]


# 单例
_reranker_service = None


def get_reranker_service(config: Optional[RerankerConfig] = None) -> RerankerService:
    """获取 Re-ranker 服务单例"""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = RerankerService(config or RerankerConfig())
    return _reranker_service
