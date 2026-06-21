"""
Embedding 服务 - 使用阿里云通义千问 API
"""

import os
import httpx
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Embedding 服务"""

    def __init__(self):
        self.api_key = os.getenv("ALIBABA_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        self.model = "text-embedding-v3"
        
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取单个文本的向量

        参数:
            text: 要获取向量的文本

        返回:
            向量列表(1536维),失败返回 None
        """
        if not self.api_key:
            logger.error("阿里云通义千问 API 密钥未配置")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": {
                            "texts": [text]
                        },
                        "parameters": {
                            "text_type": "document"  # 文档类型
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data["output"]["embeddings"][0]["embedding"]
                    logger.info(f"Embedding 生成成功, 维度: {len(embedding)}")
                    return embedding
                else:
                    logger.error(f"Embedding API 错误: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"Embedding 生成失败: {e}")
            return None
    
    async def get_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量获取文本向量

        参数:
            texts: 文本列表

        返回:
            向量列表列表
        """
        if not self.api_key:
            logger.error("ALIBABA_API_KEY 未配置")
            return [None] * len(texts)
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": {
                            "texts": texts
                        },
                        "parameters": {
                            "text_type": "document"  # 文档类型
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embeddings = [item["embedding"] for item in data["output"]["embeddings"]]
                    logger.info(f"批量 Embedding 生成成功, 数量: {len(embeddings)}")
                    return embeddings
                else:
                    logger.error(f"Embedding API 错误: {response.status_code} - {response.text}")
                    return [None] * len(texts)
                
        except Exception as e:
            logger.error(f"批量 Embedding 生成失败: {e}")
            return [None] * len(texts)
        
# 单例
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """获取 Embedding 服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
