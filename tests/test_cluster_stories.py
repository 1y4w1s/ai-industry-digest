"""
Signal - 事件聚类单元测试（改造计划 §2.1）
仅覆盖纯逻辑（聚类分组 / 跨 24h 同事件合并 / 空输入降级 / 确定性 / 无误合并 / 热度排序 / 邮件集成），
不依赖数据库或 LLM，保持 pytest 绿。
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, date, timezone

from collector.base import Article
from processor.reporter import (
    cluster_stories,
    _extract_entities,
    _title_tokens,
)
from scripts.newsletter import _demo_report, NewsletterRenderer


def _art(title, url, src="S", summary="", tags=None, imp="low",
          pa=None, so_what=None):
    return Article(
        title=title, url=url, source_name=src, raw_content="",
        summary=summary, tags=tags or [], importance=imp,
        importance_reason="", so_what=so_what,
        published_at=pa or datetime(2026, 7, 10, 9, 0, tzinfo=timezone.utc),
    )


# ── 实体抽取 ──────────────────────────────
def test_extract_entities_gpt_and_fable():
    assert "GPT" in _extract_entities("OpenAI 发布 GPT-6，推理成本下降")
    assert "Fable" in _extract_entities("Fable-5.1 对比稿出炉")


def test_extract_entities_meta_word_boundary():
    # \bmeta\b 不应误中 metadata / meta-learning
    assert "Meta" not in _extract_entities("metadata 字段说明")
    assert "Meta" in _extract_entities("Meta 发布新模型")


def test_title_tokens_drops_stopwords():
    toks = _title_tokens("OpenAI 发布 GPT-6 模型")
    assert "发布" not in toks  # 高频噪声词被剔除
    assert "gpt" in toks or "gpt-6" in toks


# ── 聚类分组：同一事件多报道合并 ──────────────
def test_same_event_two_reports_merge():
    arts = [
        _art("OpenAI 发布 GPT-6，推理成本下降 70%", "https://e.com/1",
              "机器之心", "OpenAI 今日发布 GPT-6。", ["大模型", "OpenAI"], "high"),
        _art("媒体解读：GPT-6 到底意味着什么", "https://e.com/2",
              "量子位", "我们拆解了 GPT-6 的能力边界。",
              ["解读", "大模型"], "medium",
              datetime(2026, 7, 10, 20, 0, tzinfo=timezone.utc)),
    ]
    r = cluster_stories(arts, date(2026, 7, 10))
    assert r["total_stories"] == 1
    s = r["stories"][0]
    assert s["entity"] == "GPT"
    assert set(s["article_ids"]) == {"https://e.com/1", "https://e.com/2"}
    # 挂文列表应包含两篇标题
    hung = {a["title"] for a in s["articles"]}
    assert "OpenAI 发布 GPT-6，推理成本下降 70%" in hung
    assert "媒体解读：GPT-6 到底意味着什么" in hung


def test_gpt6_fable_merge():
    """验收抽测：GPT-6 发布 + Fable-5.1 对比稿（对比稿提及 GPT-6）应并到同一条主线。"""
    arts = [
        _art("OpenAI 发布 GPT-6，推理成本下降 70%", "https://e.com/g",
              "机器之心", "OpenAI 今日发布 GPT-6。", ["大模型", "OpenAI"], "high"),
        _art("Fable-5.1 对比稿：和 GPT-6 谁更强", "https://e.com/f",
              "量子位", "我们把 Fable-5.1 与 GPT-6 拉来对比实测。",
              ["对比", "大模型"], "medium",
              datetime(2026, 7, 10, 22, 0, tzinfo=timezone.utc)),
    ]
    r = cluster_stories(arts, date(2026, 7, 10))
    assert r["total_stories"] == 1
    s = r["stories"][0]
    assert s["entity"] == "GPT"
    assert set(s["article_ids"]) == {"https://e.com/g", "https://e.com/f"}


def test_cross_24h_same_event_merge():
    """跨 24h 内的同事件报道也应被合并。"""
    arts = [
        _art("GPT-6 今日发布", "https://e.com/a",
              "机器之心", "OpenAI 发布 GPT-6。", ["OpenAI"], "high",
              datetime(2026, 7, 10, 8, 0, tzinfo=timezone.utc)),
        _art("一天后，关于 GPT-6 的深度评论", "https://e.com/b",
              "量子位", "GPT-6 发布后业界怎么看。", ["评论"], "medium",
              datetime(2026, 7, 10, 23, 0, tzinfo=timezone.utc)),
    ]
    r = cluster_stories(arts, date(2026, 7, 10))
    assert r["total_stories"] == 1
    assert set(r["stories"][0]["article_ids"]) == {"https://e.com/a", "https://e.com/b"}


# ── 空输入降级 ──────────────────────────────
def test_empty_input_degrades():
    r = cluster_stories([], date(2026, 7, 10))
    assert r["total_stories"] == 0
    assert r["stories"] == []
    assert r["report_date"] == "2026-07-10"


def test_singleton_story():
    arts = [_art("百度发布文心 5.0", "https://e.com/1", "36氪",
                   "百度文心 5.0 上新。", ["百度"], "low")]
    r = cluster_stories(arts, date(2026, 7, 10))
    assert r["total_stories"] == 1
    s = r["stories"][0]
    assert s["title"] == "百度发布文心 5.0"
    assert s["article_ids"] == ["https://e.com/1"]


# ── 无误合并 ────────────────────────────────
def test_no_false_merge():
    """不相关的实体不应被误并到同一条主线。"""
    arts = [
        _art("百度发布文心 5.0", "https://e.com/1", "36氪",
              "百度文心 5.0 上新。", ["百度"], "low"),
        _art("特斯拉发布新车型", "https://e.com/2", "Reuters",
              "Tesla 新车型亮相。", [], "low"),
        _art("OpenAI 发布 GPT-6", "https://e.com/3", "机器之心",
              "GPT-6 来了。", ["OpenAI"], "high"),
    ]
    r = cluster_stories(arts, date(2026, 7, 10))
    # 3 条互不相关 → 3 条主线
    assert r["total_stories"] == 3
    titles = {s["title"] for s in r["stories"]}
    assert "百度发布文心 5.0" in titles
    assert "特斯拉发布新车型" in titles
    assert "OpenAI 发布 GPT-6" in titles


# ── 确定性可复现 ─────────────────────────────
def test_deterministic_same_input_same_output():
    arts = [
        _art("OpenAI 发布 GPT-6", "https://e.com/1", "机器之心",
              "GPT-6 发布。", ["OpenAI"], "high"),
        _art("Fable-5.1 对比 GPT-6", "https://e.com/2", "量子位",
              "Fable-5.1 与 GPT-6 对比。", ["对比"], "medium"),
        _art("百度文心 5.0 发布", "https://e.com/3", "36氪",
              "文心 5.0。", ["百度"], "low"),
    ]
    r1 = cluster_stories(arts, date(2026, 7, 10))
    r2 = cluster_stories(arts, date(2026, 7, 10))
    assert json.dumps(r1, ensure_ascii=False, sort_keys=True) == \
        json.dumps(r2, ensure_ascii=False, sort_keys=True)


# ── 热度排序 ───────────────────────────────
def test_heat_ordering():
    """高重要性事件的主线应排在低重要性之前。"""
    arts = [
        _art("小厂融资 100 万", "https://e.com/low", "小报",
              "某小厂融资。", ["融资"], "low"),
        _art("OpenAI 发布 GPT-6（重磅）", "https://e.com/high", "机器之心",
              "GPT-6 重磅发布。", ["OpenAI"], "high"),
    ]
    r = cluster_stories(arts, date(2026, 7, 10))
    assert r["total_stories"] == 2
    # 高重要性（heat 更大）排第一
    assert r["stories"][0]["entity"] == "GPT"
    assert r["stories"][0]["heat"] > r["stories"][1]["heat"]


# ── 邮件集成：今日主线从占位升级为真实聚类 ──
def test_demo_report_uses_real_cluster():
    rep = _demo_report(8)
    assert isinstance(rep.get("main_stories"), dict)
    assert "stories" in rep["main_stories"]
    # main_thread 不再是以「热度关键词」开头的占位串
    mt = rep.get("main_thread") or []
    assert not any(b.startswith("热度关键词") for b in mt)
    # 每篇挂文带 url 与 source_name（供邮件渲染）
    for s in rep["main_stories"]["stories"]:
        for a in s["articles"]:
            assert a["url"] and a["source_name"]


def test_renderer_shows_cluster_not_placeholder():
    rep = _demo_report(8)
    html = NewsletterRenderer(base_url="https://signal.test").render(
        rep, "https://signal.test/unsubscribe?token=T")
    # 聚类已上线：旧的占位说明语不应再出现
    assert "事件聚类即将上线" not in html
    assert "事件聚类自动生成" in html
    # 至少展示一条真实主线标题 + 其挂文链接
    assert "今日主线" in html
    assert "https://example.com/1" in html
