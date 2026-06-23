"""
Signal - 全流程运行入口
采集 → 去重 → AI 处理 → 日报生成 → 入库
"""

import os
import sys
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collector.base import Article
from collector.rss_collector import RSSCollector
from collector.arxiv_collector import ArxivCollector
from collector.hf_collector import HFCollector
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
        elif api_type == "huggingface":
            return HFCollector(source_config)
    return None


def _collect_single_source(source_config: dict) -> tuple:
    """采集单个信息源（含 fallback 逻辑），供并发调用"""
    name = source_config.get("name", "unknown")
    print(f"\n--- {name} ---")
    collectors = source_config.get("collectors", [])

    for idx, coll_cfg in enumerate(collectors):
        if idx > 0:
            print(f"  [FALLBACK] 尝试备用方式: {coll_cfg.get('type')}")
        collector = create_collector(source_config, coll_cfg.get("type"))
        if not collector:
            continue

        try:
            articles = collector.collect()
            if articles:
                print(f"  ✅ 采集到 {len(articles)} 篇")
                return (name, articles, True)
            else:
                print(f"  [EMPTY] 未采集到文章")
        except Exception as e:
            print(f"  [ERROR] 采集异常: {e}")
            continue

    return (name, [], False)


def collect_all(sources: List[dict]) -> List[Article]:
    """并发采集所有信息源"""
    worker_count = min(len(sources), 4)
    print(f"\n🚀 并发采集: {len(sources)} 个信息源 (max_workers={worker_count})")

    all_articles: List[Article] = []
    stats = {"success": 0, "failed": 0}
    start_ts = time.time()

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(_collect_single_source, src): src for src in sources}
        for fut in as_completed(futures):
            try:
                name, articles, success = fut.result()
                if success:
                    all_articles.extend(articles)
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                name = futures[fut].get("name", "unknown")
                print(f"\n  [ERROR] {name} 采集线程异常: {e}")
                stats["failed"] += 1

    elapsed = time.time() - start_ts
    print(f"\n📊 采集: {stats['success']} 源成功, {stats['failed']} 源失败, 共 {len(all_articles)} 篇 (耗时 {elapsed:.1f}s)")
    return all_articles


def _process_with_retry(ai: AIProcessor, articles: List[Article], max_retries: int = 2) -> List[Article]:
    """带指数退避重试的 AI 处理
    确保即使 AI 处理完全崩溃，也能继续后续入库流程
    """
    article_count = len(articles)
    print(f"\n--- AI 处理重试模块 ---")
    print(f"  待处理: {article_count} 篇 | 最大重试: {max_retries} 次")

    for attempt in range(max_retries + 1):
        attempt_label = f"第 {attempt + 1} 次"
        if attempt > 0:
            attempt_label += "（重试）"
        print(f"  ▶ 开始{attempt_label}尝试...")
        start_ts = time.time()

        try:
            result = ai.process_articles(articles)
            elapsed = time.time() - start_ts
            if attempt > 0:
                print(f"  ✅ 重试成功! 耗时 {elapsed:.1f}s，处理 {len(result)} 篇")
            else:
                print(f"  ✅ 首次处理完成，耗时 {elapsed:.1f}s，处理 {len(result)} 篇")
            return result
        except Exception as e:
            elapsed = time.time() - start_ts
            print(f"  ❌ 第 {attempt + 1} 次尝试失败 (耗时 {elapsed:.1f}s)")
            print(f"    异常类型: {type(e).__name__}")
            print(f"    异常信息: {e}")
            if attempt < max_retries:
                wait = 2 ** (attempt + 2)  # 4s, 8s
                print(f"  ⏳ 等待 {wait}s 后进行第 {attempt + 2} 次重试...")
                time.sleep(wait)
            else:
                print(f"  ⚠️  重试次数已耗尽（共尝试 {max_retries + 1} 次）")
                print(f"  ⚠️  跳过 AI 处理，为 {article_count} 篇文章设置默认值后继续入库")
                for article in articles:
                    if article.summary is None:
                        article.summary = f"[AI处理失败] {article.title}"
                    if not article.tags:
                        article.tags = ["其他"]
                    if article.importance is None:
                        article.importance = "low"
                    if article.importance_reason is None:
                        article.importance_reason = "AI 处理失败，使用默认值"
                print(f"  📝  已为 {article_count} 篇填充默认摘要/标签/重要性")
    return articles


def main():
    """全流程主入口"""
    start_time = datetime.utcnow()
    print("=" * 60)
    print(f"  Signal - 全流程运行")
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

    # 4. AI 处理（带重试兜底）
    if ai:
        articles = _process_with_retry(ai, articles)
    else:
        print("\n⚠️  跳过 AI 处理（未配置 API Key）")

    # 5. 日报生成（按采集日期，每篇标注原始 published_at）
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
            report = reporter.generate(articles)

            count = db.get_article_count()
            print(f"\n📦 数据库文章总数: {count}")

        except ValueError as e:
            print(f"\n❌ {e}")
        except Exception as e:
            print(f"\n❌ 数据库操作失败: {e}")

    # 7. 日报摘要输出
    print("\n" + "=" * 60)
    print(f"📋 {report['report_date']} 日报摘要")
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

    # 9. 自动导入知识库（可选，通过环境变量 KB_IMPORT=true 启用）
    if os.getenv("KB_IMPORT", "").lower() in ("true", "1", "yes"):
        print("\n" + "=" * 60)
        print("  📚 正在导入知识库...")
        print("=" * 60)
        try:
            from scripts.import_to_kb import import_articles
            from_date = (date.today() - timedelta(days=1)).isoformat()
            to_date = date.today().isoformat()
            import_articles(from_date=from_date, to_date=to_date)
        except ImportError as e:
            print(f"  [WARN] 知识库导入模块加载失败: {e}")
        except Exception as e:
            print(f"  [WARN] 知识库导入失败: {e}")


if __name__ == "__main__":
    main()
