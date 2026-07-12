"""
Signal - 邮件简报生成与发送（改造计划 §1.3：产品核心）
============================================================
读者「收」简报，不是「来」网站。本脚本是产品核心的推送端。

做了什么：
  1. 复用 processor.reporter.DailyReportGenerator 产出
     「按重要性分组文章 + 热点关键词 + 概览」——不重写 reporter。
  2. 今日主线（§2.1）由 processor.reporter.cluster_stories() 真实事件聚类产出，
     替换原「热度关键词占位」；同一事件的多篇报道被拧成一条主线。
  3. 渲染含 Step1(§1.2) so_what 观点层的邮件 HTML。
  4. 经 ESP 发送（Resend / SMTP / console 任选；默认 console 便于本地/测试验证）。
  5. 退订机制：每封邮件带 ?token= 退订链接 + newsletter_subscribers 表落库。

约束遵守：
  - 不动发送 / 退订 / 追踪像素逻辑（§1.3/§1.5 已交付）。
  - 不引入新依赖（Resend 走 httpx，SMTP 走标准库；httpx 已在 requirements）。

用法：
  python scripts/newsletter.py render [--date YYYY-MM-DD] [--top-n 8] [--demo] [--esp console]
  python scripts/newsletter.py send   [--to a@b.com] [--top-n 8] [--esp resend|smtp|console] [--dry-run]
  python scripts/newsletter.py seed   --email you@example.com
  python scripts/newsletter.py list
  python scripts/newsletter.py unsubscribe --token <token>

环境变量：
  NEWSLETTER_ESP        resend|smtp|console（默认 console）
  NEWSLETTER_RECIPIENTS 逗号分隔收件人（CI 用；每个会落库以便退订生效）
  NEWSLETTER_BASE_URL   退订链接域名（默认 https://signal.example.com，部署时填真实域名）
  NEWSLETTER_FROM       发件人（如 "Signal <news@yourdomain.com>"）
  RESEND_API_KEY        Resend 发送密钥
  SMTP_HOST/PORT/USER/PASSWORD/TLS   SMTP 后端配置（本地可用 Mailpit: localhost:1025）
"""

from __future__ import annotations

import os
import re
import sys
import html
import secrets
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple

# 允许以 `python scripts/newsletter.py` 直接运行（项目根加入 path）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
import httpx

from collector.base import Article
from processor.reporter import DailyReportGenerator, cluster_stories
from processor.github_agents import fetch_github_agents

load_dotenv()

# DatabaseManager 仅在涉及 DB 的命令（send/seed/list/unsubscribe）用到；
# 渲染/演示路径不需要 Supabase 连接，故延迟导入，避免渲染时也强依赖 DB 客户端。
def _get_db() -> "DatabaseManager":
    from api.models.database import DatabaseManager
    return DatabaseManager()


# ──────────────────────────────────────────────────────────────
# 1. 数据获取：复用 reporter 的现有数据结构
# ──────────────────────────────────────────────────────────────

def _rows_to_articles(rows: List[dict]) -> List[Article]:
    """将 DB 行转为 Article（保留 so_what，reporter 序列化时会丢弃，渲染前再补回）"""
    articles: List[Article] = []
    for r in rows:
        pa = r.get("published_at")
        published_at = None
        if pa:
            try:
                published_at = datetime.fromisoformat(str(pa).replace("Z", "+00:00"))
            except Exception:
                published_at = None
        articles.append(Article(
            title=r.get("title") or "",
            url=r.get("url") or "",
            source_name=r.get("source_name") or "",
            raw_content="",
            published_at=published_at,
            summary=r.get("summary") or "",
            tags=r.get("tags") or [],
            importance=r.get("importance") or "low",
            importance_reason=r.get("importance_reason") or "",
            so_what=r.get("so_what"),
        ))
    return articles


# ──────────────────────────────────────────────────────────────
# GitHub AI Agent 高星新星卡片（邮件 + 公开页同源复用）
# ──────────────────────────────────────────────────────────────

