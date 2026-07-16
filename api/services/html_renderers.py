"""
Signal · 共享 HTML 渲染函数

消除 scripts/newsletter.py 与 api/routes/public_digest.py 之间的重复代码。
"""

# ── 共享常量 ───────────────────────────────────────
COLOR_IMPORTANCE = {"high": "#dc2626", "medium": "#d97706", "low": "#6b7280"}
FONT_DISPLAY = "'Fraunces',Georgia,'Songti SC',serif"
FONT_MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Consolas,monospace"
BADGE_STYLE = "font-size:11px;padding:1px 8px;border-radius:999px;"
MAIN_THREAD_NOTE_CLUSTER = "事件聚类自动生成 · 同一事件的多篇报道已合并"
MAIN_THREAD_NOTE_FALLBACK = "（暂无可聚类信号，显示热度 Top 候选）"


# ── 主线渲染 ───────────────────────────────────────
def render_main_thread(report: dict, escape, max_width: str = "100%") -> tuple:
    """
    渲染「今日主线」HTML 区块。

    返回 (main_thread_html: str, note: str)
    两个调用方（邮件 / 公开页）可通过 max_width 参数控制容器宽度。
    """
    main_stories = report.get("main_stories") or {}
    stories = main_stories.get("stories") if isinstance(main_stories, dict) else []

    if stories:
        blocks = []
        for s in stories:
            entity = s.get("entity")
            badge = (
                f'<span style="{BADGE_STYLE}'
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
        return "\n".join(blocks), MAIN_THREAD_NOTE_CLUSTER

    # 聚类无结果：回退展示 main_thread 占位字符串列表
    fallback = report.get("main_thread") or []
    main_thread_html = "\n".join(
        f'<li style="font-size:13px;line-height:1.6;color:#374151;margin-bottom:4px;">'
        f'{escape(b)}</li>' for b in fallback
    )
    return main_thread_html, MAIN_THREAD_NOTE_FALLBACK


# ── GitHub 卡片 ─────────────────────────────────────
def fmt_github_card(item: dict, escape) -> str:
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
      <div style="font-family:{FONT_MONO};font-size:15px;font-weight:600;color:#111827;margin-bottom:4px;">
        <a href="{url}" style="color:#111827;text-decoration:none;">{name}</a>{rising_badge}
      </div>
      <p style="font-size:13px;line-height:1.6;color:#374151;margin:0 0 6px;">{desc}</p>
      <div style="font-family:{FONT_MONO};font-size:12px;color:#6b7280;">★ {stars:,}{lang_badge} · 更新于 {pushed_date}</div>
    </div>"""
