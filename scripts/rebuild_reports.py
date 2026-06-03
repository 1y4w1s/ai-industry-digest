"""
AI Industry Digest - 重建日报
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


def build_report_data(articles: list, ai: AIProcessor = None) -> dict:
    """为一天的文章构建日报数据"""
    from collections import Counter
    import jieba
    import re

    # 按重要性分组
    grouped = {"high": [], "medium": [], "low": []}
    for a in articles:
        imp = a.get("importance", "low") or "low"
        if imp in grouped:
            grouped[imp].append(a)
        else:
            grouped["low"].append(a)

    # 提取关键词
    tag_counter = Counter()
    word_counter = Counter()
    stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不",
                  "人", "都", "一", "一个", "上", "也", "很", "到",
                  "说", "要", "去", "你", "会", "着", "没有", "看",
                  "好", "自己", "这", "他", "她", "它", "们", "与",
                  "及", "或", "等", "从", "被", "把", "对", "为",
                  "the", "a", "an", "and", "or", "for", "of", "in",
                  "to", "is", "it", "on", "with", "by", "as", "at",
                  "that", "this", "from", "are", "was", "be", "has",
                  "have", "not", "but", "we", "its", "their"}

    for a in articles:
        for tag in (a.get("tags", []) or []):
            tag_counter[tag] += 1
        words = jieba.lcut(a.get("title", ""))
        for w in words:
            w = w.strip().lower()
            if re.match(r'^[\u4e00-\u9fff]+$', w) and len(w) >= 2 and w not in stop_words:
                word_counter[w] += 1
            elif re.match(r'^[a-zA-Z]+$', w) and len(w) >= 4 and w not in stop_words:
                word_counter[w] += 1

    combined = tag_counter + word_counter
    keywords = [w for w, _ in combined.most_common(10)]

    # 生成概览
    insight = ""
    if ai:
        try:
            top_articles = grouped["high"][:5] if grouped["high"] else articles[:5]
            arts_list = "\n".join([
                f"- [{a.get('importance','low')}] {a.get('title','')}: {(a.get('summary','') or '')[:100]}"
                for a in top_articles
            ])
            prompt = f"以下是今天最重要的 {len(top_articles)} 篇 AI 行业新闻。请写一段 150 字以内的'今日概览'。\n{arts_list}\n今日概览："
            response = ai._call_api(prompt)
            if response:
                insight = response["choices"][0]["message"]["content"].strip()
        except Exception:
            insight = ""

    return {
        "summary_insight": insight or f"今日共收录 {len(articles)} 篇文章。",
        "trending_keywords": keywords,
        "grouped": grouped,
    }


def save_report(db: DatabaseManager, report_date: str, articles: list):
    """将日报写入 daily_reports 表"""
    # 获取文章 UUID
    article_uuids = []
    for a in articles:
        result = db.client.table("articles") \
            .select("id") \
            .eq("url", a["url"]) \
            .execute()
        if result.data:
            article_uuids.append(result.data[0]["id"])

    report_data = {
        "report_date": report_date,
        "article_ids": article_uuids if article_uuids else None,
        "summary_insight": "",
        "trending_keywords": [],
        "trend_analysis": "",
    }

    db.client.table("daily_reports").upsert(
        report_data,
        on_conflict="report_date"
    ).execute()

    # 更新概览和关键词
    db.client.table("daily_reports") \
        .update({
            "summary_insight": report_data["summary_insight"],
            "trending_keywords": report_data["trending_keywords"],
        }) \
        .eq("report_date", report_date) \
        .execute()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="重建日报")
    parser.add_argument("--date", type=str, default=None, help="只重建指定日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    print("=" * 50)
    print("  AI Industry Digest - 重建日报")
    print("=" * 50)

    db = DatabaseManager()

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

    for day in sorted(groups.keys()):
        articles = groups[day]
        print(f"\n  📅 {day}: {len(articles)} 篇", end="")

        # 获取文章 UUID
        article_uuids = []
        for a in articles:
            result = db.client.table("articles") \
                .select("id") \
                .eq("url", a["url"]) \
                .execute()
            if result.data:
                article_uuids.append(result.data[0]["id"])

        report_data = {
            "report_date": day,
            "article_ids": article_uuids if article_uuids else None,
            "summary_insight": "",
            "trending_keywords": [],
            "trend_analysis": "",
        }

        db.client.table("daily_reports").upsert(
            report_data,
            on_conflict="report_date"
        ).execute()
        print(f" ✅ {len(article_uuids)} 个 ID 已入库")

    print("\n" + "=" * 50)
    print("  重建完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
