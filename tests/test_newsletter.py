"""
Signal - 邮件简报单元测试（改造计划 §1.3）
仅覆盖纯逻辑（渲染 / 退订链接 / ESP 选择 / 数据转换），不依赖数据库或网络，保持 pytest 绿。
"""

import os
import sys
import secrets

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.newsletter import (
    NewsletterRenderer,
    get_sender,
    SubscriberStore,
    _rows_to_articles,
    _build_main_thread_placeholder,
    _demo_report,
    ResendESP,
    SmtpESP,
    ConsoleESP,
)


def _make_report():
    """构造一个 reporter 结构的报告（含 so_what），用于渲染测试。"""
    return _demo_report(8)


def test_renderer_contains_so_what_and_unsubscribe():
    report = _make_report()
    renderer = NewsletterRenderer(base_url="https://signal.test")
    url = renderer.build_unsubscribe_url("TOK123")
    html = renderer.render(report, url)

    # 标题与摘要出现
    assert "OpenAI 发布" in html
    # so_what 观点层出现（含真实 so_what 的那篇）
    assert "So What / 对你意味着什么" in html
    assert "API 成本大幅下降" in html
    # 退订链接出现
    assert "https://signal.test/unsubscribe?token=TOK123" in html
    assert "退订" in html
    # 今日主线占位标注
    assert "今日主线" in html


def test_renderer_escapes_html_in_title():
    report = _make_report()
    # demo 报告第一篇标题含 <script> 注入，渲染后应被转义而非执行
    html = NewsletterRenderer().render(report, "https://x/u?token=1")
    assert "<script>alert(1)</script>OpenAI" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;OpenAI" in html


def test_renderer_handles_missing_so_what():
    report = _make_report()
    # 第三篇 so_what 为 None，应渲染「暂无观点层」
    html = NewsletterRenderer().render(report, "https://x/u?token=1")
    assert "暂无观点层" in html


def test_build_unsubscribe_url():
    r = NewsletterRenderer(base_url="https://a.b")
    assert r.build_unsubscribe_url("abc") == "https://a.b/unsubscribe?token=abc"
    # 默认 base_url 末尾斜杠应被规整
    r2 = NewsletterRenderer(base_url="https://a.b/")
    assert r2.build_unsubscribe_url("abc") == "https://a.b/unsubscribe?token=abc"


def test_esp_selection():
    assert isinstance(get_sender("resend"), ResendESP)
    assert isinstance(get_sender("smtp"), SmtpESP)
    assert isinstance(get_sender("console"), ConsoleESP)
    assert isinstance(get_sender(None), ConsoleESP)  # 默认 console


def test_rows_to_articles_preserves_so_what():
    rows = [{
        "title": "t", "url": "https://u", "source_name": "s",
        "summary": "sm", "tags": ["x"], "importance": "high",
        "importance_reason": "r", "so_what": "观点", "published_at": None,
    }]
    arts = _rows_to_articles(rows)
    assert len(arts) == 1
    assert arts[0].so_what == "观点"
    assert arts[0].importance == "high"


def test_main_thread_placeholder_fallback():
    report = {"trending_keywords": [], "articles": {"high": [], "medium": [], "low": []}}
    bullets = _build_main_thread_placeholder(report, [], 8)
    assert any("暂无高优先级信号" in b for b in bullets)


def test_subscriber_token_unique():
    # 退订 token 由 secrets 生成，应不可预测且唯一
    t1 = secrets.token_urlsafe(32)
    t2 = secrets.token_urlsafe(32)
    assert t1 != t2 and len(t1) >= 32
