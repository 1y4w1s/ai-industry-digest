"""
Signal - 公开页 SEO / 每日简报公开归档页（改造计划 §2.3）

把「每日简报」从"只在邮箱里"升级为"可被搜索引擎发现的公开网页"。

提供三个公开只读端点（无前缀，挂在站点根，便于 SEO）：
  GET /digest/{date}       → 指定日期的公开 HTML（今日主线 + Top N 文章含 so_what）
  GET /sitemap.xml         → 最近 N 天公开简报日期的绝对链接列表
  GET /robots.txt          → 允许索引并指向 sitemap

设计约束遵守：
  - 复用 scripts.newsletter.NewsletterRenderer 的区块结构（文章卡直接调用其静态方法
    _render_article，做到与邮件简报"同源"排版），但输出**独立 HTML**：
    去掉退订链接 / 打开追踪像素 / 邮件外壳。
  - 不重写 DailyReportGenerator / cluster_stories / NewsletterRenderer 主体；
    公开页只做"只读 HTML 渲染层"。数据复用 newsletter.build_report（同口径取数 + 聚类）。
  - 优雅降级：DB 不可达 / 当天无文章 → 友好空页（含"暂无内容"提示 + 合法 meta），不 500。
  - 不泄露非公开数据：仅渲染已落库、标记为可公开的日报内容。
  - 不引入新重依赖；HTML 用模板字符串，无服务端渲染框架。

SEO 口径：
  - PUBLIC_BASE_URL 缺省 `https://1y4w1s.icu:8080`（注意带 8080 端口，因线上为该端口且 HTTPS 待收敛）；
    允许环境变量 PUBLIC_BASE_URL 覆盖。
  - canonical / og:url / sitemap <loc> / 站内链接 均用该 base 拼**绝对 URL**，
    避免相对路径导致搜索引擎爬到错误规范链接。
"""

import os
import html
import json
from datetime import datetime, timedelta

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from api.models.database import get_db

# 复用邮件简报的取数 + 聚类口径（同一份 cluster_stories 数据，与邮件同源）
from scripts.newsletter import build_report, NewsletterRenderer

# 公开页常量
DEFAULT_PUBLIC_BASE_URL = "https://1y4w1s.icu:8080"   # 线上域名（8080 端口 + HTTPS 待收敛）
SITEMAP_DAYS = 30                                       # sitemap 收录最近 N 天
TOP_N = 8                                               # 公开页 Top N 文章
PRODUCT_NAME = "Signal"

router = APIRouter()


