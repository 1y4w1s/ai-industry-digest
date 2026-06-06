"""
Signal - 知识库自动导入脚本
从日报文章自动导入知识库，实现知识库内容自动扩充

用法:
  # 导入昨天的文章（适合 cron 每日执行）
  python scripts/import_to_kb.py

  # 导入指定日期范围
  python scripts/import_to_kb.py --from-date 2026-06-01 --to-date 2026-06-06

  # 导入全部未导入的文章（首次批量导入）
  python scripts/import_to_kb.py --all

  # 查看统计
  python scripts/import_to_kb.py --stats
"""

import os
import sys
import asyncio
import uuid
import argparse
from datetime import datetime, date, timedelta
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.database import DatabaseManager


# ── 配置 ──
KB_DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api", "uploads")


def ensure_tracking_table(db: DatabaseManager):
    """确保导入追踪表存在"""
    # 使用 raw SQL 通过 Supabase 的 REST API 创建表
    # Supabase 推荐在 SQL Editor 中手动执行，这里做个安全判断
    try:
        result = db.client.table("kb_imported_articles").select("id").limit(1).execute()
        return  # 表已存在
    except Exception:
        print("  [INFO] kb_imported_articles 表不存在，请在 Supabase SQL Editor 执行:")
        print("""
CREATE TABLE IF NOT EXISTS kb_imported_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    kb_document_id UUID NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
    imported_at TIMESTAMP DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kb_imported_article ON kb_imported_articles(article_id);
        """)


def get_already_imported_ids(db: DatabaseManager) -> set:
    """获取已导入的文章 ID 集合"""
    try:
        result = db.client.table("kb_imported_articles").select("article_id").execute()
        return {row["article_id"] for row in (result.data or [])}
    except Exception:
        return set()


def mark_as_imported(db: DatabaseManager, article_id: str, kb_document_id: str):
    """标记文章已导入"""
    try:
        db.client.table("kb_imported_articles").insert({
            "id": str(uuid.uuid4()),
            "article_id": article_id,
            "kb_document_id": kb_document_id,
            "imported_at": datetime.now().isoformat(),
        }).execute()
    except Exception as e:
        print(f"    [WARN] 标记导入失败: {e}")


def fetch_articles(db: DatabaseManager, from_date: str = None, to_date: str = None, all_articles: bool = False) -> List[dict]:
    """从 articles 表获取文章"""
    query = db.client.table("articles") \
        .select("id, title, url, source_name, raw_content, summary, tags, published_at, importance") \
        .order("published_at", desc=True)

    if not all_articles:
        # 默认导入昨天
        if not from_date:
            from_date = (date.today() - timedelta(days=1)).isoformat()
        if not to_date:
            to_date = date.today().isoformat()
        query = query.gte("published_at", f"{from_date}T00:00:00Z")
        query = query.lte("published_at", f"{to_date}T23:59:59Z")

    # 只导入有实际内容的文章
    query = query.not_.is_("raw_content", "null")
    query = query.neq("raw_content", "")

    result = query.execute()
    return result.data or []


def create_kb_document(db: DatabaseManager, article: dict) -> str:
    """创建知识库文档记录，返回 document_id"""
    document_id = str(uuid.uuid4())
    
    # 使用文章标题作为文件名
    safe_title = "".join(c if c.isalnum() or c in ' -_.,()[]' else '_' for c in article["title"])[:100]
    filename = f"{safe_title}.txt"
    
    # 构建标签（合并文章标签 + 来源）
    tags = list(set((article.get("tags") or []) + [article.get("source_name", "website")]))
    
    db.client.table("kb_documents").insert({
        "id": document_id,
        "user_id": "123e4567-e89b-12d3-a456-426614174000",  # 默认系统用户
        "name": filename,
        "file_type": "text",
        "file_size": len(article.get("raw_content", "") or ""),
        "status": "pending",
        "source": "website",
        "tags": tags,
        "is_public": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }).execute()

    return document_id


