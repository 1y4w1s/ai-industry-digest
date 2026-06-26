"""
定时任务：批量处理未生成 Embedding 的文档切片，以及单文档完整处理

使用方法：
    celery -A tasks beat --loglevel=info    # 启动调度器
    celery -A tasks worker --loglevel=info # 启动 worker
"""

import os
import sys
import uuid
import asyncio
from datetime import datetime
from typing import Optional
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
def process_single_document(document_id: str, force_reprocess: bool = False):
    """
    处理单个文档的完整流程（Celery 异步任务）
    
    包含：读取文件 → 切片 → 批量 Embedding → 保存切片 → 实体识别 → 关系抽取
    支持 F-11 增量更新：内容未变更时跳过处理
    
    当用户通过 API 触发文档处理时，自动调用此任务
    """
    from api.routes.kb import read_file_content, split_into_chunks, _safe_file_path, EXTENSION_MAP
    from api.services.embedding import get_embeddings_sync
    from api.services.embedding import get_embedding_service
    from api.services.metadata import get_metadata_enricher
    from api.services.document_tracker import get_document_tracker
    from api.models.database import get_db
    from processor.ai_processor import AIProcessor
    
    logger = app.log.get_default_logger()
    db = get_db()
    
    logger.info(f"[process_single_document] 开始处理文档: {document_id}")
    
    try:
        # 1. 获取文档信息
        doc_result = db.client.table("kb_documents") \
            .select("id, name, file_type, user_id") \
            .eq("id", document_id) \
            .execute()
        
        if not doc_result.data:
            logger.error(f"[process_single_document] 文档不存在: {document_id}")
            return {"status": "failed", "document_id": document_id, "error": "文档不存在"}
        
        document = doc_result.data[0]
        file_type = document.get("file_type", "text")
        document_name = document.get("name", "")
        
        # 2. 读取文件内容
        file_path = _safe_file_path(document_id, file_type)
        content = read_file_content(file_path, file_type)
        
        # F-11 增量更新：检测内容是否变更
        if not force_reprocess:
            tracker = get_document_tracker()
            change = tracker.detect_change(document_id, content)
            if not change["changed"]:
                logger.info(f"[process_single_document] {change['skip_reason']}")
                return {"status": "skipped", "document_id": document_id, "reason": change["skip_reason"]}
        
        # F-13 多模态支持：从 PDF/DOCX 提取图片并生成描述
        if file_type in ("pdf", "docx"):
            try:
                from api.services.image_extractor import get_image_extractor
                from api.services.image_caption import get_image_caption_service
                
                extractor = get_image_extractor()
                captioner = get_image_caption_service()
                
                if file_type == "pdf":
                    images = extractor.extract_from_pdf(file_path, document_id)
                else:
                    images = extractor.extract_from_docx(file_path, document_id)
                
                if images:
                    captioned = captioner.describe_batch(images)
                    image_lines = []
                    for img in captioned:
                        desc = img.get("description", "[图片内容]")
                        image_lines.append(f"[图片: {desc}]")
                    if image_lines:
                        content += "\n\n" + "\n\n".join(image_lines)
                        logger.info(f"[process_single_document] 提取了 {len(images)} 张图片")
            except Exception as e:
                logger.error(f"[process_single_document] 图片处理失败（非致命）: {e}")
        
        # 3. 切片处理
        chunks = split_into_chunks(content)
        logger.info(f"[process_single_document] 切片完成: {len(chunks)} 个")
        
        # 4. 批量生成 Embedding
        BATCH_SIZE = 10
        all_embeddings = []
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_embeddings = get_embeddings_sync(batch)
            all_embeddings.extend(batch_embeddings)
        
        # 5. 保存切片（第一轮：基础元数据，不含实体）
        enricher = get_metadata_enricher()
        chunk_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            
            meta = enricher.enrich(
                chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                document_name=document_name,
                file_type=file_type,
                page_number=0,
            )
            
            db.client.table("kb_chunks").insert({
                "id": chunk_id,
                "document_id": document_id,
                "content": chunk,
                "chunk_index": i,
                "embedding": embedding,
                "metadata": meta,
                "created_at": datetime.now().isoformat(),
            }).execute()
        
        logger.info(f"[process_single_document] 切片保存完成, 共 {len(chunks)} 个")
        
        # 6. 实体识别和关系抽取（使用 asyncio.run 包装异步调用）
        try:
            ai_processor = AIProcessor()
            entities, relations = asyncio.run(ai_processor.extract_knowledge(content))
            
            # 保存实体
            entity_map = {}
            for entity in entities:
                entity_id = str(uuid.uuid4())
                entity_map[entity["name"]] = entity_id
                db.client.table("kb_entities").insert({
                    "id": entity_id,
                    "document_id": document_id,
                    "name": entity["name"],
                    "type": entity.get("type", "concept"),
                    "created_at": datetime.now().isoformat(),
                }).execute()
            
            # 保存关系
            for relation in relations:
                if relation["source"] in entity_map and relation["target"] in entity_map:
                    db.client.table("kb_relations").insert({
                        "id": str(uuid.uuid4()),
                        "document_id": document_id,
                        "source_entity_id": entity_map[relation["source"]],
                        "target_entity_id": entity_map[relation["target"]],
                        "relation_type": relation.get("relation", "related_to"),
                        "label": relation.get("label", ""),
                        "created_at": datetime.now().isoformat(),
                    }).execute()
            
            logger.info(f"[process_single_document] 知识图谱完成: {len(entities)} 实体, {len(relations)} 关系")
            
            # 第二轮：更新切片元数据，补充实体信息
            entity_names = list(entity_map.keys())
            if entity_names:
                for chunk_id in chunk_ids:
                    chunk_result = db.client.table("kb_chunks") \
                        .select("id, content, metadata") \
                        .eq("id", chunk_id) \
                        .execute()
                    if chunk_result.data:
                        chunk_data = chunk_result.data[0]
                        if isinstance(chunk_data.get("metadata"), dict):
                            enriched = enricher.enrich(
                                chunk_data["content"],
                                extracted_entities=entity_names,
                            )
                            updated_meta = chunk_data["metadata"]
                            updated_meta["extracted_entities"] = enriched["extracted_entities"]
                            updated_meta["section_title"] = enriched["section_title"]
                            updated_meta["section_depth"] = enriched["section_depth"]
                            updated_meta["has_code"] = enriched["has_code"]
                            updated_meta["code_language"] = enriched["code_language"]
                            
                            db.client.table("kb_chunks") \
                                .update({"metadata": updated_meta}) \
                                .eq("id", chunk_id) \
                                .execute()
            
            logger.info(f"[process_single_document] 切片元数据更新完成")
        except Exception as e:
            logger.error(f"[process_single_document] 知识图谱处理失败: {e}")
            entities, relations = [], []
        
        # 7. 更新文档状态为完成
        db.client.table("kb_documents") \
            .update({
                "status": "completed",
                "chunks_count": len(chunks),
                "updated_at": datetime.now().isoformat()
            }) \
            .eq("id", document_id) \
            .execute()
        
        # F-11 增量更新：成功处理后递增版本号
        tracker = get_document_tracker()
        tracker.bump_version(document_id, content)
        
        logger.info(f"[process_single_document] 文档处理完成: {document_id}")
        
        return {
            "status": "completed",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "entities_count": len(entities),
            "relations_count": len(relations),
        }
    
    except Exception as e:
        logger.error(f"[process_single_document] 处理失败: {e}")
        
        # 更新文档状态为失败
        try:
            db.client.table("kb_documents") \
                .update({"status": "failed", "updated_at": datetime.now().isoformat()}) \
                .eq("id", document_id) \
                .execute()
        except:
            pass
        
        return {
            "status": "failed",
            "document_id": document_id,
            "error": str(e)
        }