def _public_base_url() -> str:
    """公开页绝对地址基址：环境变量优先，缺省带 8080 端口的线上域名。"""
    return os.getenv("PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL).rstrip("/")


# ──────────────────────────────────────────────────────────────
# 公开页渲染层（只读 HTML，与邮件简报同源排版）
# ──────────────────────────────────────────────────────────────

class PublicDigestRenderer:
    """把 report dict 渲染成**公开**独立 HTML（含 SEO meta）。

    与 NewsletterRenderer 的关系：
      - 文章卡：直接复用 NewsletterRenderer._render_article（静态方法），排版 100% 同源。
      - 今日主线区块：沿用与邮件一致的 inline-style 结构（同 CSS、同徽标/挂文列表）。
      - 差异：本类输出完整 <html><head> 含 SEO 标签；**不含**退订链接 / 追踪像素 / 邮件外壳。
    """

    def __init__(self, base_url: str = None, product_name: str = PRODUCT_NAME, top_n: int = TOP_N):
        self.base_url = (base_url or _public_base_url()).rstrip("/")
        self.product_name = product_name
        self.top_n = top_n

    # 复用邮件的 time 格式化（静态方法）
    @staticmethod
    def _fmt_time(iso):
        return NewsletterRenderer._fmt_time(iso)

    # ── 今日主线区块（与邮件同结构）────────────────────────
    def _render_main_thread(self, report: dict, escape) -> tuple:
        """返回 (main_thread_html, main_thread_note)。结构同 NewsletterRenderer.render()。"""
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
            return "\n".join(blocks), "事件聚类自动生成 · 同一事件的多篇报道已合并"
        # 聚类无结果：回退展示 main_thread 占位字符串列表
        fallback = report.get("main_thread") or []
        main_thread_html = "\n".join(
            f'<li style="font-size:13px;line-height:1.6;color:#374151;margin-bottom:4px;">'
            f'{escape(b)}</li>' for b in fallback
        )
        return main_thread_html, "（暂无可聚类信号，显示热度 Top 候选）"

    # ── Top N 文章区块（复用邮件卡片）──────────────────────
    def _ranked_articles(self, report: dict) -> list:
        arts = (report.get("articles") or {})
        return (arts.get("high", []) + arts.get("medium", []) + arts.get("low", []))[:self.top_n]

    def _render_articles(self, report: dict, escape) -> str:
        ranked = self._ranked_articles(report)
        if not ranked:
            return ('<p style="font-size:13px;color:#9ca3af;margin:0;">'
                    '今日暂无收录内容。</p>')
        # 直接复用邮件简报的文章卡渲染（同源排版）
        return "\n".join(NewsletterRenderer._render_article(a, escape) for a in ranked)

    # ── SEO 头 ───────────────────────────────────────────
    def _build_head(self, report: dict, report_date, ranked: list, escape) -> str:
        date_str = report_date.isoformat()
        canonical = f"{self.base_url}/digest/{date_str}"
        title = f"{self.product_name} 每日 AI 情报 · {date_str}｜今日 AI 新闻主线与观点"
        # description：概览 + 前几条主线标题，截断到 ~160 字
        desc_parts = []
        insight = (report.get("summary_insight") or "").strip()
        if insight:
            desc_parts.append(insight)
        stories = (report.get("main_stories") or {}).get("stories") or []
        for s in stories[:3]:
            t = (s.get("title") or "").strip()
            if t:
                desc_parts.append(t)
        description = " · ".join(desc_parts) if desc_parts else (
            f"{self.product_name} 每日 AI 情报简报 {date_str}，今日暂无内容。"
        )
        description = escape(description[:160])

        # JSON-LD：CollectionPage → ItemList → Article（利于"今日 AI 新闻"类检索命中）
        item_list = []
        for i, a in enumerate(ranked, start=1):
            item_list.append({
                "@type": "ListItem",
                "position": i,
                "item": {
                    "@type": "Article",
                    "headline": a.get("title") or "（无标题）",
                    "url": a.get("url") or canonical,
                    "author": {"@type": "Organization",
                               "name": a.get("source_name") or self.product_name},
                    "datePublished": a.get("published_at") or f"{date_str}T00:00:00+08:00",
                },
            })
        json_ld = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": canonical,
            "datePublished": f"{date_str}T00:00:00+08:00",
            "description": description,
            "publisher": {"@type": "Organization", "name": self.product_name},
            "mainEntity": {"@type": "ItemList", "itemListElement": item_list},
        }
        ld = json.dumps(json_ld, ensure_ascii=False)
        # 防止 JSON 中的 < > & 破坏 HTML / 触发 XSS
        ld = ld.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

        return f"""<title>{escape(title)}</title>
<meta name="description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{escape(self.product_name)}">
<meta property="article:published_time" content="{date_str}T00:00:00+08:00">
<link rel="canonical" href="{canonical}">
<script type="application/ld+json">{ld}</script>"""

    # ── 主渲染 ───────────────────────────────────────────
    def render(self, report: dict, report_date, degraded: bool = False) -> str:
        """渲染完整公开页 HTML。report 为空/缺字段时优雅降级为友好空页（合法 meta）。"""
        escape = html.escape
        date_str = report_date.isoformat()
        ranked = self._ranked_articles(report)
        insight = (report.get("summary_insight") or "今日暂无概览。").strip()

        main_thread_html, main_thread_note = self._render_main_thread(report, escape)
        articles_html = self._render_articles(report, escape)
        head = self._build_head(report, report_date, ranked, escape)

        # 降级横幅（DB 不可达等）：合法 meta 之外的友好提示，不泄露错误细节
        banner = ""
        if degraded:
            banner = ('<div style="margin:0 28px 12px;padding:12px 14px;border-radius:8px;'
                      'background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;font-size:13px;">'
                      '内容暂时无法加载，请稍后重试。你仍可浏览其他日期的公开简报。</div>')

        home_url = f"{self.base_url}/"
        archive_url = f"{self.base_url}/archive"

        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{head}
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'PingFang SC','Microsoft YaHei',sans-serif;color:#1f2937;">
  <div style="max-width:720px;margin:0 auto;background:#ffffff;">
    <div style="background:#0f172a;color:#fff;padding:24px 28px;">
      <div style="font-size:20px;font-weight:700;">{escape(self.product_name)} · 每日 AI 情报简报</div>
      <div style="font-size:13px;color:#94a3b8;margin-top:4px;">{escape(date_str)} · 公开归档页（无需订阅即可阅读）</div>
    </div>
    {banner}
    <div style="padding:20px 28px;">
      <p style="font-size:14px;line-height:1.7;color:#374151;margin:0;">{escape(insight)}</p>
    </div>
    <div style="padding:0 28px 8px;">
      <div style="font-size:15px;font-weight:700;color:#0f172a;margin-bottom:4px;">🧭 今日主线</div>
      <div style="font-size:12px;color:#9ca3af;margin-bottom:10px;">{escape(main_thread_note)}</div>
      <ul style="margin:0;padding-left:18px;">{main_thread_html}</ul>
    </div>
    <div style="padding:8px 28px 24px;">
      <div style="font-size:15px;font-weight:700;color:#0f172a;margin:12px 0;">📌 今日精选（Top {len(ranked)}）</div>
      {articles_html}
    </div>
    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:18px 28px;font-size:12px;color:#9ca3af;">
      <p style="margin:0 0 6px;">{escape(self.product_name)} 每日 AI 情报简报 · 公开归档页。编辑部每日精选值得关注的 AI 信号，可自由阅读、分享。</p>
      <p style="margin:0;"><a href="{escape(archive_url)}" style="color:#6b7280;">往期归档</a> · <a href="{escape(home_url)}" style="color:#6b7280;">返回首页</a></p>
    </div>
  </div>
