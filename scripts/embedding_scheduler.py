"""
APScheduler 定时任务：批量处理未生成 Embedding 的文档切片

使用方法：
    python scripts/embedding_scheduler.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置参数
BATCH_SIZE = 100
MAX_BATCHES = 100
DELAY_BETWEEN_BATCH = 1.0


def process_missing_embeddings():
    """
    主处理函数
    """
    from api.services.embedding import get_embedding_service
    from api.models.database import get_db
    
    logger.info("=" * 60)
    logger.info(f"开始执行 Embedding 批量处理任务 - {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        db = get_db()
        embedding_service = get_embedding_service()
        
        total_processed = 0
        total_failed = 0
        
        for batch_num in range(MAX_BATCHES):
            # 1. 查询未处理的切片
            chunks = db.client.table("kb_chunks") \
                .select("id", "document_id", "content") \
                .is_("embedding", None) \
                .limit(BATCH_SIZE) \
                .execute()
            
            if not chunks.data:
                logger.info(f"没有更多未处理的切片，任务完成")
                break
            
            chunk_list = chunks.data
            logger.info(f"批次 {batch_num + 1}: 处理 {len(chunk_list)} 个切片")
            
            # 2. 批量生成 Embedding（同步版本）
            contents = [chunk["content"] for chunk in chunk_list]
            embeddings = embedding_service.get_embeddings_sync(contents)
            
            # 3. 更新数据库
            success_count = 0
            for chunk, embedding in zip(chunk_list, embeddings):
                if embedding:
                    try:
                        db.client.table("kb_chunks") \
                            .update({"embedding": embedding}) \
                            .eq("id", chunk["id"]) \
                            .execute()
                        success_count += 1
                    except Exception as e:
                        logger.error(f"更新失败 {chunk['id']}: {e}")
                        total_failed += 1
            
            total_processed += success_count
            logger.info(f"批次 {batch_num + 1} 完成: 成功 {success_count}/{len(chunk_list)}")
            
            # 批次间延迟
            import time
            time.sleep(DELAY_BETWEEN_BATCH)
        
        logger.info("=" * 60)
        logger.info(f"任务完成: 成功 {total_processed} 个, 失败 {total_failed} 个")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")


def main():
    """主函数"""
    logger.info("启动 Embedding 定时任务调度器")
    
    scheduler = BlockingScheduler()
    
    # 每 24 小时执行一次
    scheduler.add_job(
        process_missing_embeddings,
        trigger=IntervalTrigger(hours=24),
        id='embedding_processor',
        name='Embedding 批量处理器',
        replace_existing=True,
        next_run_time=datetime.now()  # 立即执行一次
    )
    
    logger.info("调度器已启动，下次执行时间将自动计算")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器已停止")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
