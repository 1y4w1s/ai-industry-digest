"""
Signal - 播客 RSS（改造计划 §2.2：对标 Rundown audio）

提供 GET /podcast.xml，列出**最近 N 天已生成音频**的日期，输出标准 podcast RSS。

设计约束遵守：
  - 仅列出确有 mp3 的日期（扫描 media/podcast/*.mp3），无音频不列，避免坏 enclosure。
  - enclosure 用「PUBLIC_BASE_URL/podcast/{date}.mp3」绝对地址；
    PUBLIC_BASE_URL 取值逻辑**复用** public_digest._public_base_url（环境变量覆盖 + 缺省 8080 域名）。
  - 音频静态托管在 /podcast（见 api/main.py 的 StaticFiles 挂载），与 frontend/dist 并存不冲突。
  - 不依赖 Supabase；不碰邮件 / 退订 / 像素逻辑。
  - 不引入新重依赖；RSS 用字符串模板生成（标准 RSS 2.0）。
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import APIRouter
from fastapi.responses import Response

# 复用公开页的 PUBLIC_BASE_URL 取值逻辑（环境变量覆盖 + 缺省 8080 域名）
from api.routes.public_digest import _public_base_url

# media/podcast 目录（与 scripts/podcast.generate 落地路径一致）
PODCAST_DIR = Path(__file__).resolve().parent.parent.parent / "media" / "podcast"
PODCAST_DAYS = 30  # RSS 最多列出最近 N 天

router = APIRouter()


def _list_podcast_dates(days: int = PODCAST_DAYS) -> List[Tuple[date, int]]:
    """扫描 media/podcast/*.mp3，返回 [(date, 字节长度), ...]（按日期降序，截断到 days）。

    只认 YYYY-MM-DD.mp3 命名的文件；其它文件（如临时/非日期命名）忽略。
    无目录或无文件时返回空列表。
    """
    if not PODCAST_DIR.exists():
        return []
    out: List[Tuple[date, int]] = []
    for p in PODCAST_DIR.glob("*.mp3"):
        stem = p.stem
        try:
            d = datetime.strptime(stem, "%Y-%m-%d").date()
        except ValueError:
            continue  # 非日期命名，跳过（避免坏项）
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        out.append((d, size))
    out.sort(key=lambda x: x[0], reverse=True)
    return out[:days]


def _build_rss(items: List[Tuple[date, int]], base_url: Optional[str] = None) -> str:
    """由已生成音频的 (date, size) 列表生成标准 podcast RSS 2.0 字符串。"""
    base = (base_url or _public_base_url()).rstrip("/")

    item_xml: List[str] = []
    for d, size in items:
        date_str = d.isoformat()
        url = f"{base}/podcast/{date_str}.mp3"
        pub = d.strftime("%a, %d %b %Y 00:00:00 +0800")  # RFC 822
        item_xml.append(
            "    <item>\n"
            f"      <title>Signal 每日 AI 情报播客 · {date_str}</title>\n"
            f"      <description>Signal 每日 AI 情报简报音频版（{date_str}），"
            f"每日自动生成，对标 Rundown audio。</description>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f'      <guid isPermaLink="false">{url}</guid>\n'
            f'      <enclosure url="{url}" type="audio/mpeg" length="{size}" />\n'
            "    </item>"
        )

    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>Signal 每日 AI 情报播客</title>\n"
        f"    <link>{base}/</link>\n"
        f"    <language>zh-CN</language>\n"
        f"    <description>Signal 每日 AI 情报简报的音频版，每日自动生成，对标 Rundown audio。</description>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f'    <atom:link rel="self" href="{base}/podcast.xml" />\n'
        + "\n".join(item_xml) + "\n"
        "  </channel>\n"
        "</rss>"
    )
    return xml


@router.get("/podcast.xml", response_class=Response, tags=["播客 RSS"])
async def podcast_feed():
    """播客 RSS：仅列出确有音频的日期，enclosure 为绝对 mp3 URL。"""
    items = _list_podcast_dates(PODCAST_DAYS)
    xml = _build_rss(items, _public_base_url())
    return Response(content=xml, media_type="application/rss+xml")
