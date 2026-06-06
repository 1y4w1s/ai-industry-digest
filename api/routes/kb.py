"""
Signal - 知识库路由
提供文档上传、切片、知识图谱等功能
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.models.database import DatabaseManager
from processor.ai_processor import AIProcessor

router = APIRouter(prefix="/kb", tags=["知识库"])

security = HTTPBearer()

# 支持的文件类型
SUPPORTED_EXTENSIONS = {
    ".txt": "text",
    ".md": "markdown",
    ".pdf": "pdf",
    ".docx": "docx",
}

# 最大文件大小（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """获取当前用户ID（简化实现，实际应验证JWT）"""
    # 实际实现中应该验证JWT token并提取用户ID
    return credentials.credentials  # 临时返回token作为用户ID


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    tags: Optional[str] = "",
    user_id: str = Depends(get_current_user)
):
    """上传文档"""
    # 验证文件类型
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，支持：{', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    # 验证文件大小
    file_size = 0
    content = b""
    async for chunk in file.file:
        file_size += len(chunk)
        content += chunk
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超过限制（最大10MB）")

    # 保存文档记录
    db = DatabaseManager()
    document_id = str(uuid.uuid4())
    
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    
    db.client.table("kb_documents").insert({
        "id": document_id,
        "user_id": user_id,
        "name": file.filename,
        "file_type": SUPPORTED_EXTENSIONS[ext],
        "file_size": file_size,
        "status": "pending",
        "tags": tag_list,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }).execute()

    # 保存文件到本地（临时）
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{document_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "id": document_id,
        "name": file.filename,
        "file_type": SUPPORTED_EXTENSIONS[ext],
        "file_size": file_size,
        "status": "pending",
        "tags": tag_list,
        "created_at": datetime.now().isoformat(),
    }


@router.get("/health")
async def health_check():
    """知识库服务健康检查（公开接口）"""
    return {"status": "ok", "service": "knowledge-base"}


@router.get("/documents")
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """获取文档列表"""
    db = DatabaseManager()
    
    query = db.client.table("kb_documents") \
        .select("*", count="exact") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True)

    if tag:
        query = query.contains("tags", [tag])
    if status:
        query = query.eq("status", status)

    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)

    result = query.execute()

    total = result.count or 0
    return {
        "items": result.data or [],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取文档详情"""
    db = DatabaseManager()
    
    result = db.client.table("kb_documents") \
        .select("*") \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="文档不存在")

    return result.data[0]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """删除文档"""
    db = DatabaseManager()
    
    # 检查文档是否存在
    result = db.client.table("kb_documents") \
        .select("id") \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除文档（级联删除关联的切片、实体、关系）
    db.client.table("kb_documents") \
        .delete() \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()

    # 删除本地文件
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    for ext in SUPPORTED_EXTENSIONS.keys():
        file_path = os.path.join(upload_dir, f"{document_id}{ext}")
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"message": "文档已删除"}


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取文档切片列表"""
    db = DatabaseManager()
    
    # 验证文档属于用户
    doc_result = db.client.table("kb_documents") \
        .select("id") \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="文档不存在")

    result = db.client.table("kb_chunks") \
        .select("*") \
        .eq("document_id", document_id) \
        .order("chunk_index") \
        .execute()

    return result.data or []


@router.get("/documents/{document_id}/graph")
async def get_document_graph(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取文档知识图谱数据"""
    db = DatabaseManager()
    
    # 验证文档属于用户
    doc_result = db.client.table("kb_documents") \
        .select("id") \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 获取实体
    entities = db.client.table("kb_entities") \
        .select("id, name, type") \
        .eq("document_id", document_id) \
        .execute()

    # 获取关系
    relations = db.client.table("kb_relations") \
        .select("source_entity_id, target_entity_id, relation_type, label") \
        .eq("document_id", document_id) \
        .execute()

    return {
        "nodes": entities.data or [],
        "edges": relations.data or [],
    }


@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: str,
    user_id: str = Depends(get_current_user)
):
    """处理文档（切片 + 实体识别 + 关系抽取）"""
    db = DatabaseManager()
    
    # 验证文档属于用户
    doc_result = db.client.table("kb_documents") \
        .select("id, name, file_type") \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="文档不存在")

    document = doc_result.data[0]

    # 更新状态为处理中
    db.client.table("kb_documents") \
        .update({"status": "processing", "updated_at": datetime.now().isoformat()}) \
        .eq("id", document_id) \
        .execute()

    try:
        # 读取文件内容
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
        _, ext = os.path.splitext(document["name"].lower())
        file_path = os.path.join(upload_dir, f"{document_id}{ext}")
        
        content = read_file_content(file_path, document["file_type"])
        
        # 切片处理
        chunks = split_into_chunks(content)
        
        # 保存切片
        for i, chunk in enumerate(chunks):
            db.client.table("kb_chunks").insert({
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "content": chunk,
                "chunk_index": i,
                "metadata": {"length": len(chunk)},
                "created_at": datetime.now().isoformat(),
            }).execute()

        # 实体识别和关系抽取（使用AI）
        ai_processor = AIProcessor()
        entities, relations = await ai_processor.extract_knowledge(content)
        
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

        # 更新状态为完成
        db.client.table("kb_documents") \
            .update({"status": "completed", "updated_at": datetime.now().isoformat()}) \
            .eq("id", document_id) \
            .execute()

        return {
            "message": "处理完成",
            "chunks_count": len(chunks),
            "entities_count": len(entities),
            "relations_count": len(relations),
        }

    except Exception as e:
        # 更新状态为失败
        db.client.table("kb_documents") \
            .update({"status": "failed", "updated_at": datetime.now().isoformat()}) \
            .eq("id", document_id) \
            .execute()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


def read_file_content(file_path: str, file_type: str) -> str:
    """读取文件内容"""
    if file_type == "text" or file_type == "markdown":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_type == "pdf":
        # 使用 PyMuPDF 读取 PDF
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except ImportError:
            raise HTTPException(status_code=500, detail="缺少 PyMuPDF 依赖")
    elif file_type == "docx":
        # 使用 python-docx 读取 DOCX
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            raise HTTPException(status_code=500, detail="缺少 python-docx 依赖")
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")


def split_into_chunks(content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将内容切分为多个切片"""
    chunks = []
    start = 0
    content_len = len(content)
    
    while start < content_len:
        end = min(start + chunk_size, content_len)
        # 在句子边界处分割（只在还有更多内容时尝试）
        if end < content_len:
            # 找到最近的句号、问号、感叹号或换行
            for i in range(min(50, end - start), 0, -1):
                if content[end - i] in ".?!\n":
                    end = end - i + 1
                    break
        
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 计算下一个起始位置，确保至少前进一个字符
        next_start = end - overlap
        if next_start <= start:
            # 如果没有前进，强制前进至少一个字符
            next_start = start + 1
        start = next_start
    return chunks
