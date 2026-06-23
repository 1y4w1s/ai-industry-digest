"""
Signal - 并发采集逻辑单元测试
验证 _collect_single_source 的容错/fallback 机制和 collect_all 的并发行为

运行: python -m pytest tests/test_collect.py -v
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch, ANY
import pytest

from collector.base import Article


# ── 测试辅助函数 ──────────────────────────────────

def _make_source(name, collectors=None):
    """创建测试用信息源配置"""
    if collectors is None:
        collectors = [{"type": "rss", "url": "https://test.com/rss"}]
    return {
        "name": name,
        "id": f"test-{name.lower()}",
        "collectors": collectors,
        "enabled": True,
    }


def _make_articles(count=3, prefix=""):
    """创建测试用文章列表"""
    return [
        Article(
            title=f"{prefix}Article {i}",
            url=f"https://test.com/{prefix}{i}",
            source_name=prefix or "test",
            raw_content=f"content {prefix}{i}",
        )
        for i in range(count)
    ]


# ── _collect_single_source 测试 ─────────────────

class TestSingleSource:
    """单源采集逻辑"""

    @patch("run.create_collector")
    def test_success(self, mock_create):
        """正常采集返回文章列表和成功状态"""
        articles = _make_articles(3)
        mock_collector = MagicMock()
        mock_collector.collect.return_value = articles
        mock_create.return_value = mock_collector

        from run import _collect_single_source
        name, result, success = _collect_single_source(_make_source("SourceA"))

        assert success is True
        assert len(result) == 3
        assert name == "SourceA"
        mock_collector.collect.assert_called_once()

    @patch("run.create_collector")
    def test_empty(self, mock_create):
        """采集到空列表返回成功=False"""
        mock_collector = MagicMock()
        mock_collector.collect.return_value = []
        mock_create.return_value = mock_collector

        from run import _collect_single_source
        *_, success = _collect_single_source(_make_source("EmptySource"))

        assert success is False

    @patch("run.create_collector")
    def test_exception(self, mock_create):
        """采集抛出异常返回成功=False"""
        mock_collector = MagicMock()
        mock_collector.collect.side_effect = ConnectionError("network error")
        mock_create.return_value = mock_collector

        from run import _collect_single_source
        *_, success = _collect_single_source(_make_source("BadSource"))

        assert success is False

    @patch("run.create_collector")
    def test_fallback_success(self, mock_create):
        """主方式失败后 fallback 到备用方式"""
        articles = _make_articles(2)
        mock_rss = MagicMock()
        mock_rss.collect.side_effect = TimeoutError("rss timeout")
        mock_api = MagicMock()
        mock_api.collect.return_value = articles

        # create_collector 按调用顺序返回不同的 mock
        mock_create.side_effect = [mock_rss, mock_api]

        source = _make_source("FallbackSource", [
            {"type": "rss"},
            {"type": "api", "api_type": "arxiv"},
        ])

        from run import _collect_single_source
        name, result, success = _collect_single_source(source)

        assert success is True
        assert len(result) == 2
        # 验证 fallback 被调用
        assert mock_create.call_count == 2

    @patch("run.create_collector")
    def test_all_collectors_fail(self, mock_create):
        """所有采集方式都失败返回成功=False"""
        mock_rss = MagicMock()
        mock_rss.collect.side_effect = Exception("fail")
        mock_api = MagicMock()
        mock_api.collect.side_effect = Exception("also fail")
        mock_create.side_effect = [mock_rss, mock_api]

        source = _make_source("AllBad", [
            {"type": "rss"},
            {"type": "api", "api_type": "arxiv"},
        ])

        from run import _collect_single_source
        *_, success = _collect_single_source(source)

        assert success is False


# ── collect_all 并发采集测试 ─────────────────

class TestCollectAll:
    """并发采集整体流程"""

    @patch("run.create_collector")
    def test_all_success(self, mock_create):
        """多个信息源全部采集成功"""
        def collector_side_effect(config, collector_type=None):
            name = config.get("name", "")
            mock = MagicMock()
            if name == "SourceA":
                mock.collect.return_value = _make_articles(3, "A")
            elif name == "SourceB":
                mock.collect.return_value = _make_articles(2, "B")
            elif name == "SourceC":
                mock.collect.return_value = _make_articles(4, "C")
            return mock

        mock_create.side_effect = collector_side_effect

        sources = [
            _make_source("SourceA"),
            _make_source("SourceB"),
            _make_source("SourceC"),
        ]

        from run import collect_all
        articles = collect_all(sources)

        # 所有文章应被收集
        assert len(articles) == 9  # 3+2+4
        titles = [a.title for a in articles]
        assert "AArticle 0" in titles
        assert "BArticle 0" in titles
        assert "CArticle 0" in titles

    @patch("run.create_collector")
    def test_partial_failure(self, mock_create):
        """部分源失败不影响其他源"""
        def collector_side_effect(config, collector_type=None):
            name = config.get("name", "")
            mock = MagicMock()
            if name == "GoodSource":
                mock.collect.return_value = _make_articles(2, "Good")
            elif name == "BadSource":
                mock.collect.side_effect = Exception("crash")
            else:
                mock.collect.return_value = _make_articles(1, "Other")
            return mock

        mock_create.side_effect = collector_side_effect

        sources = [
            _make_source("GoodSource"),
            _make_source("BadSource"),
            _make_source("OtherSource"),
        ]

        from run import collect_all
        articles = collect_all(sources)

        # 错误的源被跳过，正常的源仍能入库
        assert len(articles) == 3  # 2 + 1
        assert all("Bad" not in a.title for a in articles)

    @patch("run.create_collector")
    def test_all_fail(self, mock_create):
        """所有源都失败返回空列表"""
        mock_collector = MagicMock()
        mock_collector.collect.side_effect = Exception("network down")
        mock_create.return_value = mock_collector

        from run import collect_all
        articles = collect_all([_make_source("A"), _make_source("B")])

        assert len(articles) == 0

    @patch("run.create_collector")
    def test_concurrent_execution(self, mock_create):
        """多个源并发采集，总耗时远小于串行耗时之和"""
        delay = 0.4  # 每个源模拟 400ms 网络延迟

        def delayed_collector(config, collector_type=None):
            mock = MagicMock()
            def _delayed():
                time.sleep(delay)
                return _make_articles(2, config.get("name", "")[:3])
            mock.collect.side_effect = _delayed
            return mock

        mock_create.side_effect = delayed_collector

        sources = [_make_source("SlowA"), _make_source("SlowB"), _make_source("SlowC")]

        from run import collect_all
        start = time.time()
        articles = collect_all(sources)
        elapsed = time.time() - start

        # 串行需要 3 * 0.4s = 1.2s；并发 4 线程应接近 0.4s
        # 留余量：断言 < 0.8s（远小于 1.2s 即证明并发）
        assert elapsed < 0.8, f"并发未生效! 耗时 {elapsed:.2f}s（串行至少 1.2s）"
        assert len(articles) == 6  # 3源 * 2篇
