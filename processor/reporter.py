"""
AI Industry Digest - 日报生成器
按重要性分组、提取热点关键词、生成概览、写入数据库
"""

from datetime import date, datetime
from typing import List, Dict, Tuple
from collections import Counter
import json

from collector.base import Article
from processor.ai_processor import AIProcessor


class DailyReportGenerator:
    """日报生成器"""

    def __init__(self, db_manager=None, ai_processor: AIProcessor = None):
        """
        Args:
            db_manager: DatabaseManager 实例
            ai_processor: AIProcessor 实例
        """
        self.db = db_manager
        self.ai = ai_processor

    def generate(self, articles: List[Article], report_date: date = None) -> dict:
        """生成日报数据
        Returns:
            dict: 日报数据，包含概览、分组文章、关键词等
        """
        if not articles:
            return self._empty_report(report_date)

        report_date = report_date or date.today()
        print(f"\n📰 生成日报: {report_date}")

        # 1. 按重要性分组
        grouped = self._group_by_importance(articles)
        print(f"   高: {len(grouped['high'])} | 中: {len(grouped['medium'])} | 低: {len(grouped['low'])}")

        # 2. 提取热点关键词
        keywords = self._extract_keywords(articles)
        print(f"   热点关键词: {', '.join(keywords[:5])}")

        # 3. 生成概览
        insight = ""
        if self.ai:
            try:
                insight = self.ai.generate_summary_insight(articles)
                print(f"   概览已生成")
            except Exception as e:
                print(f"   [WARN] 概览生成失败: {e}")
                insight = self._generate_fallback_insight(articles)

        # 4. 构建日报数据
        report = {
            "report_date": report_date.isoformat(),
            "total_articles": len(articles),
            "source_count": len(set(a.source_name for a in articles)),
            "summary_insight": insight,
            "trending_keywords": keywords[:10],
            "articles": {
                "high": self._serialize_articles(grouped["high"]),
                "medium": self._serialize_articles(grouped["medium"]),
                "low": self._serialize_articles(grouped["low"]),
            }
        }

        # 5. 写入数据库
        if self.db:
            try:
                self._save_to_db(report, articles)
                print(f"   💾 日报已写入数据库")
            except Exception as e:
                print(f"   [ERROR] 写入数据库失败: {e}")

        return report

    # ── 按重要性分组 ──────────────────────────

    def _group_by_importance(self, articles: List[Article]) -> Dict[str, List[Article]]:
        """按重要性分组"""
        groups = {"high": [], "medium": [], "low": []}
        for a in articles:
            imp = a.importance or "low"
            if imp in groups:
                groups[imp].append(a)
            else:
                groups["low"].append(a)
        return groups

    # ── 提取热点关键词 ────────────────────────

    def _extract_keywords(self, articles: List[Article]) -> List[str]:
        """从文章标签和标题中提取热点关键词"""
        tag_counter = Counter()
        word_counter = Counter()

        # 统计标签
        for a in articles:
            for tag in (a.tags or []):
                tag_counter[tag] += 1

        # 从标题中提取关键词（取高频词）
        import jieba
        import re
        # 停用词表（精简版）
        stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不",
                      "人", "都", "一", "一个", "上", "也", "很", "到",
                      "说", "要", "去", "你", "会", "着", "没有", "看",
                      "好", "自己", "这", "他", "她", "它", "们", "与",
                      "及", "或", "等", "从", "被", "把", "对", "为",
                      "the", "a", "an", "and", "or", "for", "of", "in",
                      "to", "is", "it", "on", "with", "by", "as", "at",
                      "that", "this", "from", "are", "was", "be", "has",
                      "have", "not", "but", "we", "its", "their"}

        def is_meaningful_word(w: str) -> bool:
            """判断是否为有意义的词：中文词（长度>=2）或英文词（长度>=4）"""
            if not w:
                return False
            if re.match(r'^[\u4e00-\u9fff]+$', w):  # 中文
                return len(w) >= 2
            if re.match(r'^[a-zA-Z]+$', w):  # 英文
                return len(w) >= 4
            return False

        for a in articles:
            words = jieba.lcut(a.title)
            for w in words:
                w = w.strip().lower()
                if is_meaningful_word(w) and w not in stop_words:
                    word_counter[w] += 1

        # 合并标签和标题关键词
        combined = tag_counter + word_counter
        # 过滤掉单次出现的词
        keywords = [w for w, c in combined.most_common(20) if c >= 2]
        return keywords[:10] if keywords else [w for w, _ in combined.most_common(10)]

    # ── 概览（备选） ─────────────────────────

    def _generate_fallback_insight(self, articles: List[Article]) -> str:
        """当 AI 概览失败时，用规则生成简单概览"""
        high_count = sum(1 for a in articles if a.importance == "high")
        sources = set(a.source_name for a in articles)
        keywords = self._extract_keywords(articles)

        insight = (
            f"今日共收录 {len(articles)} 篇文章，"
            f"覆盖 {len(sources)} 个信息源，"
            f"其中高重要性文章 {high_count} 篇。"
        )
        if keywords:
            insight += f" 热点关键词: {'、'.join(keywords[:5])}。"
        return insight

    # ── 序列化 ─────────────────────────────

    def _serialize_articles(self, articles: List[Article]) -> List[dict]:
        """将 Article 对象转为可 JSON 序列化的字典"""
        return [
            {
                "title": a.title,
                "url": a.url,
                "source_name": a.source_name,
                "summary": a.summary or "",
                "tags": a.tags or [],
                "importance": a.importance or "low",
                "reason": a.importance_reason or "",
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ]

    # ── 写入数据库 ─────────────────────────

    def _save_to_db(self, report: dict, articles: List[Article]):
        """将日报写入 daily_reports 表"""
        if not self.db:
            return

        # 从数据库查询文章的 UUID
        article_uuids = []
        for article in articles:
            try:
                result = self.db.client.table("articles") \
                    .select("id") \
                    .eq("url", article.url) \
                    .execute()
                if result.data:
                    article_uuids.append(result.data[0]["id"])
            except Exception:
                pass

        data = {
            "report_date": report["report_date"],
            "article_ids": article_uuids if article_uuids else None,
            "summary_insight": report["summary_insight"],
            "trending_keywords": report["trending_keywords"],
            "trend_analysis": "",
        }
        self.db.client.table("daily_reports").upsert(
            data,
            on_conflict="report_date"
        ).execute()

    # ── 空日报 ─────────────────────────────

    def _empty_report(self, report_date: date = None) -> dict:
        """生成空日报"""
        report_date = report_date or date.today()
        return {
            "report_date": report_date.isoformat(),
            "total_articles": 0,
            "source_count": 0,
            "summary_insight": "今日暂无收录内容。",
            "trending_keywords": [],
            "articles": {"high": [], "medium": [], "low": []}
        }
