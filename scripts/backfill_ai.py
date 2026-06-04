"""
Signal - 回填脚本
扫描数据库中无摘要的文章，调用 AI 补上摘要/标签/重要性

用法:
    python scripts/backfill_ai.py          # 回填所有无摘要的文章
    python scripts/backfill_ai.py --limit 10  # 只处理 10 篇（测试用）
"""

import os
import sys
import time
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.database import DatabaseManager
from processor.ai_processor import AIProcessor
from collector.base import Article


def fetch_unprocessed_articles(db: DatabaseManager, limit: int = None) -> List[dict]:
    """获取数据库中没有 AI 摘要的文章"""
    query = db.client.table("articles") \
        .select("*", count="exact") \
        .is_("summary", "null") \
        .order("published_at", desc=True)

    if limit:
        query = query.limit(limit)

    result = query.execute()
    articles = result.data or []
    print(f"  查询到 {len(articles)} 篇未处理文章" + (f" (limit={limit})" if limit else ""))
    return articles


def convert_to_article(row: dict) -> Article:
    """将数据库行转为 Article 对象"""
    from datetime import datetime
    published_at = None
    if row.get("published_at"):
        try:
            if isinstance(row["published_at"], str):
                published_at = datetime.fromisoformat(row["published_at"].replace("Z", "+00:00"))
            else:
                published_at = row["published_at"]
        except Exception:
            pass

    return Article(
        title=row.get("title", ""),
        url=row.get("url", ""),
        source_name=row.get("source_name", ""),
        raw_content=row.get("raw_content", ""),
        published_at=published_at,
    )


def update_article(db: DatabaseManager, article_id: str, article: Article):
    """更新文章的 AI 字段"""
    data = {
        "summary": article.summary or "",
        "tags": article.tags or [],
        "importance": article.importance or "low",
        "importance_reason": article.importance_reason or "",
    }
    db.client.table("articles") \
        .update(data) \
        .eq("id", article_id) \
        .execute()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="回填 AI 处理结果")
    parser.add_argument("--limit", type=int, default=None, help="限制处理数量（测试用）")
    args = parser.parse_args()

    print("=" * 50)
    print("  Signal - 回填脚本")
    print("  为数据库中无摘要的文章补上 AI 处理结果")
    print("=" * 50)

    # 初始化
    db = DatabaseManager()
    ai = AIProcessor(batch_size=10)

    # 获取未处理文章
    rows = fetch_unprocessed_articles(db, limit=args.limit)
    if not rows:
        print("\n✅ 所有文章已处理完毕！")
        return

    # 转为 Article 对象并分批处理
    articles = [convert_to_article(row) for row in rows]
    print(f"\n🤖 正在处理 {len(articles)} 篇文章...")

    processed = ai.process_articles(articles)

    # 逐个更新数据库
    success = 0
    failed = 0
    print(f"\n💾 正在写入数据库...")

    for row, article in zip(rows, processed):
        if article and article.summary:
            try:
                update_article(db, row["id"], article)
                success += 1
            except Exception as e:
                print(f"  [ERROR] 更新失败 [{row['id'][:8]}]: {e}")
                failed += 1
        else:
            failed += 1

        # 每 10 篇显示一次进度
        if (success + failed) % 10 == 0:
            print(f"  进度: {success + failed}/{len(rows)}")

    print(f"\n📊 完成: 成功 {success} 篇, 失败 {failed} 篇")
    print("=" * 50)


if __name__ == "__main__":
    main()
