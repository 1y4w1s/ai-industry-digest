"""
Signal - 去重管道
三层去重：URL 精确去重 → 标题相似度去重 → AI 辅助去重
"""

from typing import List, Dict, Tuple
from difflib import SequenceMatcher

from collector.base import Article


class Deduplicator:
    """三层去重管道"""

    # 标题相似度阈值
    FUZZY_THRESHOLD = 0.85       # > 85% 确定为同一事件
    AI_THRESHOLD_MIN = 0.70     # 70%-85% 需 AI 判断
    AI_THRESHOLD_MAX = 0.85

    def __init__(self, ai_processor=None):
        """
        Args:
            ai_processor: AIProcessor 实例（用于第三层 AI 去重）
        """
        self.ai = ai_processor

    def deduplicate(self, articles: List[Article]) -> List[Article]:
        """三层去重主入口"""
        if not articles:
            return []

        print(f"\n🔍 去重管道: 输入 {len(articles)} 篇文章")

        # 第一层：URL 精确去重
        articles = self._dedup_by_url(articles)
        print(f"  第一层(URL精确): {len(articles)} 篇")

        # 第二层：标题相似度去重
        articles, fuzzy_duplicates = self._dedup_by_title(articles)
        print(f"  第二层(标题相似度): {len(articles)} 篇 (合并 {len(fuzzy_duplicates)} 组)")

        # 第三层：AI 辅助去重（仅对模糊区间内的文章）
        if self.ai and fuzzy_duplicates:
            articles = self._dedup_by_ai(articles, fuzzy_duplicates)
            print(f"  第三层(AI辅助): {len(articles)} 篇")

        print(f"  去重完成: {len(articles)} 篇")
        return articles

    # ── 第一层：URL 精确去重 ──────────────────────

    def _dedup_by_url(self, articles: List[Article]) -> List[Article]:
        """URL 精确去重：相同 URL 只保留第一篇"""
        seen_urls: set = set()
        unique: List[Article] = []

        for article in articles:
            url = article.url.strip().rstrip("/")
            if url not in seen_urls:
                seen_urls.add(url)
                unique.append(article)
            # 相同 URL 直接丢弃

        return unique

    # ── 第二层：标题相似度去重 ──────────────────

    def _dedup_by_title(self, articles: List[Article]) -> Tuple[List[Article], List[Tuple[Article, Article]]]:
        """标题相似度去重
        返回:
            - 去重后的文章列表
            - 需要 AI 进一步判断的模糊配对列表
        """
        unique: List[Article] = []
        fuzzy_pairs: List[Tuple[Article, Article]] = []

        for article in articles:
            matched = False
            for existing in unique:
                similarity = self._title_similarity(article.title, existing.title)

                if similarity >= self.FUZZY_THRESHOLD:
                    # 确定为同一事件：合并，保留信息更丰富的
                    self._merge_articles(existing, article)
                    matched = True
                    break

                elif similarity >= self.AI_THRESHOLD_MIN:
                    # 模糊区间：记录待 AI 判断
                    fuzzy_pairs.append((existing, article))
                    matched = True
                    break

            if not matched:
                unique.append(article)

        return unique, fuzzy_pairs

    def _title_similarity(self, title_a: str, title_b: str) -> float:
        """计算两个标题的相似度 (0.0 - 1.0)"""
        # 使用 SequenceMatcher（简单有效）
        return SequenceMatcher(None, title_a.lower(), title_b.lower()).ratio()

    def _merge_articles(self, target: Article, source: Article):
        """合并两篇同一事件的文章，保留更完整的信息"""
        # 如果 target 没有正文，用 source 的
        if not target.raw_content and source.raw_content:
            target.raw_content = source.raw_content

        # 记录来源
        if source.url not in target.source_refs:
            target.source_refs.append(source.url)

        # 如果 target 没有发布时间，用 source 的
        if not target.published_at and source.published_at:
            target.published_at = source.published_at

    # ── 第三层：AI 辅助去重 ──────────────────────

    def _dedup_by_ai(self, articles: List[Article],
                     fuzzy_pairs: List[Tuple[Article, Article]]) -> List[Article]:
        """AI 判断模糊配对是否为同一事件"""
        merged_indices: set = set()

        for existing, new_article in fuzzy_pairs:
            try:
                is_dup = self.ai.judge_duplicate(
                    existing.title, new_article.title
                )
                if is_dup:
                    self._merge_articles(existing, new_article)
                    # 标记新文章已被合并
                    if new_article in articles:
                        merged_indices.add(articles.index(new_article))
            except Exception as e:
                print(f"  [WARN] AI 去重判断失败: {e}")
                continue

        # 过滤掉已被合并的文章
        result = [
            a for i, a in enumerate(articles)
            if i not in merged_indices
        ]
        return result
