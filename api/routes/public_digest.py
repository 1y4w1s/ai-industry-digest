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

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from api.models.database import get_db

# 复用邮件简报的取数 + 聚类口径（同一份 cluster_stories 数据，与邮件同源）
from scripts.newsletter import build_report, NewsletterRenderer
from api.services.html_renderers import render_main_thread, fmt_github_card

# 公开页常量
DEFAULT_PUBLIC_BASE_URL = "http://localhost:8000"   # 生产环境应设置 PUBLIC_BASE_URL 环境变量
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

        return f"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<title>{escape(title)}</title>
<meta name="description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{escape(self.product_name)}">
<meta property="og:image" content="{self.base_url}/og/digest/{date_str}.svg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{escape(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{self.base_url}/og/digest/{date_str}.svg">
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

        main_thread_html, main_thread_note = render_main_thread(report, escape)
        articles_html = self._render_articles(report, escape)
        github_html = self._render_github_agents(report, escape, report.get("gh_filter") or {}, report_date)
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
    {github_html}
    <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:18px 28px;font-size:12px;color:#9ca3af;">
      <p style="margin:0 0 6px;">{escape(self.product_name)} 每日 AI 情报简报 · 公开归档页。编辑部每日精选值得关注的 AI 信号，可自由阅读、分享。</p>
      <p style="margin:0;"><a href="{escape(archive_url)}" style="color:#6b7280;">往期归档</a> · <a href="{escape(home_url)}" style="color:#6b7280;">返回首页</a></p>
    </div>
  </div>