def save_document_file(document_id: str, content: str):
    """保存文档内容到本地文件"""
    os.makedirs(KB_DOCUMENTS_DIR, exist_ok=True)
    file_path = os.path.join(KB_DOCUMENTS_DIR, f"{document_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def process_document(db: DatabaseManager, document_id: str, content: str) -> dict:
    """处理文档：切片 + 实体识别 + 关系抽取"""
    from api.routes.kb import split_into_chunks
    from processor.ai_processor import AIProcessor

    # 更新状态为处理中
    db.client.table("kb_documents") \
        .update({"status": "processing", "updated_at": datetime.now().isoformat()}) \
        .eq("id", document_id) \
        .execute()

    try:
        # 切片
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

        # AI 实体识别和关系抽取
        entities = []
        relations = []
        try:
            ai = AIProcessor()
            entities, relations = asyncio.run(ai.extract_knowledge(content))
        except Exception as e:
            print(f"    [WARN] AI 处理失败: {e}")

        # 保存实体
        entity_map = {}
        for entity in entities:
            entity_id = str(uuid.uuid4())
            entity_map[entity.get("name", "?" )] = entity_id
            db.client.table("kb_entities").insert({
                "id": entity_id,
                "document_id": document_id,
                "name": entity.get("name", ""),
                "type": entity.get("type", "concept"),
                "created_at": datetime.now().isoformat(),
            }).execute()

        # 保存关系
        for relation in relations:
            if relation.get("source") in entity_map and relation.get("target") in entity_map:
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
            .update({
                "status": "completed",
                "chunks_count": len(chunks),
                "updated_at": datetime.now().isoformat()
            }) \
            .eq("id", document_id) \
            .execute()

        return {
            "chunks": len(chunks),
            "entities": len(entities),
            "relations": len(relations),
        }

    except Exception as e:
        db.client.table("kb_documents") \
            .update({"status": "failed", "updated_at": datetime.now().isoformat()}) \
            .eq("id", document_id) \
            .execute()
        raise e


def show_stats(db: DatabaseManager):
    """显示导入统计"""
    try:
        # KB 文档统计
        kb_result = db.client.table("kb_documents").select("id, source", count="exact").execute()
        total_kb = len(kb_result.data or [])
        website_docs = sum(1 for d in (kb_result.data or []) if d.get("source") == "website")
        user_docs = sum(1 for d in (kb_result.data or []) if d.get("source") == "user")

        # 导入记录
        imported_result = db.client.table("kb_imported_articles").select("id", count="exact").execute()
        total_imported = imported_result.count or len(imported_result.data or [])

        # 文章总览
        articles_result = db.client.table("articles").select("id", count="exact").execute()
        total_articles = articles_result.count or len(articles_result.data or [])

        print(f"\n{'='*50}")
        print(f"  知识库导入统计")
        print(f"{'='*50}")
        print(f"  📦 知识库文档总数:  {total_kb}")
        print(f"      ├─ 网站自动导入: {website_docs}")
        print(f"      └─ 用户上传:     {user_docs}")
        print(f"  📄 文章总库:        {total_articles}")
        print(f"  🔄 已导入知识库:    {total_imported}")
        print(f"  ⏳ 待导入:          {max(0, total_articles - total_imported)}")
        print(f"{'='*50}\n")

    except Exception as e:
        print(f"  [ERROR] 获取统计失败: {e}")
        print("  提示：可能 kb_imported_articles 表未创建，但不影响导入功能。")


def import_articles(from_date: str = None, to_date: str = None, all_articles: bool = False, dry_run: bool = False):
    """主导入逻辑"""
    db = DatabaseManager()
    
    # 获取已有导入记录
    imported_ids = get_already_imported_ids(db)
    
    # 获取文章
    articles = fetch_articles(db, from_date, to_date, all_articles)
    
    # 过滤已导入的
    to_import = [a for a in articles if a["id"] not in imported_ids]
    
    print(f"\n{'='*50}")
    print(f"  知识库自动导入")
    print(f"{'='*50}")
    print(f"  查询到: {len(articles)} 篇文章")
    print(f"  已导入: {len(articles) - len(to_import)} 篇")
    print(f"  待导入: {len(to_import)} 篇")
    print(f"{'='*50}\n")

    if not to_import:
        print("  ✅ 没有需要导入的文章")
        return {"imported": 0, "skipped": 0, "errors": 0}

    if dry_run:
        print("  [DRY RUN] 预览模式，不执行实际导入\n")
        for article in to_import:
            print(f"  📄 {article['title'][:60]}")
            print(f"     来源: {article['source_name']} | 字符: {len(article.get('raw_content', '') or '')}")
        print(f"\n  共计 {len(to_import)} 篇待导入\n")
        return {"imported": 0, "skipped": len(to_import), "errors": 0}

    # 执行导入
    stats = {"imported": 0, "skipped": 0, "errors": 0}
    
    for i, article in enumerate(to_import, 1):
        title_short = article["title"][:50]
        content = article.get("raw_content") or article.get("summary") or ""
        
        if not content or len(content) < 50:
            print(f"  [{i}/{len(to_import)}] ⏭ 内容过短: {title_short}")
            stats["skipped"] += 1
            continue

        try:
            print(f"  [{i}/{len(to_import)}] 📄 {title_short}", end="", flush=True)
            
            # 1. 创建 KB 文档
            doc_id = create_kb_document(db, article)
            
            # 2. 保存文件
            save_document_file(doc_id, content)
            
            # 3. 处理文档（切片+实体识别）
            result = process_document(db, doc_id, content)
            
            # 4. 标记已导入
            mark_as_imported(db, article["id"], doc_id)
            
            print(f" → ✅ 切片:{result['chunks']} 实体:{result['entities']} 关系:{result['relations']}")
            stats["imported"] += 1

        except Exception as e:
            print(f" → ❌ 失败: {str(e)[:60]}")
            stats["errors"] += 1

    print(f"\n{'='*50}")
    print(f"  导入完成")
    print(f"  ✅ 成功: {stats['imported']}")
    print(f"  ⏭ 跳过: {stats['skipped']}")
    print(f"  ❌ 失败: {stats['errors']}")
    print(f"{'='*50}\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="知识库自动导入脚本")
    parser.add_argument("--from-date", help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--to-date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="导入全部未导入文章")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际执行")
    parser.add_argument("--stats", action="store_true", help="查看导入统计")
    
    args = parser.parse_args()

    if args.stats:
        db = DatabaseManager()
        show_stats(db)
        return

    import_articles(
        from_date=args.from_date,
        to_date=args.to_date,
        all_articles=args.all,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
