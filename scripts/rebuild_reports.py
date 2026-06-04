"""
Signal - 重建日报
扫描所有文章按 published_at 分组，更新或创建日报记录

用法:
    python scripts/rebuild_reports.py        # 重建所有日报
    python scripts/rebuild_reports.py --date 2026-06-03  # 只重建某一天
"""

import os
import sys
from collections import defaultdict
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.database import DatabaseManager
from processor.ai_processor import AIProcessor
from processor.reporter import DailyReportGenerator
from collector.base import Article


def fetch_all_articles(db: DatabaseManager) -> list:
    """获取所有文章"""
    page = 1
    all_articles = []
    while True:
        result = db.get_articles(page=page, page_size=100)
        all_articles.extend(result["items"])
        if page >= result["pages"]:
            break
        page += 1
    print(f"  共 {len(all_articles)} 篇文章")
    return all_articles


def regroup_published_at(db: DatabaseManager) -> dict:
    """按发布日分组所有文章"""
    all_articles = fetch_all_articles(db)
    groups = defaultdict(list)

    for a in all_articles:
        pub = a.get("published_at")
        if pub:
            day = pub[:10]  # YYYY-MM-DD
        else:
            day = date.today().isoformat()
        groups[day].append(a)

    print(f"  覆盖 {len(groups)} 个日期")
    return groups


def main():
    import argparse
    parser = argparse.ArgumentParser(description="重建日报")
    parser.add_argument("--date", type=str, default=None, help="只重建指定日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    print("=" * 50)
    print("  Signal - 重建日报")
    print("=" * 50)

    db = DatabaseManager()
    ai = AIProcessor()

    if args.date:
        # 只重建指定日期
        result = db.client.table("articles") \
            .select("*") \
            .gte("published_at", f"{args.date}T00:00:00Z") \
            .lte("published_at", f"{args.date}T23:59:59Z") \
            .execute()
        if not result.data:
            print(f"  日期 {args.date} 无文章")
            return
        groups = {args.date: result.data}
        print(f"  日期 {args.date}: {len(result.data)} 篇文章")
    else:
        groups = regroup_published_at(db)

    # 将所有文章按日期合并为 Article 对象列表
    all_articles = []
    for day in sorted(groups.keys()):
        for a in groups[day]:
            pub_at = None
            if a.get("published_at"):
                try:
                    pub_at = datetime.fromisoformat(a["published_at"].replace("Z", "+00:00"))
                except Exception:
                    pass
            article = Article(
                title=a.get("title", ""),
                url=a.get("url", ""),
                source_name=a.get("source_name", ""),
                raw_content=a.get("raw_content", "") or "",
                published_at=pub_at,
                summary=a.get("summary", ""),
                tags=a.get("tags", []) or [],
                importance=a.get("importance", "low"),
                importance_reason=a.get("importance_reason", ""),
                source_refs=a.get("source_refs", []) or [],
            )
            all_articles.append(article)

    # 用 DailyReportGenerator 按日期分组生成日报（含 AI 摘要）
    reporter = DailyReportGenerator(db_manager=db, ai_processor=ai)
    reports = reporter.generate_grouped_by_date(all_articles)

    print("\n" + "=" * 50)
    print(f"  重建完成！共 {len(reports)} 期日报")
    for day in sorted(reports.keys()):
        r = reports[day]
        print(f"    📅 {day}: {r['total_articles']} 篇")
    print("=" * 50)


if __name__ == "__main__":
    main()
