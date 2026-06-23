"""
Signal - AI 处理重试逻辑单元测试
验证 _process_with_retry 的 try-catch、指数退避、默认值填充行为

运行: python -m pytest tests/test_retry.py -v
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch
import pytest

from collector.base import Article


def _make_articles(count=3):
    """创建测试用文章列表（AI 字段均为 None）"""
    return [
        Article(
            title=f"Test Article {i}",
            url=f"https://test.com/{i}",
            source_name="test",
            raw_content=f"content {i}",
        )
        for i in range(count)
    ]


class TestProcessWithRetry:
    """_process_with_retry 重试 + 兜底逻辑"""

    @patch("run.AIProcessor")
    def test_first_attempt_success(self, mock_processor_class):
        """首次尝试成功，不触发重试"""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        articles = _make_articles(3)
        mock_processor.process_articles.return_value = articles

        from run import _process_with_retry
        result = _process_with_retry(mock_processor, articles)

        assert len(result) == 3
        mock_processor.process_articles.assert_called_once()

    @patch("run.AIProcessor")
    def test_retry_success(self, mock_processor_class):
        """首次失败，重试成功，验证指数退避等待"""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        articles = _make_articles(3)
        # 第一次抛异常，第二次成功
        mock_processor.process_articles.side_effect = [
            Exception("API timeout"),
            articles,
        ]

        from run import _process_with_retry
        start = time.time()
        result = _process_with_retry(mock_processor, articles)
        elapsed = time.time() - start

        assert len(result) == 3
        assert mock_processor.process_articles.call_count == 2
        # 指数退避：2^(0+2)=4s ≤ 耗时
        assert elapsed >= 3.5, f"指数退避未生效! 耗时仅 {elapsed:.2f}s"

    @patch("run.AIProcessor")
    def test_all_retries_fail_default_values(self, mock_processor_class):
        """所有重试失败，文章应填充默认值后返回"""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        articles = _make_articles(3)
        # 每次都失败
        mock_processor.process_articles.side_effect = Exception("API down")

        from run import _process_with_retry
        result = _process_with_retry(mock_processor, articles)

        assert len(result) == 3
        # 共尝试 3 次（max_retries=2）
        assert mock_processor.process_articles.call_count == 3

        # 验证默认值填充
        for article in result:
            assert article.summary == f"[AI处理失败] {article.title}"
            assert article.tags == ["其他"]
            assert article.importance == "low"
            assert article.importance_reason == "AI 处理失败，使用默认值"

    @patch("run.AIProcessor")
    def test_empty_articles(self, mock_processor_class):
        """空文章列表应调用一次后返回空"""
        mock_processor = MagicMock()
        mock_processor.process_articles.return_value = []
        mock_processor_class.return_value = mock_processor

        from run import _process_with_retry
        result = _process_with_retry(mock_processor, [])

        assert result == []
        mock_processor.process_articles.assert_called_once()

    @patch("run.AIProcessor")
    def test_existing_fields_preserved(self, mock_processor_class):
        """文章已有 AI 字段时，失败后不应覆盖已有值"""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        articles = _make_articles(2)
        # 文章 0：已有部分字段
        articles[0].summary = "已有摘要"
        articles[0].tags = ["技术突破"]
        articles[0].importance = "high"
        articles[0].importance_reason = "已分析"
        # 文章 1：全部为 None

        mock_processor.process_articles.side_effect = Exception("API down")

        from run import _process_with_retry
        result = _process_with_retry(mock_processor, articles)

        # 文章 0：已有字段应保留
        assert result[0].summary == "已有摘要"
        assert result[0].tags == ["技术突破"]
        assert result[0].importance == "high"
        assert result[0].importance_reason == "已分析"

        # 文章 1：填充默认值
        assert result[1].summary == "[AI处理失败] Test Article 1"
        assert result[1].tags == ["其他"]
        assert result[1].importance == "low"

    @patch("run.AIProcessor")
    def test_custom_max_retries(self, mock_processor_class):
        """自定义 max_retries 参数生效"""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        mock_processor.process_articles.side_effect = Exception("err")

        from run import _process_with_retry
        # max_retries=1 → 共 2 次尝试
        result = _process_with_retry(mock_processor, _make_articles(2), max_retries=1)

        assert len(result) == 2
        assert mock_processor.process_articles.call_count == 2
