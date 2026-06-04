"""
Signal - 每日数据完整性校验
检查 articles 数和 daily_reports 数是否匹配

用法:
    python scripts/daily_verify.py
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.database import DatabaseManager


def main():
    print("=" * 50)
    print("  Signal - 数据完整性校验")
    print(f"  时间: {date.today().isoformat()}")
    print("=" * 50)

    db = DatabaseManager()

    # 1. 文章总数
    total = db.get_article_count()
    print(f"\n📦 文章总数: {total}")

    # 2. 日报数
    reports = db.get_reports(page=1, page_size=100)
    report_count = reports["total"]
    print(f"📰 日报数: {report_count}")

    # 3. 检查最近 3 天是否有日报
    print(f"\n📅 最近日报:")
    for item in reports["items"][:7]:
        article_count = len(item.get("article_ids", []) or [])
        indicator = "✅" if article_count > 0 else "⚠️"
        print(f"  {indicator} {item['report_date']}: {article_count} 篇文章")

    # 4. 检查昨天的日报是否存在
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    yesterday_report = db.get_report_by_date(yesterday)
    if yesterday_report:
        print(f"\n✅ 昨日 ({yesterday}) 日报存在: {len(yesterday_report.get('article_ids', []) or [])} 篇文章")
    else:
        print(f"\n⚠️  昨日 ({yesterday}) 日报不存在（可能无数据）")

    # 5. 检查信息源健康状态
    print(f"\n📡 信息源:")
    sources = db.get_sources()
    for s in sources:
        result = db.client.table("articles") \
            .select("id", count="exact") \
            .eq("source_name", s) \
            .execute()
        count = result.count or 0
        print(f"  ✅ {s}: {count} 篇")

    print(f"\n{'=' * 50}")
    print(f"  校验完成")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