def _fmt_github_card(item: dict, escape) -> str:
    """单个 GitHub Agent 项目卡片（内联样式，邮件 / 公开页通用）。"""
    name = escape(item.get("name") or "")
    url = escape(item.get("url") or "#")
    desc = escape(item.get("description") or "")
    stars = item.get("stars", 0)
    lang = escape(item.get("language") or "")
    pushed = item.get("pushed_at") or ""
    rising = item.get("is_rising_star")
    rising_badge = (
        '<span style="font-size:11px;padding:1px 7px;border-radius:999px;'
        'background:#ecfdf5;color:#047857;margin-left:6px;">⚡ 新星</span>'
    ) if rising else ""
    lang_badge = (
        f'<span style="font-size:11px;color:#6b7280;margin-left:6px;">· {lang}</span>'
    ) if lang else ""
    pushed_date = pushed[:10] if pushed else ""
    return f"""<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px;margin-bottom:10px;">
      <div style="font-size:15px;font-weight:600;color:#111827;margin-bottom:4px;">
        <a href="{url}" style="color:#111827;text-decoration:none;">{name}</a>{rising_badge}
      </div>
      <p style="font-size:13px;line-height:1.6;color:#374151;margin:0 0 6px;">{desc}</p>
      <div style="font-size:12px;color:#6b7280;">★ {stars:,}{lang_badge} · 更新于 {pushed_date}</div>
    </div>"""


def _render_github_agents_section(items: list, escape) -> str:
    """「本周 AI Agent 新星」邮件区块（静态，无交互筛选器）。"""
    if not items:
        return ""
    cards = "\n".join(_fmt_github_card(it, escape) for it in items)
    return f"""<div style="padding:8px 28px 24px;">
      <div style="font-size:15px;font-weight:700;color:#0f172a;margin:12px 0;">🤖 本周 AI Agent 新星（GitHub 高星开源）</div>
      <div style="font-size:12px;color:#9ca3af;margin-bottom:10px;">按 Star 数降序 · ⚡ 为近期创建且日增迅速的新项目</div>
      {cards}
    </div>"""


def build_report(db: DatabaseManager, report_date: date, top_n: int = 8,
                 window_days: int = 3, gh_params: Optional[dict] = None) -> dict:
    """取当日文章，复用 reporter.generate 产出报告结构（不修改 reporter）。

    返回结构 = reporter 的 report dict，并额外挂：
      - main_stories: dict   今日主线（§2.1 事件聚类真实结果）
      - main_thread: List[str]  向后兼容的「主线标题」字符串列表（聚类无结果时回退占位）
      - 每个 article 项补回 so_what
    """
    from_date = (report_date - timedelta(days=window_days)).isoformat()
    res = db.get_articles(
        page=1, page_size=300, date_from=from_date,
        sort_by="published_at", sort_order="desc", use_cache=False,
    )
    rows = res.get("items", []) or []
    articles = _rows_to_articles(rows)

    # 仅保留 report_date 当天（与 reporter 分组口径一致）；无当日数据则回退到最新 top_n
    day_articles = [a for a in articles if a.published_at and a.published_at.date() == report_date]
    if not day_articles:
        day_articles = articles[:top_n]

    generator = DailyReportGenerator(db_manager=None, ai_processor=None)
    report = generator.generate(day_articles, report_date=report_date)
    if not report.get("summary_insight"):
        report["summary_insight"] = generator._generate_fallback_insight(day_articles)

    # 今日主线：事件聚类（§2.1）替换原占位实现
    clusters = cluster_stories(day_articles, report_date)
    report["main_stories"] = clusters
    # 向后兼容：main_thread 仍保留一份「主线标题」字符串列表；
    # 仅当聚类无结果时回退到占位实现（热度关键词 + Top 候选）。
    report["main_thread"] = (
        [s["title"] for s in clusters["stories"]]
        or _build_main_thread_placeholder(report, day_articles, top_n)
    )

    # 补回 so_what（reporter._serialize_articles 丢弃了该字段）
    by_url = {a.url: a for a in day_articles}
    for tier in ("high", "medium", "low"):
        for item in report["articles"][tier]:
            a = by_url.get(item.get("url"))
            item["so_what"] = a.so_what if a else None

    # 内嵌每日日报 · GitHub AI Agent 高星新星（用户 2026-07-12）
    # 默认最近一周 + 最低 100 star；公开页可经 gh_params 覆盖时间范围/最低 star/排序。
    default_gh = {"range": "week", "min_stars": 100, "sort": "stars", "limit": 12}
    gh = {**default_gh, **(gh_params or {})}
    try:
        report["github_agents"] = fetch_github_agents(**gh)
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] github_agents 注入失败（降级为空）: {e}")
        report["github_agents"] = []
    report["gh_filter"] = gh
    return report


