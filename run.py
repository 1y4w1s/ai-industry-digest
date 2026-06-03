"""
AI Industry Digest - 全流程运行入口
采集 → 去重 → AI 处理 → 日报生成 → 入库
"""

import os
import sys
import yaml
from datetime import datetime, date
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector.base import Article
from collector.rss_collector import RSSCollector
from collector.arxiv_collector import ArxivCollector
from processor.dedup import Deduplicator
from processor.ai_processor import AIProcessor
from processor.reporter import DailyReportGenerator
from api.models.database import DatabaseManager


def load_sources() -> List[dict]:
    """加载信息源配置"""
    config_path = os.path.join(os.path.dirname(__file__), "config", "sources.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [s for s in data.get("sources", []) if s.get("enabled", True)]


def create_collector(source_config: dict, collector_type: str = None):
    """创建采集器"""
    collectors = source_config.get("collectors", [])
    if not collectors:
        return None
    target_type = collector_type or collectors[0].get("type")
    target_config = next((c for c in collectors if c.get("type") == target_type), None)
    if not target_config:
        return None

    if target_type == "rss":
        return RSSCollector(source_config)
    elif target_type == "api":
        api_type = target_config.get("api_type", "")
        if api_type == "arxiv":
            return ArxivCollector(source_config)
    return None


def collect_all(sources: List[dict]) -> List[Article]:
    """采集所有信息源"""
    all_articles: List[Article] = []
    stats = {"success": 0, "failed": 0}

    for source_config in sources:
        name = source_config.get("name", "unknown")
        print(f"\n--- {name} ---")
        collectors = source_config.get("collectors", [])
        success = False

        for idx, coll_cfg in enumerate(collectors):
            if idx > 0:
                print(f"  [FALLBACK] 尝试备用方式: {coll_cfg.get('type')}")
            collector = create_collector(source_config, coll_cfg.get("type"))
            if not collector:
                continue

            try:
                articles = collector.collect()
                if articles:
                    all_articles.extend(articles)
                    success = True
                    break
                else:
                    print(f"  [EMPTY] 未采集到文章")
            except Exception as e:
                print(f"  [ERROR] 采集异常: {e}")
                continue

        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1

    print(f"\n📊 采集: {stats['success']} 源成功, {stats['failed']} 源失败, 共 {len(all_articles)} 篇")
    return all_articles


def main():
    """全流程主入口"""
    start_time = datetime.utcnow()
    print("=" * 60)
    print(f"  AI Industry Digest - 全流程运行")
    print(f"  时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 加载配置
    sources = load_sources()
    print(f"\n📋 信息源: {len(sources)} 个")

    # 2. 采集
    all_articles = collect_all(sources)
    if not all_articles:
        print("\n⚠️  未采集到任何文章，流程终止")
        return

    # 3. 去重
    ai = None
    db = None
    try:
        ai = AIProcessor(batch_size=10)
    except ValueError as e:
        print(f"\n⚠️  AI 未配置: {e}")
        print("   将跳过 AI 处理步骤")

    dedup = Deduplicator(ai_processor=ai if ai else None)
    articles = dedup.deduplicate(all_articles)

    # 4. AI 处理
    if ai:
        articles = ai.process_articles(articles)
    else:
        print("\n⚠️  跳过 AI 处理（未配置 API Key）")

    # 5. 日报生成
    reporter = DailyReportGenerator(db_manager=db, ai_processor=ai)
    report = reporter.generate(articles)

    # 6. 写入数据库
    if articles:
        print(f"\n💾 写入数据库 ...")
        try:
            db = DatabaseManager()
            result = db.save_articles(articles)
            print(f"   ✅ 新增: {result['inserted']} 篇")
            print(f"   ⏭ 跳过: {result['skipped']} 篇")
            print(f"   ❌ 失败: {result['errors']} 篇")

            # 重新生成日报并写入 DB（带有 db 实例）
            reporter.db = db
            reporter.generate(articles)

            count = db.get_article_count()
            print(f"\n📦 数据库文章总数: {count}")

        except ValueError as e:
            print(f"\n❌ {e}")
        except Exception as e:
            print(f"\n❌ 数据库操作失败: {e}")

    # 7. 日报摘要输出
    print("\n" + "=" * 60)
    print(f"📋 日报摘要 - {report['report_date']}")
    print(f"   文章数: {report['total_articles']}")
    print(f"   信息源: {report['source_count']} 个")
    print(f"   关键词: {', '.join(report['trending_keywords'][:5])}")
    if report['summary_insight']:
        print(f"\n   💡 {report['summary_insight'][:200]}")
    print("=" * 60)

    # 8. 耗时统计
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    print(f"\n⏱ 总耗时: {elapsed:.1f} 秒")
    print("=" * 60)


if __name__ == "__main__":
    main()
