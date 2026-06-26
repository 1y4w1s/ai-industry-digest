"""
旧文档数据清洗脚本
===================

对知识库中已完成的文档，重新读取原文件 → 数据清洗 → 重新切片 → 重新入库。

使用方式：
  # 安全模式：只扫描，不做任何修改（推荐先跑一遍看看结果）
  python scripts/reprocess_documents.py --dry-run

  # 正式执行
  python scripts/reprocess_documents.py

  # 只处理指定文档
  python scripts/reprocess_documents.py --ids doc-id-1 doc-id-2

  # 只处理包含 HTML 标签的文档（最快筛选脏文档）
  python scripts/reprocess_documents.py --only-dirty

说明：
  - 跳过 status != "completed" 或原始文件不存在的文档
  - 清洗后内容无变化 → 跳过（避免无意义的 Embedding 调用）
  - 清洗后有变化 → 重新切片 + Embedding + 更新数据库
  - 旧数据会被删除（级联删除老切片 → 插入新切片）
  - 所有变更记录在日志中
"""

import asyncio
import hashlib
import os
import sys
import time
import re
from datetime import datetime
from typing import List, Optional

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── 导入项目模块 ──────────────────────────────
# 需要在运行前加载 .env（项目入口负责）
from api.models.database import get_db
from api.services.data_cleaner import get_data_cleaner, DocumentQuality
from api.services.metadata import get_metadata_enricher
from api.services.embedding import get_embedding_service


# ── HTML 检测正则 ─────────────────────────────
_RE_HTML_TAG = re.compile(r"<[a-z][\s\S]*?>", re.IGNORECASE)


def has_html_tags(text: str) -> bool:
    """快速检测文本中是否包含 HTML 标签"""
    return bool(_RE_HTML_TAG.search(text))


def load_dotenv_if_needed():
    """加载 .env 文件（如果尚未加载）"""
    if not os.getenv("SUPABASE_URL"):
        from dotenv import load_dotenv
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            print(f"   📄 已加载 .env 文件: {dotenv_path}")
        else:
            print(f"   ⚠️ .env 文件不存在，使用环境变量")


# ── 数据库辅助函数 ────────────────────────────

def fetch_all_completed(db) -> List[dict]:
    """获取所有已完成文档"""
    result = db.client.table("kb_documents") \
        .select("id, name, file_type, file_size, source, user_id") \
        .eq("status", "completed") \
        .order("created_at", desc=True) \
        .execute()
    return result.data or []


def fetch_documents_by_ids(db, ids: List[str]) -> List[dict]:
    """按 ID 获取文档"""
    result = db.client.table("kb_documents") \
        .select("id, name, file_type, file_size, source, user_id") \
        .in_("id", ids) \
        .execute()
    return result.data or []


def count_existing_chunks(db, document_id: str) -> int:
    """统计文档现有切片数"""
    result = db.client.table("kb_chunks") \
        .select("id", count="exact") \
        .eq("document_id", document_id) \
        .execute()
    return result.count or 0


def delete_old_chunks(db, document_id: str):
    """级联删除旧切片、实体、关系"""
    db.client.table("kb_relations") \
        .delete() \
        .eq("document_id", document_id) \
        .execute()
    db.client.table("kb_entities") \
        .delete() \
        .eq("document_id", document_id) \
        .execute()
    db.client.table("kb_chunks") \
        .delete() \
        .eq("document_id", document_id) \
        .execute()


def find_existing_chunks(db, document_id: str) -> List[dict]:
    """获取现有切片内容"""
    result = db.client.table("kb_chunks") \
        .select("content, chunk_index, metadata") \
        .eq("document_id", document_id) \
        .order("chunk_index") \
        .execute()
    return result.data or []


def update_document_status(db, document_id: str, status: str, chunks_count: int = 0):
    """更新文档状态"""
    data = {"status": status, "updated_at": datetime.now().isoformat()}
    if chunks_count:
        data["chunks_count"] = chunks_count
    db.client.table("kb_documents") \
        .update(data) \
        .eq("id", document_id) \
        .execute()


def safe_file_path(document_id: str, file_type: str) -> Optional[str]:
    """构建安全的文件路径（与 kb.py 的 _safe_file_path 逻辑一致）"""
    ext_map = {
        "text": ".txt", "markdown": ".md",
        "pdf": ".pdf", "docx": ".docx",
    }
    ext = ext_map.get(file_type, ".txt")
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "api", "uploads")
    return os.path.join(upload_dir, f"{document_id}{ext}")


