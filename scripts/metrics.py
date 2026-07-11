"""
Signal - 留存指标脚本（改造计划 §1.5）
=====================================================================
把「留不住」变成可测量的三张数：订阅数(subscriptions) / 打开率(opens) / 退订率(unsubscribes)。

设计原则：
  - 计算逻辑全为纯函数（输入 list[dict] → 输出 dict），不依赖真实 Supabase；
    因此可离线/单测，CI 中也可无网跑纯逻辑（见 tests/test_metrics.py）。
  - DB 拉取与纯计算解耦，且对缺表/缺列容错（缺则记 0，不崩）。
  - 不建 BI 看板：每周由 GitHub Actions 跑一次，经 FeishuNotifier 推一张极简卡。

指标口径：
  - 订阅：newsletter_subscribers 表 → active / total / unsubscribed。
  - 打开：open_events 表，去重规则「同 (token, article) 24h 内只算 1 次」；
          打开率 = 去重后唯一打开数 / 发送数(newsletter_sends)。
  - 退订：newsletter_subscribers 中 status=unsubscribed 且 unsubscribed_at 在周期内；
          退订率 = 本期新增退订 / (期末在订 + 本期新增退订)。

隐私合规：open_events 只写 token+article，绝不写 IP / User-Agent / 设备指纹。

用法：
  python scripts/metrics.py [--days 7] [--no-push] [--json]
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# 允许以 `python scripts/metrics.py` 直接运行（项目根加入 path）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from api.models.database import DatabaseManager
from scripts.feishu_notifier import FeishuNotifier

# 打开事件去重窗口（小时）：同一 (token, article) 在窗口内只算一次打开
OPEN_DEDUP_WINDOW_HOURS = 24


# ──────────────────────────────────────────────────────────────
# 1. 纯计算函数（可单测，不依赖数据库）
# ──────────────────────────────────────────────────────────────

def compute_subscription_metrics(rows: List[dict]) -> dict:
    """订阅三数：total / active / unsubscribed。"""
    total = len(rows)
    active = sum(1 for r in rows if (r.get("status") or "").lower() == "active")
    unsubscribed = sum(
        1 for r in rows if (r.get("status") or "").lower() == "unsubscribed"
    )
    return {"total": total, "active": active, "unsubscribed": unsubscribed}


def _parse_ts(v) -> Optional[datetime]:
    if not v:
        return None
    s = str(v)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def dedup_opens(open_rows: List[dict],
                window_hours: int = OPEN_DEDUP_WINDOW_HOURS) -> Dict[tuple, int]:
    """按 (token, article) 去重，返回每个 (token, article) 的去重后打开次数。

    规则：同一对在 window_hours 内只计 1 次打开；若隔了一个窗口再次打开则再计 1 次。
    例：同一订阅者 30 分钟内重复打开同一期 → 1 次；
        隔了 2 天再次打开同一期 → 2 次（两个窗口）。
    返回 dict：key=(token, article)，value=去重后打开次数（>=1）。
    """
    groups: Dict[tuple, List[datetime]] = defaultdict(list)
    for r in open_rows:
        t = _parse_ts(r.get("opened_at"))
        if t is None:
            continue
        groups[(r.get("token"), r.get("article"))].append(t)

    counts: Dict[tuple, int] = {}
    window = timedelta(hours=window_hours)
    for key, times in groups.items():
        times.sort()
        last = None
        cnt = 0
        for t in times:
            if last is None or (t - last) >= window:
                cnt += 1
                last = t
        counts[key] = cnt
    return counts


def compute_open_metrics(open_rows: List[dict], send_rows: List[dict],
                         window_hours: int = OPEN_DEDUP_WINDOW_HOURS) -> dict:
    """打开三数：去重唯一打开数 / 发送数 / 打开率 / 打开人数。"""
    open_counts = dedup_opens(open_rows, window_hours)
    unique_opens = sum(open_counts.values())
    send_count = len(send_rows)
    openers = len({r.get("token") for r in open_rows if r.get("token")})
    open_rate = (unique_opens / send_count) if send_count else 0.0
    return {
        "unique_opens": unique_opens,
        "send_count": send_count,
        "openers": openers,
        "open_rate": open_rate,
    }


def compute_unsubscribe_metrics(rows: List[dict], period_start: str) -> dict:
    """退订两数：本期新增退订数 / 退订率。

    退订率分母用「期末在订 + 本期新增退订」≈ 期初在订，避免负数/除零。
    """
    new_unsub = [
        r for r in rows
        if (r.get("status") or "").lower() == "unsubscribed"
        and r.get("unsubscribed_at")
        and str(r.get("unsubscribed_at")) >= period_start
    ]
    new_unsub_count = len(new_unsub)
    active_now = sum(1 for r in rows if (r.get("status") or "").lower() == "active")
    active_at_start = active_now + new_unsub_count
    unsub_rate = (new_unsub_count / active_at_start) if active_at_start else 0.0
    return {
        "new_unsubscribes": new_unsub_count,
        "active_now": active_now,
        "unsubscribe_rate": unsub_rate,
    }


# ──────────────────────────────────────────────────────────────
# 2. DB 拉取（容错，缺表不崩）
# ──────────────────────────────────────────────────────────────

def fetch_metrics(db: DatabaseManager, days: int = 7) -> dict:
    """从 DB 拉取原始行并汇总为三数；任意表缺失/报错时退化为 0，不抛异常。"""
    now = datetime.now(timezone.utc)
    period_start = (now - timedelta(days=days)).isoformat()

    subscribers: List[dict] = []
    open_rows: List[dict] = []
    send_rows: List[dict] = []

    try:
        res = db.client.table("newsletter_subscribers") \
            .select("email,status,subscribed_at,unsubscribed_at").execute()
        subscribers = res.data or []
    except Exception as e:
        print(f"  [METRICS] 拉取订阅者失败（记 0）: {e}")

    try:
        res = db.client.table("open_events") \
            .select("token,article,opened_at").gte("opened_at", period_start).execute()
        open_rows = res.data or []
    except Exception as e:
        print(f"  [METRICS] 拉取打开事件失败（记 0）: {e}")

    try:
        res = db.client.table("newsletter_sends") \
            .select("token,sent_at,issue_date").gte("sent_at", period_start).execute()
        send_rows = res.data or []
    except Exception as e:
        print(f"  [METRICS] 拉取发送事件失败（记 0）: {e}")

    sub = compute_subscription_metrics(subscribers)
    opens = compute_open_metrics(open_rows, send_rows)
    unsub = compute_unsubscribe_metrics(subscribers, period_start)

    return {
        "period_days": days,
        "generated_at": now.isoformat(),
        "subscriptions": sub,
        "opens": opens,
        "unsubscribes": unsub,
    }


# ──────────────────────────────────────────────────────────────
# 3. 飞书卡片
# ──────────────────────────────────────────────────────────────

def build_card_lines(m: dict) -> List[str]:
    sub = m["subscriptions"]
    opens = m["opens"]
    unsub = m["unsubscribes"]
    pct = lambda x: f"{x * 100:.1f}%"
    return [
        f"统计周期：近 {m['period_days']} 天",
        f"订阅：在订 {sub['active']} / 总计 {sub['total']} / 已退订 {sub['unsubscribed']}",
        f"打开：唯一打开 {opens['unique_opens']} / 发送 {opens['send_count']} / 打开率 {pct(opens['open_rate'])}",
        f"退订：本期新增 {unsub['new_unsubscribes']} / 退订率 {pct(unsub['unsubscribe_rate'])}",
    ]


# ──────────────────────────────────────────────────────────────
# 4. CLI
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Signal 留存指标（§1.5）")
    parser.add_argument("--days", type=int, default=7, help="统计周期（天）")
    parser.add_argument("--no-push", action="store_true", help="只打印，不推飞书")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出（便于调试）")
    args = parser.parse_args()

    db = DatabaseManager()
    metrics = fetch_metrics(db, args.days)

    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print("── Signal 留存指标 ──")
        for line in build_card_lines(metrics):
            print("  " + line)

    if not args.no_push:
        notifier = FeishuNotifier()
        notifier.send_metrics_card("Signal 留存指标周报", build_card_lines(metrics))


if __name__ == "__main__":
    main()
