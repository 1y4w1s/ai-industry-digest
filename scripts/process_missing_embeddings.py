"""
Embedding 批量补全脚本
检测没有 Embedding 的文档切片并批量生成

使用方法:
    python scripts/process_missing_embeddings.py
    
功能:
    1. 查找所有没有 Embedding 的文档切片
    2. 批量生成 Embedding
    3. 更新数据库
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.embedding import get_embedding_service
from api.models.database import get_db


class EmbeddingProcessor:
    """Embedding 批量处理器"""
    
    def __init__(self):
        self.db = get_db()
        self.embedding_service = get_embedding_service()
    
    async def find_chunks_without_embedding(self, limit: int = 100) -> List[Dict[str, Any]]:
        """查找没有 Embedding 的文档切片"""
        try:
            result = self.db.client.table("kb_chunks") \
                .select("id", "document_id", "content") \
                .is_("embedding", None) \
                .limit(limit) \
                .execute()
            
            return result.data or []
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        try:
            total_result = self.db.client.table("kb_chunks") \
                .select("id", count="exact") \
                .execute()
            total = total_result.count or 0
            
            with_embedding_result = self.db.client.table("kb_chunks") \
                .select("id", count="exact") \
                .not_.is_("embedding", None) \
                .execute()
            with_embedding = with_embedding_result.count or 0
            
            return {
                "total": total,
                "with_embedding": with_embedding,
                "without_embedding": total - with_embedding
            }
        except Exception as e:
            print(f"❌ 获取统计失败: {e}")
            return {"total": 0, "with_embedding": 0, "without_embedding": 0}
    
    async def batch_update_embeddings(self, chunks: List[Dict[str, Any]]) -> int:
        """批量更新 Embedding"""
        if not chunks:
            return 0
        
        print(f"  正在处理 {len(chunks)} 个切片...")
        
        # 获取内容列表
        contents = [chunk["content"] for chunk in chunks]
        
        # 批量生成 Embedding
        embeddings = await self.embedding_service.get_embeddings(contents)
        
        success_count = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding:
                try:
                    # 更新数据库
                    self.db.client.table("kb_chunks") \
                        .update({
                            "embedding": embedding
                        }) \
                        .eq("id", chunk["id"]) \
                        .execute()
                    success_count += 1
                except Exception as e:
                    print(f"    ❌ 更新失败 {chunk['id']}: {e}")
            
            # 每处理 10 个打印进度
            if (i + 1) % 10 == 0:
                print(f"    进度: {i + 1}/{len(chunks)}")
        
        return success_count
    
    async def process_all_missing(self, batch_size: int = 50, delay: float = 1.0):
        """处理所有缺失的 Embedding"""
        print("=" * 60)
        print("    Embedding 批量补全脚本")
        print("=" * 60)
        
        # 检查 API Key
        api_key = os.getenv("ALIBABA_API_KEY")
        if not api_key:
            print("❌ ALIBABA_API_KEY 未配置")
            return
        
        print("✅ API Key 已配置")
        
        # 获取初始统计
        stats = await self.get_stats()
        print(f"\n📊 初始统计:")
        print(f"  总切片数: {stats['total']}")
        print(f"  有 Embedding: {stats['with_embedding']}")
        print(f"  无 Embedding: {stats['without_embedding']}")
        
        if stats["without_embedding"] == 0:
            print("\n🎉 所有切片都已有 Embedding！")
            return
        
        print(f"\n🔄 开始批量处理...")
        
        total_processed = 0
        total_batches = (stats["without_embedding"] + batch_size - 1) // batch_size
        current_batch = 0
        
        while True:
            # 查找需要处理的切片
            chunks = await self.find_chunks_without_embedding(limit=batch_size)
            
            if not chunks:
                break
            
            current_batch += 1
            print(f"\n📦 批次 {current_batch}/{total_batches}")
            
            # 批量更新
            count = await self.batch_update_embeddings(chunks)
            total_processed += count
            
            # 更新统计
            stats = await self.get_stats()
            print(f"  已处理: {total_processed}")
            print(f"  剩余待处理: {stats['without_embedding']}")
            
            # 等待一下，避免 API 限流
            await asyncio.sleep(delay)
        
        print(f"\n🎉 处理完成！")
        print(f"总共处理了 {total_processed} 个切片")
        
        # 最终统计
        stats = await self.get_stats()
        print(f"\n📊 最终统计:")
        print(f"  总切片数: {stats['total']}")
        print(f"  有 Embedding: {stats['with_embedding']}")
        print(f"  覆盖率: {(stats['with_embedding'] / max(stats['total'], 1)) * 100:.1f}%")


if __name__ == "__main__":
    processor = EmbeddingProcessor()
    asyncio.run(processor.process_all_missing())