def _build_main_thread_placeholder(report: dict, articles: List[Article], top_n: int) -> List[str]:
    """今日主线占位：事件聚类未上线前的临时方案。"""
    bullets: List[str] = []
    keywords = report.get("trending_keywords") or []
    if keywords:
        bullets.append("热度关键词：" + "、".join(keywords[:6]))
    high = report["articles"]["high"]
    for a in high[:3]:
        t = (a.get("title") or "").strip()
        if t:
            bullets.append("重点：" + t)
    if not bullets:
        bullets.append("今日暂无高优先级信号，以下为精选文章。")
    return bullets


# ──────────────────────────────────────────────────────────────
# 2. 订阅者存储（退订落库）
# ──────────────────────────────────────────────────────────────

class SubscriberStore:
    """newsletter_subscribers 表的读写；退订状态落库。"""

    TABLE = "newsletter_subscribers"

    def __init__(self, db: DatabaseManager):
        self.db = db

    def _table(self):
        return self.db.client.table(self.TABLE)

    def upsert(self, email: str, source: str = "seed") -> Optional[str]:
        """新增或恢复订阅，返回 token（用于退订链接）。"""
        email = (email or "").strip().lower()
        if not email or "@" not in email:
            return None
        existing = self._table().select("token,status").eq("email", email).execute()
        if existing.data:
            row = existing.data[0]
            if row.get("status") != "active":
                self._table().update({"status": "active", "unsubscribed_at": None}) \
                    .eq("email", email).execute()
            return row["token"]
        token = secrets.token_urlsafe(32)
        self._table().insert({
            "email": email, "token": token, "source": source, "status": "active",
        }).execute()
        return token

    def get_active(self) -> List[dict]:
        res = self._table().select("email,token").eq("status", "active").execute()
        return res.data or []

    def unsubscribe(self, token: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        res = self._table().update(
            {"status": "unsubscribed", "unsubscribed_at": now_iso}
        ).eq("token", token).execute()
        return bool(res.data)

    def list_all(self) -> List[dict]:
        res = self._table().select("email,status,subscribed_at") \
            .order("subscribed_at", desc=True).execute()
        return res.data or []

    def record_send_event(self, token: str, issue_date: str) -> bool:
        """记录一次发送（打开率分母），委托 DatabaseManager，同 issue 幂等。"""
        return self.db.record_send_event(token, issue_date)


# ──────────────────────────────────────────────────────────────
# 3. 邮件 HTML 渲染
# ──────────────────────────────────────────────────────────────

class NewsletterRenderer:
    """把 report dict 渲染成邮件 HTML（含 so_what + 退订链接）。"""

    def __init__(self, base_url: Optional[str] = None, product_name: str = "Signal",
                 top_n: int = 8):
        self.base_url = (base_url or os.getenv("NEWSLETTER_BASE_URL",
                                                "https://signal.example.com")).rstrip("/")
        self.product_name = product_name
        self.top_n = top_n

    def build_unsubscribe_url(self, token: str) -> str:
        return f"{self.base_url}/unsubscribe?token={token}"

    def build_open_tracking_url(self, token: str, article: str) -> str:
        """打开追踪像素地址（§1.5）。article 本期=简报日期 YYYY-MM-DD。"""
        return f"{self.base_url}/track/open?token={token}&article={article}"

    @staticmethod
    def _fmt_time(iso: Optional[str]) -> str:
        if not iso:
            return ""
        try:
            dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
            dt = dt.astimezone(timezone(timedelta(hours=8)))  # 以北京时间展示
        except Exception:
            return ""
        return dt.strftime("%m-%d %H:%M")

    def render(self, report: dict, unsubscribe_url: str,
               report_date: Optional[date] = None,
               open_tracking_url: Optional[str] = None) -> str:
        report_date = report_date or date.today()
        escape = html.escape

        insight = report.get("summary_insight") or "今日暂无概览。"

        # 今日主线：优先渲染 §2.1 事件聚类结果（主线标题 + 挂的文章标题列表）
        main_stories = report.get("main_stories") or {}
        stories = main_stories.get("stories") if isinstance(main_stories, dict) else []
        if stories:
            blocks = []
            for s in stories:
                entity = s.get("entity")
                badge = (
                    f'<span style="font-size:11px;padding:1px 8px;border-radius:999px;'
                    f'background:#eef2ff;color:#4338ca;margin-right:6px;">{escape(entity)}</span>'
                ) if entity else ""
                hung = s.get("articles") or []
                li_html = "\n".join(
                    f'<li style="font-size:13px;line-height:1.6;color:#374151;margin-bottom:3px;">'
                    f'<a href="{escape(a.get("url") or "#")}" style="color:#2563eb;text-decoration:none;">'
                    f'{escape(a.get("title") or "（无标题）")}</a>'
                    f'<span style="color:#9ca3af;"> · {escape(a.get("source_name") or "")}</span></li>'
                    for a in hung[:6]
                )
                blocks.append(
                    '<div style="margin-bottom:14px;">'
                    f'<div style="font-size:14px;font-weight:600;color:#0f172a;margin-bottom:2px;">{badge}{escape(s.get("title") or "")}</div>'
                    f'<ul style="margin:2px 0 0;padding-left:18px;">{li_html}</ul>'
                    '</div>'
                )
            main_thread_html = "\n".join(blocks)
            main_thread_note = "事件聚类自动生成 · 同一事件的多篇报道已合并"
        else:
            # 聚类无结果：回退展示 main_thread 占位字符串列表
            fallback = report.get("main_thread") or []
            main_thread_html = "\n".join(
                f'<li style="font-size:13px;line-height:1.6;color:#374151;margin-bottom:4px;">'
                f'{escape(b)}</li>' for b in fallback
            )
            main_thread_note = "（暂无可聚类信号，显示热度 Top 候选）"

        # Top N：跨重要性层级（高→中→低）取前 N
        ranked = (report["articles"]["high"]
                  + report["articles"]["medium"]
                  + report["articles"]["low"])[:self.top_n]
        if not ranked:
            articles_html = ('<p style="font-size:13px;color:#9ca3af;margin:0;">'
                             '今日暂无收录内容。</p>')
        else:
            articles_html = "\n".join(
                self._render_article(a, escape) for a in ranked
            )
        github_html = _render_github_agents_section(report.get("github_agents") or [], escape)

        subject = f"{self.product_name} 每日 AI 简报 · {report_date.isoformat()}"
        date_str = report_date.isoformat()

        # 打开追踪像素（§1.5）：1px 透明、对邮件客户端无害；
        # 仅在提供了 open_tracking_url 时注入，且只记录 token 维度聚合（不定位个人）。
        open_pixel = ""
        if open_tracking_url:
            open_pixel = (
                '\n    <img src="{url}" width="1" height="1" alt="" '
                'style="display:block;width:1px;height:1px;border:0;margin:0;padding:0;" />'
            ).format(url=escape(open_tracking_url))

        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;">
  <div style="max-width:640px;margin:0 auto;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'PingFang SC','Microsoft YaHei',sans-serif;color:#1f2937;">
    <div style="background:#0f172a;color:#fff;padding:24px 28px;">
      <div style="font-size:20px;font-weight:700;">{escape(self.product_name)} · 每日 AI 情报简报</div>
      <div style="font-size:13px;color:#94a3b8;margin-top:4px;">{escape(date_str)} · 自动推送，零主动访问</div>
    </div>
    <div style="padding:20px 28px;">
      <p style="font-size:14px;line-height:1.7;color:#374151;margin:0;">{escape(insight)}</p>
    </div>
    <div style="padding:0 28px 8px;">
      <div style="font-size:15px;font-weight:700;color:#0f172a;margin-bottom:4px;">🧭 今日主线</div>
      <div style="font-size:12px;color:#9ca3af;margin-bottom:10px;">{main_thread_note}</div>
      <ul style="margin:0;padding-left:18px;">{main_thread_html}</ul>
    </div>
    <div style="padding:8px 28px 24px;">
      <div style="font-size:15px;font-weight:700;color:#0f172a;margin:12px 0;">📌 今日精选（Top {len(ranked)}）</div>
      {articles_html}
    </div>
    {github_html}
    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:18px 28px;font-size:12px;color:#9ca3af;">
      <p style="margin:0 0 6px;">你收到此邮件，是因为订阅了 {escape(self.product_name)} 每日 AI 情报简报。编辑部每天为你挑选值得关注的 AI 信号。</p>
      <p style="margin:0;"><a href="{escape(unsubscribe_url)}" style="color:#6b7280;">退订 Signal 每日情报</a></p>
    </div>
  </div>{open_pixel}
</body>
</html>"""

    @staticmethod
    def _render_article(a: dict, escape) -> str:
        imp = (a.get("importance") or "low").lower()
        badge = {"high": ("#dc2626", "高"), "medium": ("#d97706", "中")}.get(
            imp, ("#6b7280", "低"))
        badge_color, badge_text = badge

        title = escape(a.get("title") or "（无标题）")
        url = escape(a.get("url") or "#")
        source = escape(a.get("source_name") or "未知来源")
        time_str = NewsletterRenderer._fmt_time(a.get("published_at"))
        summary = escape(a.get("summary") or "")

        so_what = a.get("so_what")
        if so_what:
            so_what_block = (
                '<div style="margin-top:10px;padding:10px 12px;background:#fffbeb;'
                'border-left:3px solid #f59e0b;border-radius:4px;">'
                '<div style="font-size:12px;font-weight:600;color:#b45309;margin-bottom:2px;">'
                '💡 So What / 对你意味着什么</div>'
                f'<div style="font-size:13px;line-height:1.6;color:#92400e;">{escape(so_what)}</div>'
                '</div>'
            )
        else:
            so_what_block = (
                '<div style="margin-top:8px;font-size:12px;color:#9ca3af;">'
                '（暂无观点层）</div>'
            )

        return f"""<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span style="font-size:11px;padding:2px 8px;border-radius:999px;color:#fff;background:{badge_color};">{badge_text}</span>
        <span style="font-size:12px;color:#6b7280;">{source} · {time_str}</span>
      </div>
      <a href="{url}" style="font-size:15px;font-weight:600;color:#111827;text-decoration:none;">{title}</a>
      <p style="font-size:13px;line-height:1.6;color:#374151;margin:8px 0 0;">{summary}</p>
      {so_what_block}
    </div>"""


# ──────────────────────────────────────────────────────────────
# 4. ESP 发送层（Resend / SMTP / console）
# ──────────────────────────────────────────────────────────────

class EmailSender:
    def send(self, to: str, subject: str, html: str, unsubscribe_url: str) -> bool:
        raise NotImplementedError


class ConsoleESP(EmailSender):
    """开发/测试后端：把邮件 HTML 写到 output/，不实际发送（满足本地验收）。"""

    def __init__(self, out_dir: str = "output"):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

    def send(self, to: str, subject: str, html: str, unsubscribe_url: str) -> bool:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", to)
        path = os.path.join(self.out_dir, f"newsletter_{date.today().isoformat()}_{safe}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [CONSOLE] 邮件已写入: {path}")
        print(f"  [CONSOLE] 收件人: {to} | 主题: {subject}")
        print(f"  [CONSOLE] 退订链接: {unsubscribe_url}")
        return True


class ResendESP(EmailSender):
    """生产后端：Resend REST API（httpx，无需额外依赖）。"""

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_addr = os.getenv("NEWSLETTER_FROM", "Signal <news@signal.example.com>")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def send(self, to: str, subject: str, html: str, unsubscribe_url: str) -> bool:
        if not self.is_configured():
            print("  [RESEND] 未配置 RESEND_API_KEY，跳过发送")
            return False
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.from_addr,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        # List-Unsubscribe 提升送达率（RFC 2369）
                        "headers": {"List-Unsubscribe": f"<{unsubscribe_url}>"},
                    },
                )
                resp.raise_for_status()
                print(f"  [RESEND] 已发送至 {to}: {resp.json().get('id')}")
                return True
        except Exception as e:
            print(f"  [RESEND] 发送失败 {to}: {e}")
            return False


class SmtpESP(EmailSender):
    """本地/自托管后端：SMTP（可用 Mailpit 等本地 SMTP 验证）。"""

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "localhost")
        self.port = int(os.getenv("SMTP_PORT", "1025"))
        self.user = os.getenv("SMTP_USER") or ""
        self.password = os.getenv("SMTP_PASSWORD") or ""
        self.from_addr = os.getenv("NEWSLETTER_FROM", "Signal <news@signal.example.com>")
        self.use_tls = os.getenv("SMTP_TLS", "false").lower() == "true"

    def send(self, to: str, subject: str, html: str, unsubscribe_url: str) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg.attach(MIMEText(html, "html", "utf-8"))
        try:
            with smtplib.SMTP(self.host, self.port) as s:
                if self.use_tls:
                    s.starttls()
                if self.user:
                    s.login(self.user, self.password)
                s.sendmail(self.from_addr, [to], msg.as_string())
            print(f"  [SMTP] 已发送至 {to}")
            return True
        except Exception as e:
            print(f"  [SMTP] 发送失败 {to}: {e}")
            return False


def get_sender(esp: Optional[str] = None) -> EmailSender:
    esp = (esp or os.getenv("NEWSLETTER_ESP", "console")).lower()
    if esp == "resend":
        return ResendESP()
    if esp == "smtp":
        return SmtpESP()
    return ConsoleESP()


# ──────────────────────────────────────────────────────────────
# 5. 编排服务
# ──────────────────────────────────────────────────────────────

class NewsletterService:
    def __init__(self, db: DatabaseManager, esp: Optional[str] = None,
                 base_url: Optional[str] = None, top_n: int = 8):
        self.db = db
        self.store = SubscriberStore(db)
        self.sender = get_sender(esp)
        self.renderer = NewsletterRenderer(base_url=base_url, top_n=top_n)
        self.top_n = top_n

    def _recipients(self, to_email: Optional[str] = None) -> List[Tuple[str, str]]:
        recipients: List[Tuple[str, str]] = []
        # CI 环境变量列表（每个落库，保证退订链接有效）
        env_list = os.getenv("NEWSLETTER_RECIPIENTS", "")
        for e in [x.strip() for x in env_list.split(",") if x.strip()]:
            token = self.store.upsert(e, source="env")
            if token:
                recipients.append((e, token))
        # DB 在订用户
        for row in self.store.get_active():
            recipients.append((row["email"], row["token"]))
        # 一次性 --to（也落库）
        if to_email:
            token = self.store.upsert(to_email, source="cli")
            if token:
                recipients.append((to_email, token))
        # 去重
        seen = set()
        uniq = []
        for email, token in recipients:
            if email in seen:
                continue
            seen.add(email)
            uniq.append((email, token))
        return uniq

    def send(self, report_date: Optional[date] = None,
             to_email: Optional[str] = None, dry_run: bool = False) -> int:
        report_date = report_date or date.today()
        report = build_report(self.db, report_date, self.top_n)
        recipients = self._recipients(to_email)
        if not recipients:
            print("  [NEWSLETTER] 无收件人（未配置 NEWSLETTER_RECIPIENTS 且无在订用户）。跳过发送。")
            return 0
        subject = f"Signal 每日 AI 简报 · {report_date.isoformat()}"
        issue_id = report_date.isoformat()
        sent = 0
        for email, token in recipients:
            unsubscribe_url = self.renderer.build_unsubscribe_url(token)
            open_url = self.renderer.build_open_tracking_url(token, issue_id)
            html = self.renderer.render(report, unsubscribe_url, report_date, open_url)
            if dry_run:
                print(f"  [DRY-RUN] 将发送给 {email}（不实际发送）| 退订: {unsubscribe_url}")
                sent += 1
                continue
            if self.sender.send(email, subject, html, unsubscribe_url):
                sent += 1
                # 记录发送事件（打开率分母）；同 issue 幂等
                try:
                    self.store.record_send_event(token, issue_id)
                except Exception:
                    pass
        print(f"  [NEWSLETTER] 处理完成：{sent}/{len(recipients)} 封")
        return sent


# ──────────────────────────────────────────────────────────────
# 6. Demo 报告（无 DB 也能验证渲染）
# ──────────────────────────────────────────────────────────────

def _demo_report(top_n: int) -> dict:
    now = datetime.now()
    sample = [
        {
            "title": "<script>alert(1)</script>OpenAI 发布 GPT-6，推理成本下降 70%",
            "url": "https://example.com/1", "source_name": "机器之心",
            "summary": "OpenAI 今日发布 GPT-6，官方称推理成本较上代下降 70%，长上下文翻倍。",
            "tags": ["大模型", "OpenAI"], "importance": "high", "importance_reason": "行业重磅",
            "so_what": "对中小团队意味着 API 成本大幅下降，可以更低门槛把多模态能力塞进产品。",
            "published_at": now.isoformat(),
        },
        {
            "title": "Hugging Face 上线本地推理网关",
            "url": "https://example.com/2", "source_name": "Hugging Face",
            "summary": "HF 推出本地推理网关，支持私有化部署主流开源模型。",
            "tags": ["开源", "部署"], "importance": "medium", "importance_reason": "工程利好",
            "so_what": "数据合规要求高的团队，终于能绕开公有云把模型跑在自己机房。",
            "published_at": now.isoformat(),
        },
        {
            "title": "某独角兽被曝裁员 30%",
            "url": "https://example.com/3", "source_name": "36氪",
            "summary": "一家 AI 应用独角兽被曝裁员 30%，聚焦核心产品线。",
            "tags": ["行业"], "importance": "low", "importance_reason": "信号待验证",
            "so_what": None,
            "published_at": now.isoformat(),
        },
    ]
    articles = _rows_to_articles(sample)
    gen = DailyReportGenerator(db_manager=None, ai_processor=None)
    report = gen.generate(articles, report_date=date.today())
    report["summary_insight"] = gen._generate_fallback_insight(articles)
    # 今日主线：与 build_report 同口径，用聚类结果替换占位
    clusters = cluster_stories(articles, date.today())
    report["main_stories"] = clusters
    report["main_thread"] = (
        [s["title"] for s in clusters["stories"]]
        or _build_main_thread_placeholder(report, articles, top_n)
    )
    by_url = {a.url: a for a in articles}
    for tier in ("high", "medium", "low"):
        for item in report["articles"][tier]:
            item["so_what"] = by_url[item["url"]].so_what
    return report


# ──────────────────────────────────────────────────────────────
# 7. CLI
# ──────────────────────────────────────────────────────────────

def _date_type(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main():
    parser = argparse.ArgumentParser(description="Signal 邮件简报（§1.3 产品核心）")
    sub = parser.add_subparsers(dest="cmd")

    p_render = sub.add_parser("render", help="仅渲染邮件 HTML 到 output/（不发送）")
    p_render.add_argument("--date", type=_date_type, default=date.today())
    p_render.add_argument("--top-n", type=int, default=8)
    p_render.add_argument("--demo", action="store_true", help="用合成数据，无需数据库")
    p_render.add_argument("--esp", default=None)

    p_send = sub.add_parser("send", help="生成并发送邮件简报")
    p_send.add_argument("--date", type=_date_type, default=date.today())
    p_send.add_argument("--top-n", type=int, default=8)
    p_send.add_argument("--to", default=None, help="一次性收件人（会落库以便退订生效）")
    p_send.add_argument("--esp", default=None)
    p_send.add_argument("--dry-run", action="store_true", help="渲染但不实际发送")

    p_seed = sub.add_parser("seed", help="添加/恢复一个订阅者（dogfood 自己先订阅）")
    p_seed.add_argument("--email", required=True)
    p_seed.add_argument("--source", default="seed")

    p_list = sub.add_parser("list", help="列出所有订阅者")

    p_un = sub.add_parser("unsubscribe", help="凭 token 退订")
    p_un.add_argument("--token", required=True)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    db: Optional[DatabaseManager] = None

    if args.cmd == "render":
        if args.demo:
            report = _demo_report(args.top_n)
            print("  [RENDER] 使用 demo 数据（无数据库）")
        else:
            db = _get_db()
            report = build_report(db, args.date, args.top_n)
        token = "DEMO_TOKEN" if args.demo else secrets.token_urlsafe(16)
        renderer = NewsletterRenderer(top_n=args.top_n)
        url = renderer.build_unsubscribe_url(token)
        html = renderer.render(report, url, args.date)
        out = os.path.join("output", f"newsletter_{args.date.isoformat()}.html")
        os.makedirs("output", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [RENDER] 已写入 {out}")
        print(f"  [RENDER] 退订链接(示例): {url}")
        return

    # 以下命令需要数据库
    db = _get_db()

    if args.cmd == "send":
        svc = NewsletterService(db, esp=args.esp, top_n=args.top_n)
        svc.send(report_date=args.date, to_email=args.to, dry_run=args.dry_run)
    elif args.cmd == "seed":
        store = SubscriberStore(db)
        token = store.upsert(args.email, source=args.source)
        print(f"  [SEED] {args.email} 已添加/恢复，token={token}")
    elif args.cmd == "list":
        store = SubscriberStore(db)
        rows = store.list_all()
        if not rows:
            print("  [LIST] 暂无订阅者")
        for r in rows:
            print(f"  {r['email']}  {r['status']}  {r.get('subscribed_at')}")
    elif args.cmd == "unsubscribe":
        store = SubscriberStore(db)
        ok = store.unsubscribe(args.token)
        print(f"  [UNSUB] {'成功' if ok else '失败/无效'}")


if __name__ == "__main__":
    main()
