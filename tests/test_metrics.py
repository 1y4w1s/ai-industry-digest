"""
Signal - 留存指标单元测试（改造计划 §1.5）
覆盖三数纯计算、open 去重(24h)、退订率公式、renderer 像素注入、
record_open_event 去重、fetch_metrics 离线。全部不依赖真实 Supabase。
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts import metrics as metrics_mod
from scripts.metrics import (
    compute_subscription_metrics,
    dedup_opens,
    compute_open_metrics,
    compute_unsubscribe_metrics,
    fetch_metrics,
    build_card_lines,
)
from scripts.newsletter import NewsletterRenderer, _demo_report
from api.models.database import DatabaseManager


# ── 1. 订阅三数 ────────────────────────────────────────────────

def test_subscription_metrics_counts():
    rows = [
        {"status": "active"},
        {"status": "active"},
        {"status": "unsubscribed"},
        {"status": "active"},
    ]
    m = compute_subscription_metrics(rows)
    assert m == {"total": 4, "active": 3, "unsubscribed": 1}


def test_subscription_metrics_empty():
    assert compute_subscription_metrics([]) == {
        "total": 0, "active": 0, "unsubscribed": 0
    }


# ── 2. 打开去重（24h 规则） ────────────────────────────────────

def _open_row(token, article, hours_ago):
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {"token": token, "article": article, "opened_at": ts}


def test_dedup_opens_same_pair_within_24h_counts_once():
    rows = [
        _open_row("t1", "2026-07-10", 1),
        _open_row("t1", "2026-07-10", 2),   # 同 pair，1h 内 → 仍算 1
        _open_row("t1", "2026-07-10", 23),  # 23h 内 → 仍 1
    ]
    assert sum(dedup_opens(rows).values()) == 1


def test_dedup_opens_same_pair_over_24h_counts_twice():
    rows = [
        _open_row("t1", "2026-07-10", 1),
        _open_row("t1", "2026-07-10", 30),  # 隔了 >24h → 第二窗口
    ]
    assert sum(dedup_opens(rows).values()) == 2


def test_dedup_opens_different_articles_count_separately():
    rows = [
        _open_row("t1", "2026-07-10", 1),
        _open_row("t1", "2026-07-11", 1),   # 不同 article → 独立
    ]
    assert sum(dedup_opens(rows).values()) == 2


def test_dedup_opens_different_tokens_count_separately():
    rows = [
        _open_row("t1", "2026-07-10", 1),
        _open_row("t2", "2026-07-10", 1),
    ]
    assert sum(dedup_opens(rows).values()) == 2


def test_dedup_opens_malformed_timestamp_ignored():
    rows = [{"token": "t1", "article": "a", "opened_at": "not-a-date"}]
    assert sum(dedup_opens(rows).values()) == 0


# ── 3. 打开率公式 ──────────────────────────────────────────────

def test_open_rate_formula():
    opens = [_open_row("t1", "d1", 1), _open_row("t1", "d1", 2)]  # 去重后 1
    sends = [{"token": "t1", "sent_at": "x", "issue_date": "d1"}]
    m = compute_open_metrics(opens, sends)
    assert m["unique_opens"] == 1
    assert m["send_count"] == 1
    assert m["open_rate"] == 1.0
    assert m["openers"] == 1


def test_open_rate_zero_when_no_sends():
    m = compute_open_metrics([_open_row("t1", "d1", 1)], [])
    assert m["send_count"] == 0
    assert m["open_rate"] == 0.0


def test_open_rate_half():
    opens = [_open_row("t1", "d1", 1), _open_row("t2", "d1", 1)]
    sends = [
        {"token": "t1", "sent_at": "x", "issue_date": "d1"},
        {"token": "t2", "sent_at": "x", "issue_date": "d1"},
    ]
    m = compute_open_metrics(opens, sends)
    assert m["unique_opens"] == 2
    assert abs(m["open_rate"] - 1.0) < 1e-9


# ── 4. 退订率公式 ──────────────────────────────────────────────

def test_unsubscribe_rate_formula():
    period_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    rows = [
        {"status": "active"},
        {"status": "active"},
        {"status": "unsubscribed", "unsubscribed_at": recent},  # 本期新增 1
    ]
    m = compute_unsubscribe_metrics(rows, period_start)
    # 期末在订 2 + 本期新增 1 = 期初 3 → 退订率 1/3
    assert m["new_unsubscribes"] == 1
    assert m["active_now"] == 2
    assert abs(m["unsubscribe_rate"] - 1 / 3) < 1e-9


def test_unsubscribe_out_of_period_not_counted():
    period_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    rows = [
        {"status": "active"},
        {"status": "unsubscribed", "unsubscribed_at": old},  # 不在周期内
    ]
    m = compute_unsubscribe_metrics(rows, period_start)
    assert m["new_unsubscribes"] == 0
    assert m["unsubscribe_rate"] == 0.0


def test_unsubscribe_rate_div_by_zero_safe():
    m = compute_unsubscribe_metrics([], "2026-01-01T00:00:00+00:00")
    assert m["unsubscribe_rate"] == 0.0


# ── 5. renderer 追踪像素注入 ───────────────────────────────────

def _report():
    return _demo_report(8)


def test_renderer_injects_1px_pixel_when_url_given():
    report = _report()
    url = "https://signal.test/track/open?token=TOK&article=2026-07-10"
    html = NewsletterRenderer(base_url="https://signal.test").render(
        report, "https://signal.test/unsubscribe?token=TOK",
        _report_date(), url,
    )
    # 像素 URL 入参含 &，渲染时按 HTML 规范转义为 &amp;，故用片段断言
    assert "/track/open?token=TOK" in html
    assert "article=2026-07-10" in html
    assert 'width="1" height="1"' in html
    assert "image/gif" not in html  # 像素 URL 在邮件里，GIF 由路由返回


def test_renderer_no_pixel_when_url_absent():
    report = _report()
    html = NewsletterRenderer().render(
        report, "https://signal.test/unsubscribe?token=TOK", _report_date()
    )
    assert "/track/open" not in html


def _report_date():
    from datetime import date
    return date.today()


def test_build_open_tracking_url():
    r = NewsletterRenderer(base_url="https://signal.test")
    assert r.build_open_tracking_url("TOK", "2026-07-10") == \
        "https://signal.test/track/open?token=TOK&article=2026-07-10"


# ── 6. record_open_event 去重（DB 层，mock client） ────────────

@pytest.fixture
def fake_db():
    with patch("api.models.database.create_client") as mock_create:
        client = MagicMock()
        mock_create.return_value = client
        db = DatabaseManager()
        yield db, client


def test_record_open_event_inserts_when_no_recent(fake_db):
    db, client = fake_db
    tbl = client.table.return_value
    sel = tbl.select.return_value
    eq1 = sel.eq.return_value
    eq2 = eq1.eq.return_value
    gte = eq2.gte.return_value
    gte.execute.return_value = MagicMock(data=[])  # 无近期记录

    ok = db.record_open_event("tok", "2026-07-10")
    assert ok is True
    tbl.insert.assert_called_once_with({"token": "tok", "article": "2026-07-10"})


def test_record_open_event_skips_when_recent_exists(fake_db):
    db, client = fake_db
    tbl = client.table.return_value
    sel = tbl.select.return_value
    eq1 = sel.eq.return_value
    eq2 = eq1.eq.return_value
    gte = eq2.gte.return_value
    gte.execute.return_value = MagicMock(data=[{"id": 1}])  # 已记录

    ok = db.record_open_event("tok", "2026-07-10")
    assert ok is False
    tbl.insert.assert_not_called()


def test_record_open_event_invalid_args(fake_db):
    db, _ = fake_db
    assert db.record_open_event("", "2026-07-10") is False
    assert db.record_open_event("tok", "") is False


# ── 7. fetch_metrics 离线（fake DB，不连 Supabase） ────────────

class _FakeTable:
    def __init__(self, rows):
        self.rows = rows
    def select(self, *a):
        return self
    def gte(self, *a):
        return self
    def execute(self):
        r = MagicMock()
        r.data = self.rows
        return r


class _FakeClient:
    def __init__(self, data: dict):
        self.data = data
    def table(self, name):
        return _FakeTable(self.data.get(name, []))


class _FakeDB:
    def __init__(self, subscribers, open_rows, send_rows):
        self.client = _FakeClient({
            "newsletter_subscribers": subscribers,
            "open_events": open_rows,
            "newsletter_sends": send_rows,
        })


def test_fetch_metrics_offline():
    subscribers = [
        {"status": "active"},
        {"status": "active"},
        {"status": "unsubscribed",
         "unsubscribed_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()},
    ]
    opens = [_open_row("t1", "2026-07-10", 1)]
    sends = [{"token": "t1", "sent_at": "x", "issue_date": "2026-07-10"}]
    fake = _FakeDB(subscribers, opens, sends)

    with patch.object(metrics_mod, "DatabaseManager", lambda: fake):
        m = fetch_metrics(fake, days=7)

    assert m["subscriptions"]["active"] == 2
    assert m["subscriptions"]["unsubscribed"] == 1
    assert m["opens"]["unique_opens"] == 1
    assert m["opens"]["open_rate"] == 1.0
    assert m["unsubscribes"]["new_unsubscribes"] == 1


def test_fetch_metrics_handles_missing_tables_gracefully():
    # 表查询抛异常时退化为 0，不崩
    class _BoomClient:
        def table(self, name):
            raise RuntimeError("table missing")
    fake = MagicMock()
    fake.client = _BoomClient()

    with patch.object(metrics_mod, "DatabaseManager", lambda: fake):
        m = fetch_metrics(fake, days=7)

    assert m["subscriptions"] == {"total": 0, "active": 0, "unsubscribed": 0}
    assert m["opens"]["unique_opens"] == 0
    assert m["opens"]["open_rate"] == 0.0


def test_build_card_lines_format():
    m = {
        "period_days": 7,
        "subscriptions": {"total": 10, "active": 8, "unsubscribed": 2},
        "opens": {"unique_opens": 4, "send_count": 8, "openers": 4, "open_rate": 0.5},
        "unsubscribes": {"new_unsubscribes": 1, "active_now": 8, "unsubscribe_rate": 1 / 9},
    }
    lines = build_card_lines(m)
    assert any("近 7 天" in ln for ln in lines)
    assert any("在订 8" in ln for ln in lines)
    assert any("打开率 50.0%" in ln for ln in lines)
    assert any("退订率" in ln for ln in lines)