</body>
</html>"""

    def _render_github_agents(self, report: dict, escape, gh_filter: dict, report_date) -> str:
        """公开页「今日 GitHub 推荐」卡片：含时间范围 / 最低 star / 排序筛选器（整页刷新）。"""
        items = report.get("github_agents") or []
        f_range = gh_filter.get("range", "week")
        f_min = gh_filter.get("min_stars", 100)
        f_sort = gh_filter.get("sort", "stars")
        date_str = report_date.isoformat()
        form = (
            f'<form method="get" action="/digest/{escape(date_str)}" '
            f'style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px;">'
            f'<label style="font-size:12px;color:#6b7280;">时间范围'
            f'<select name="gh_range" style="margin-left:4px;padding:4px 6px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;">'
            f'<option value="week"{" selected" if f_range=="week" else ""}>最近一周</option>'
            f'<option value="month"{" selected" if f_range=="month" else ""}>最近一个月</option>'
            f'<option value="quarter"{" selected" if f_range=="quarter" else ""}>最近三个月</option>'
            f'</select></label>'
            f'<label style="font-size:12px;color:#6b7280;">最低 Star'
            f'<input name="gh_min_stars" type="number" min="0" step="50" value="{f_min}" '
            f'style="margin-left:4px;width:80px;padding:4px 6px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;"/></label>'
            f'<label style="font-size:12px;color:#6b7280;">排序'
            f'<select name="gh_sort" style="margin-left:4px;padding:4px 6px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;">'
            f'<option value="stars"{" selected" if f_sort=="stars" else ""}>Star 降序</option>'
            f'<option value="trending"{" selected" if f_sort=="trending" else ""}>新星飙升</option>'
            f'</select></label>'
            f'<button type="submit" style="padding:5px 12px;background:#0f172a;color:#fff;border:none;border-radius:6px;font-size:12px;cursor:pointer;">应用</button>'
            f'</form>'
        )
        if not items:
            cards = ('<p style="font-size:13px;color:#9ca3af;margin:0;">'
                     '暂无匹配项目（GitHub API 限流中，或该范围内暂无高星 Agent 项目；可放宽条件后重试）。</p>')
        else:
            cards = "\n".join(fmt_github_card(it, escape) for it in items)
        return f"""<div style="padding:0 28px 24px;">
      <div style="background:#fafaf9;border:1px solid #e7e5e4;border-radius:14px;padding:16px 18px;">
        <div style="font-family:'Fraunces',Georgia,'Songti SC',serif;font-size:19px;font-weight:700;color:#0F4C3A;margin-bottom:4px;">今日 GitHub 推荐</div>
        <div style="font-size:13px;color:#6b7280;margin-bottom:10px;line-height:1.6;">实时从 GitHub 发掘近期最活跃的 AI Agent 开源项目，按 Star 数排序，帮你快速发现有价值的工具与框架。</div>
        {form}
        {cards}
      </div>
    </div>"""

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
        "github_agents": [],
        "gh_filter": {},
    }


def _parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


@router.get("/digest/{report_date}", response_class=HTMLResponse, tags=["公开页 SEO"])
async def public_digest(
    report_date: str,
    gh_range: str = Query("week"),
    gh_min_stars: int = Query(100),
    gh_sort: str = Query("stars"),
):
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
        gh_params = {"range": gh_range, "min_stars": gh_min_stars,
                     "sort": gh_sort, "limit": 30}
        report = build_report(db, rd, TOP_N, gh_params=gh_params)
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


# OG 图片（社交分享卡片，1200×630）— 用于 /digest/{date} 的 og:image
# 设计：暖白底 + 墨绿主色 + Fraunces 标题大字号 + 编辑部 eyebrow + 主线标题
# 零外部依赖，纯 SVG 文本生成
@router.get("/og/digest/{report_date}.svg", response_class=Response, tags=["公开页 SEO"])
async def og_digest_svg(report_date: str):
    """生成 /digest/{date} 分享卡片 SVG。

    - 拉取 build_report 取主线条目标题（最多 3 条）
    - 失败/无数据 → 仍返回合法 SVG（带日期 + "今日速览"）
    - 1200×630 (Twitter Card / Facebook OG 标准)
    """
    try:
        rd = _parse_date(report_date)
        db = get_db()
        report = build_report(db, rd, 3)
        main_thread = (report.get("main_thread") or [])[:3]
    except Exception:
        main_thread = []
        rd = None

    # SVG 内容（escape 防 XSS，因为标题是用户内容）
    def esc(s):
        return html.escape(str(s)) if s else ""

    date_str = rd.strftime("%Y年%m月%d日") if rd else esc(report_date)
    headlines_html = ""
    if main_thread:
        items = []
        for idx, s in enumerate(main_thread[:3]):
            # main_thread 可能是 List[str]（占位）或 List[dict]（结构化）
            if isinstance(s, str):
                title = esc(s[:60])
                entity = ""
            else:
                title = esc((s.get("title") or s.get("entity") or "主线")[:60])
                entity = esc(s.get("entity") or "")
            if entity:
                items.append(
                    f'<g transform="translate(80, {260 + 70 * idx})">'
                    f'<rect width="56" height="22" rx="11" fill="#E0B040" opacity="0.18"/>'
                    f'<text x="28" y="16" text-anchor="middle" font-family="ui-monospace, monospace" '
                    f'font-size="11" font-weight="700" fill="#0F4C3A" letter-spacing="0.5">{entity}</text>'
                    f'<text x="76" y="17" font-family="Georgia, serif" '
                    f'font-size="24" font-weight="600" fill="#0F4C3A">{title}</text>'
                    f'</g>'
                )
            else:
                items.append(
                    f'<text x="80" y="{275 + 70 * idx}" '
                    f'font-family="Georgia, serif" font-size="26" font-weight="600" fill="#0F4C3A">{title}</text>'
                )
        headlines_html = "\n".join(items)
    else:
        headlines_html = (
            '<text x="80" y="290" font-family="var(--font-display, Georgia, serif)" '
            'font-size="32" font-weight="500" fill="#9CA3AF" font-style="italic">暂无主线数据</text>'
        )

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <!-- 暖白底 -->
  <rect width="1200" height="630" fill="#F9F7F3"/>
  <!-- 顶部品牌条 -->
  <rect width="1200" height="6" fill="#0F4C3A"/>
  <!-- 品牌 K 标志 -->
  <g transform="translate(80, 80)">
    <rect width="48" height="48" rx="10" fill="#0F4C3A"/>
    <text x="24" y="34" text-anchor="middle" font-family="Georgia, serif" font-size="28" font-weight="700" fill="#FFFFFF">K</text>
  </g>
  <text x="148" y="115" font-family="Georgia, serif" font-size="32" font-weight="700" fill="#0F4C3A" letter-spacing="-0.5">Signal</text>
  <text x="270" y="115" font-family="var(--font-mono, monospace)" font-size="14" font-weight="500" fill="#5E5A52" letter-spacing="2">SIGNAL · 每日速览</text>
  <!-- eyebrow 日期 -->
  <text x="80" y="195" font-family="var(--font-mono, monospace)" font-size="14" font-weight="600" fill="#B8860B" letter-spacing="3">{esc(date_str)}</text>
  <!-- 主标题（固定） -->
  <text x="80" y="240" font-family="Georgia, serif" font-size="42" font-weight="700" fill="#0F4C3A" letter-spacing="-0.5">今天的 AI 行业脉搏</text>
  <!-- 主线条目（动态） -->
  {headlines_html}
  <!-- 底部品牌 -->
  <text x="80" y="580" font-family="var(--font-mono, monospace)" font-size="13" font-weight="500" fill="#5E5A52" letter-spacing="2">{esc(_public_base_url())} · 由编辑部精选</text>
  <text x="1120" y="580" text-anchor="end" font-family="var(--font-mono, monospace)" font-size="13" font-weight="600" fill="#0F4C3A" letter-spacing="1">EDITORIAL</text>
</svg>'''
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=300"},
    )