def read_file_content(file_path: str, file_type: str) -> str:
    """读取文件内容（简化版，不依赖 kb.py 的 read_file_content）"""
    if file_type in ("text", "markdown"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    elif file_type == "pdf":
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            print(f"   ⚠️ PyMuPDF 未安装，跳过 PDF")
            return ""
    elif file_type == "docx":
        try:
            from docx import Document
            doc = Document(file_path)
            paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paras)
        except ImportError:
            print(f"   ⚠️ python-docx 未安装，跳过 DOCX")
            return ""
    return ""


def content_checksum(content: str) -> str:
    """计算内容 MD5 用于比对"""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def is_content_changed(old_chunks: List[dict], new_chunks: List[str]) -> bool:
    """通过 MD5 判断内容是否真的变了（避免文件本身无变化但触发重处理）"""
    old_concatenated = "".join(c["content"] for c in old_chunks if c.get("content"))
    new_concatenated = "".join(new_chunks)

    old_hash = content_checksum(old_concatenated)
    new_hash = content_checksum(new_concatenated)

    return old_hash != new_hash


# ── 主处理逻辑 ────────────────────────────────

async def reprocess_document(
    db,
    doc: dict,
    dry_run: bool = False,
) -> dict:
    """重新清洗单个文档

    Returns:
        {"action": "skip|clean|reprocess", "reason": str, ...}
    """
    doc_id = doc["id"]
    doc_name = doc.get("name", "未知")
    file_type = doc.get("file_type", "text")

    # 1. 检查文件是否存在
    file_path = safe_file_path(doc_id, file_type)
    if not os.path.exists(file_path):
        return {"action": "skip", "id": doc_id, "name": doc_name,
                "reason": "原始文件不存在"}

    # 2. 读取原始内容
    try:
        raw_content = read_file_content(file_path, file_type)
    except Exception as e:
        return {"action": "skip", "id": doc_id, "name": doc_name,
                "reason": f"读取失败: {e}"}

    if not raw_content or not raw_content.strip():
        return {"action": "skip", "id": doc_id, "name": doc_name,
                "reason": "文件内容为空"}

    # 3. 数据清洗
    cleaner = get_data_cleaner()
    cleaned_content = cleaner.clean_document(raw_content)

    if not cleaned_content or not cleaned_content.strip():
        return {"action": "skip", "id": doc_id, "name": doc_name,
                "reason": "清洗后内容为空"}

    # 4. 质量评估
    quality = cleaner.check_quality(cleaned_content)
    quality_warnings = "; ".join(quality.reasons) if quality.reasons else ""

    # 5. 检测是否真的有变化
    old_chunks = find_existing_chunks(db, doc_id) if not dry_run else []
    if old_chunks:
        from api.routes.kb import split_into_chunks
        new_chunks_raw = split_into_chunks(cleaned_content)

        if not is_content_changed(old_chunks, new_chunks_raw):
            return {"action": "skip", "id": doc_id, "name": doc_name,
                    "chunks_before": len(old_chunks),
                    "reason": "清洗后内容无变化"}

    # --- 到这里说明内容真的变了，需要重新处理 ---
    if dry_run:
        return {"action": "needs_clean", "id": doc_id, "name": doc_name,
                "raw_size": len(raw_content),
                "cleaned_size": len(cleaned_content),
                "has_html": has_html_tags(raw_content),
                "quality_warnings": quality_warnings}

    # 6. 正式处理
    try:
        from api.routes.kb import split_into_chunks
        import uuid
        from processor.ai_processor import AIProcessor

        chunks = split_into_chunks(cleaned_content)

        # 过滤低质量切片
        chunks = cleaner.filter_chunks(chunks)
        if not chunks:
            return {"action": "skip", "id": doc_id, "name": doc_name,
                    "reason": "切片后无有效内容"}

        # 删除旧数据
        delete_old_chunks(db, doc_id)

        # 重新 Embedding + 入库
        embedding_service = get_embedding_service()
        enricher = get_metadata_enricher()

        BATCH_SIZE = 10
        all_embeddings = []
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_embeddings = await embedding_service.get_embeddings(batch)
            all_embeddings.extend(batch_embeddings)

        chunk_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)

            chunk = cleaner.clean_chunk(chunk)
            meta = enricher.enrich(
                chunk, chunk_index=i, total_chunks=len(chunks),
                document_name=doc_name, file_type=file_type, page_number=0,
            )

            db.client.table("kb_chunks").insert({
                "id": chunk_id, "document_id": doc_id,
                "content": chunk, "chunk_index": i,
                "embedding": embedding, "metadata": meta,
                "created_at": datetime.now().isoformat(),
            }).execute()

        # 实体识别（跳过，依赖 LLM API）
        entity_count = 0
        relation_count = 0

        # 更新文档状态
        update_document_status(db, doc_id, "completed", len(chunks))

        return {
            "action": "reprocess",
            "id": doc_id,
            "name": doc_name,
            "chunks_before": len(old_chunks) if old_chunks else 0,
            "chunks_after": len(chunks),
            "entities": entity_count,
            "relations": relation_count,
            "raw_size": len(raw_content),
            "cleaned_size": len(cleaned_content),
            "quality_warnings": quality_warnings,
        }

    except Exception as e:
        update_document_status(db, doc_id, "failed")
        return {"action": "error", "id": doc_id, "name": doc_name,
                "reason": str(e)}


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="重新清洗旧知识库文档"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="仅扫描，不做任何修改")
    parser.add_argument("--ids", nargs="+",
                        help="只处理指定文档 ID（空格分隔）")
    parser.add_argument("--only-dirty", action="store_true",
                        help="只处理包含 HTML 标签的文档")
    parser.add_argument("--limit", type=int, default=0,
                        help="最多处理 N 个文档（0 = 不限制）")
    args = parser.parse_args()

    load_dotenv_if_needed()
    db = get_db()

    # ── 获取文档列表 ──────────────────────────
    if args.ids:
        documents = fetch_documents_by_ids(db, args.ids)
        print(f"\n📋 按 ID 查询到 {len(documents)} 个文档")
    else:
        documents = fetch_all_completed(db)
        print(f"\n📋 共查出 {len(documents)} 个已完成文档")

    if not documents:
        print("❌ 没有需要处理的文档")
        sys.exit(0)

    # ── 筛选包含 HTML 的文档 ─────────────────
    if args.only_dirty:
        dirty_docs = []
        print(f"\n🔍 正在检测 HTML 标签...")
        for doc in documents:
            file_path = safe_file_path(doc["id"], doc.get("file_type", "text"))
            if os.path.exists(file_path):
                content = read_file_content(file_path, doc.get("file_type", "text"))
                if has_html_tags(content):
                    dirty_docs.append(doc)
        print(f"   检测到 {len(dirty_docs)}/{len(documents)} 个文档可能含 HTML 残留")
        documents = dirty_docs

    # ── 应用 limit ────────────────────────────
    if args.limit > 0 and len(documents) > args.limit:
        documents = documents[:args.limit]
        print(f"   (limit={args.limit}, 仅处理前 {args.limit} 个)")

    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"🔍 DRY RUN 模式 — 只扫描，不修改")
        print(f"{'='*60}")

    print(f"\n{'='*60}")
    print(f"{'DRY RUN' if args.dry_run else '开始处理'} | 共 {len(documents)} 个文档")
    print(f"{'='*60}")

    # ── 逐一处理 ──────────────────────────────
    stats = {"skipped": 0, "reprocess": 0, "needs_clean": 0, "error": 0}
    total_start = time.time()

    for idx, doc in enumerate(documents, 1):
        print(f"\n[{idx}/{len(documents)}] {doc.get('name', '未知')} ({doc['id'][:8]}...)")
        print(f"   文件类型: {doc.get('file_type', '?')} | 来源: {doc.get('source', '?')}")

        result = await reprocess_document(db, doc, dry_run=args.dry_run)

        action = result.get("action", "error")

        if action == "skip":
            stats["skipped"] += 1
            print(f"   ⏭️  跳过: {result['reason']}")

        elif action == "needs_clean":
            stats["needs_clean"] += 1
            print(f"   🧹 需要清洗: ({result['raw_size']}b → {result['cleaned_size']}b)")
            if result.get("has_html"):
                print(f"      ⚠️ 含 HTML 标签")
            if result.get("quality_warnings"):
                print(f"      ⚠️ 质量: {result['quality_warnings']}")

        elif action == "reprocess":
            stats["reprocess"] += 1
            elapsed = time.time() - total_start
            print(f"   ✅ 重新处理完成: "
                  f"{result['chunks_before']}切片 → {result['chunks_after']}切片 "
                  f"({result['raw_size']}b → {result['cleaned_size']}b)")

        elif action == "error":
            stats["error"] += 1
            print(f"   ❌ 失败: {result['reason']}")

    # ── 汇总 ──────────────────────────────────
    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"📊 处理完成 | 耗时 {total_elapsed:.1f}s")
    print(f"   跳过: {stats['skipped']} | ", end="")
    if args.dry_run:
        print(f"待清洗: {stats['needs_clean']} | ", end="")
    else:
        print(f"已重处理: {stats['reprocess']} | ", end="")
    print(f"错误: {stats['error']}")
    print(f"{'='*60}")

    if args.dry_run and stats["needs_clean"] > 0:
        print(f"\n💡 推荐执行正式处理: python scripts/reprocess_documents.py")


if __name__ == "__main__":
    asyncio.run(main())
