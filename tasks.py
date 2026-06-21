"""
定时任务：批量处理未生成 Embedding 的文档切片

使用方法：
    celery -A tasks beat --loglevel=info    # 启动调度器
    celery -A tasks worker --loglevel=info # 启动 worker
"""

import os
import sys
from datetime import datetime
from celery import Celery

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Celery 配置
app = Celery(
    'embedding_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# 配置
app.conf.update(
    timezone='Asia/Shanghai',  # 使用中国时区
    enable_utc=True,
    
    # 定时任务配置
    beat_schedule={
        'process-missing-embeddings-every-6-hours': {
            'task': 'tasks.process_missing_embeddings',
            'schedule': 21600.0,  # 每 6 小时执行一次
            'options': {
                'queue': 'embedding_queue',
            }
        },
    },
    
    # 任务配置
    task_acks_late=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    task_time_limit=7200,  # 任务最多运行 2 小时
)


@app.task(bind=True, max_retries=3)
def process_missing_embeddings(self):
    """
    处理未生成 Embedding 的文档切片
    
    策略：
    1. 每次处理固定数量（避免单次运行时间过长）
    2. 自动重试失败的批次
    3. 记录处理日志
    """
    from api.services.embedding import get_embeddings_sync
    from api.models.database import get_db
    
    logger = self.get_logger()
    
    logger.info("=" * 60)
    logger.info("开始执行 Embedding 批量处理任务")
    logger.info("=" * 60)
    
    # 初始化服务
    db = get_db()
    
    # 配置参数
    BATCH_SIZE = 100       # 每批处理数量
    MAX_BATCHES = 100      # 每次任务最多处理批次
    DELAY_BETWEEN_BATCH = 1.0  # 批次间延迟（秒）
    
    total_processed = 0
    total_failed = 0
    
    for batch_num in range(MAX_BATCHES):
        try:
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
            
            # 2. 批量生成 Embedding（使用同步版本）
            contents = [chunk["content"] for chunk in chunk_list]
            embeddings = get_embeddings_sync(contents)
            
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
            
        except Exception as e:
            logger.error(f"批次 {batch_num + 1} 执行失败: {e}")
            # 自动重试
            raise self.retry(exc=e)
    
    # 记录处理结果
    logger.info("=" * 60)
    logger.info(f"Embedding 批量处理任务完成")
    logger.info(f"成功处理: {total_processed} 个")
    logger.info(f"失败: {total_failed} 个")
    logger.info("=" * 60)
    
    return {
        "total_processed": total_processed,
        "total_failed": total_failed,
        "timestamp": datetime.now().isoformat()
    }


@app.task
def process_single_document(document_id: str):
    """
    处理单个文档的所有切片（实时触发）
    
    当用户上传新文档时，自动调用此任务
    """
    from api.services.embedding import get_embedding_service
    from api.models.database import get_db
    
    db = get_db()
    embedding_service = get_embedding_service()
    
    # 查询该文档的所有未处理切片
    chunks = db.client.table("kb_chunks") \
        .select("id", "content") \
        .eq("document_id", document_id) \
        .is_("embedding", None) \
        .execute()
    
    if not chunks.data:
        return {"status": "no_pending_chunks", "document_id": document_id}
    
    processed = 0
    for chunk in chunks.data:
        embedding = embedding_service.get_embedding_sync(chunk["content"])
        if embedding:
            db.client.table("kb_chunks") \
                .update({"embedding": embedding}) \
                .eq("id", chunk["id"]) \
                .execute()
            processed += 1
    
    return {
        "status": "completed",
        "document_id": document_id,
        "processed": processed,
        "total": len(chunks.data)
    }