</body>
</html>"""

    def render_unavailable(self, raw_date: str) -> str:
        """日期格式非法时返回的友好页（合法 meta，404 语义由路由层设置）。"""
        escape = html.escape
        canonical = f"{self.base_url}/digest/{escape(raw_date)}"
        title = f"{self.product_name} 每日 AI 情报 · {escape(raw_date)}"
        description = f"{self.product_name} 每日 AI 情报简报 {escape(raw_date)} 的公开归档页。"
        head = f"""<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{escape(self.product_name)}">
<link rel="canonical" href="{canonical}">"""
        home_url = f"{self.base_url}/"
        archive_url = f"{self.base_url}/archive"
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{head}
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1f2937;">
  <div style="max-width:720px;margin:0 auto;background:#ffffff;">
    <div style="background:#0f172a;color:#fff;padding:24px 28px;">
      <div style="font-size:20px;font-weight:700;">{escape(self.product_name)} · 每日 AI 情报简报</div>
    </div>
    <div style="padding:40px 28px;text-align:center;">
      <h1 style="font-size:18px;color:#0f172a;margin:0 0 8px;">日期格式无效</h1>
      <p style="font-size:14px;color:#6b7280;margin:0;">公开简报日期应为 YYYY-MM-DD（如 2026-07-10）。</p>
      <p style="font-size:12px;color:#9ca3af;margin-top:20px;"><a href="{escape(archive_url)}" style="color:#6b7280;">前往往期归档</a> · <a href="{escape(home_url)}" style="color:#6b7280;">返回首页</a></p>
    </div>
  </div>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────────────────────

def _empty_report() -> dict:
    """降级用的空 report 结构（字段齐全，避免渲染层 KeyError）。"""
    return {
        "summary_insight": "",
        "main_stories": {"stories": [], "total_stories": 0},
        "main_thread": [],
        "articles": {"high": [], "medium": [], "low": []},
    }


def _parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


@router.get("/digest/{report_date}", response_class=HTMLResponse, tags=["公开页 SEO"])
async def public_digest(report_date: str):
    """公开只读简报页（改造计划 §2.3）。

    - 复用 newsletter.build_report（同 cluster_stories 数据，与邮件简报同源）。
    - DB 不可达 → 降级为空页面（合法 meta + 友好提示），不 500。
    - 当天无文章 → 渲染"暂无收录内容"的合法页面（仍含 SEO meta）。
    - 日期格式非法 → 404 友好页。
    """
    try:
        rd = _parse_date(report_date)
    except Exception:
        return HTMLResponse(
            PublicDigestRenderer().render_unavailable(report_date),
            status_code=404,
        )

    try:
        db = get_db()
        report = build_report(db, rd, TOP_N)
        degraded = False
    except Exception:
        # DB 不可达：优雅降级，返回友好空页（合法 meta），不 500
        report = _empty_report()
        degraded = True

    html = PublicDigestRenderer().render(report, rd, degraded=degraded)
    return HTMLResponse(html, status_code=200)


@router.get("/sitemap.xml", response_class=Response, tags=["公开页 SEO"])
async def sitemap():
    """动态 sitemap：列出最近 N 天公开简报日期，<loc> 用 PUBLIC_BASE_URL 拼绝对地址。"""
    base = _public_base_url()
    try:
        db = get_db()
        dates = (db.get_report_dates() or [])[:SITEMAP_DAYS]
    except Exception:
        dates = []  # DB 不可达：返回合法空 sitemap，不 500

    urls = []
    for d in dates:
        d = str(d)[:10]
        urls.append(
            f"  <url>\n"
            f"    <loc>{base}/digest/{d}</loc>\n"
            f"    <lastmod>{d}</lastmod>\n"
            f"    <changefreq>daily</changefreq>\n"
            f"    <priority>0.8</priority>\n"
            f"  </url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse, tags=["公开页 SEO"])
async def robots():
    """允许索引并指向 sitemap。"""
    base = _public_base_url()
    return PlainTextResponse(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
