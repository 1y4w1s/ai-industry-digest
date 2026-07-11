"""
Signal - 播客音频生成（改造计划 §2.2：对标 Rundown audio）

把每日简报多做一个**音频形态**：

  build_script(date)  把当日文章拼成一段口语化播报稿（复用 cluster_stories 同份数据 + 文章 summary/so_what）。
                     纯函数、不依赖 TTS，便于单测。
  generate(date)      build_script → text_to_mp3 生成 media/podcast/{date}.mp3，记录字节长度供 RSS 的 length 字段。
                     优雅降级：TTS 失败 / 当天无文章 → 跳过该天、不抛错、不写进 RSS（避免坏 enclosure）。

约束遵守：
  - 服务端 TTS 是**新增**能力（仓库原本只有前端浏览器 Web Speech API，产不出 mp3）。
    封装见 api.services.tts.text_to_mp3（默认 edge-tts，可选 OpenAI TTS）。
  - build_script 复用 §2.1 的 cluster_stories()（与邮件/公开页同源），不重写 reporter。
  - 不照抄邮件 HTML；播报稿为独立口语化文本。
  - 不碰邮件 / 退订 / 像素逻辑。
  - 不引入重依赖。

用法：
  python scripts/podcast.py generate [--date YYYY-MM-DD] [--top-n 8]
  python scripts/podcast.py script  [--date YYYY-MM-DD] [--top-n 8]   # 仅打印播报稿，不调 TTS

说明：
  - 不传 --date 时取「今天」（与 daily.yml 的 08:00 北京时间调度口径一致）。
  - generate 默认取当天文章；若当天无文章则回退到窗口内最新文章（与 newsletter.build_report 同口径）。
  - TTS 失败 / 当天无任何文章 → 跳过该天、返回 None、不写坏文件，避免 RSS 出现不可播放的 enclosure。
"""

from __future__ import annotations

import os
import sys
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

# 允许以 `python scripts/podcast.py` 直接运行（项目根加入 path）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from collector.base import Article
from processor.reporter import cluster_stories

# 服务端 TTS（新增封装；缺失依赖时由 generate 捕获降级）
from api.services.tts import text_to_mp3

# 复用邮件简报的「取数 + so_what 补回」逻辑，避免重复写 DB 访问
from scripts.newsletter import _rows_to_articles

# 音频落地目录：media/podcast/{date}.mp3
MEDIA_DIR = Path(PROJECT_ROOT) / "media" / "podcast"

# 取数窗口（天）：与 newsletter.build_report 一致，取当天；当天无则回退窗口内最新
FETCH_WINDOW_DAYS = 3
DEFAULT_TOP_N = 8


# ──────────────────────────────────────────────────────────────
# 1. 取数：复用 newsletter 的 DB 访问口径（仅取 Article 列表）
# ──────────────────────────────────────────────────────────────

def _get_db():
    from api.models.database import DatabaseManager
    return DatabaseManager()


def _fetch_day_articles(db, report_date: date, window_days: int = FETCH_WINDOW_DAYS,
                        fallback_n: int = DEFAULT_TOP_N) -> List[Article]:
    """取 report_date 当天的文章（与 newsletter 同口径）；当天无则回退窗口内最新。"""
    from_date = (report_date - timedelta(days=window_days)).isoformat()
    res = db.get_articles(
        page=1, page_size=300, date_from=from_date,
        sort_by="published_at", sort_order="desc", use_cache=False,
    )
    rows = res.get("items", []) if isinstance(res, dict) else []
    articles = _rows_to_articles(rows)

    day_articles = [a for a in articles
                    if a.published_at and a.published_at.date() == report_date]
    if not day_articles:
        day_articles = articles[:fallback_n]
    return day_articles


def _demo_articles(report_date: date) -> List[Article]:
    """合成文章（无 DB 也能验证 generate 全链路；镜像 newsletter._demo_report 口径）。"""
    now = datetime(report_date.year, report_date.month, report_date.day, 9, 0, 0)
    sample = [
        {
            "title": "OpenAI 发布 GPT-6，推理成本下降 70%",
            "url": "https://example.com/1", "source_name": "机器之心",
            "summary": "OpenAI 今日发布 GPT-6，官方称推理成本较上代下降 70%，长上下文翻倍。",
            "tags": ["大模型", "OpenAI"], "importance": "high", "importance_reason": "行业重磅",
            "so_what": "对中小团队意味着 API 成本大幅下降，可以更低门槛把多模态能力塞进产品。",
            "published_at": now.isoformat(),
        },
        {
            "title": "GPT-6 发布后媒体解读：长上下文翻倍意味着什么",
            "url": "https://example.com/2", "source_name": "机器之心",
            "summary": "多家媒体解读 GPT-6 的长上下文能力，认为将重塑 Agent 工作流。",
            "tags": ["大模型", "OpenAI"], "importance": "medium", "importance_reason": "工程利好",
            "so_what": "做 AI 应用的团队，可以把更复杂的多步任务交给模型自己串起来。",
            "published_at": now.isoformat(),
        },
        {
            "title": "Hugging Face 上线本地推理网关",
            "url": "https://example.com/3", "source_name": "Hugging Face",
            "summary": "HF 推出本地推理网关，支持私有化部署主流开源模型。",
            "tags": ["开源", "部署"], "importance": "medium", "importance_reason": "工程利好",
            "so_what": "数据合规要求高的团队，终于能绕开公有云把模型跑在自己机房。",
            "published_at": now.isoformat(),
        },
        {
            "title": "某独角兽被曝裁员 30%",
            "url": "https://example.com/4", "source_name": "36氪",
            "summary": "一家 AI 应用独角兽被曝裁员 30%，聚焦核心产品线。",
            "tags": ["行业"], "importance": "low", "importance_reason": "信号待验证",
            "so_what": None,
            "published_at": now.isoformat(),
        },
    ]
    return _rows_to_articles(sample)


# ──────────────────────────────────────────────────────────────
# 2. 播报稿：纯函数，复用 cluster_stories 同份数据（§2.1）
# ──────────────────────────────────────────────────────────────

def build_script(articles: List[Article], report_date: date,
                 top_n: int = DEFAULT_TOP_N) -> str:
    """把当日文章拼成一段口语化播报稿（纯函数，不依赖 TTS / DB）。

    复用 §2.1 的 cluster_stories() 产出「今日主线」，每条主线带代表性 summary +
    挂的文章标题；再追加 Top N 文章（含 so_what 观点层一句话）。带轻量开场/收尾。

    返回空字符串当且仅当 articles 为空（调用方据此跳过当天）。

    Args:
        articles: 当日 Article 列表（需含 title / summary / tags / published_at / so_what）。
        report_date: 简报日期（仅回显用）。
        top_n: 精选文章条数。

    Returns:
        str: 纯文本播报稿（不含 HTML，便于 TTS 朗读）。
    """
    if not articles:
        return ""

    clusters = cluster_stories(articles, report_date)
    stories = (clusters.get("stories") or []) if isinstance(clusters, dict) else []

    # Top N 文章：按重要性降序（高→中→低），再按标题稳定排序
    _weight = {"high": 3, "medium": 2, "low": 1}
    ranked = sorted(
        articles,
        key=lambda a: (-_weight.get((getattr(a, "importance", None) or "low").lower(), 1),
                       (a.title or "").lower()),
    )
    top = ranked[:top_n]

    lines: List[str] = []
    date_str = report_date.isoformat()

    # ── 开场 ──
    lines.append(f"大家好，欢迎收听 Signal 每日 AI 情报播客，今天是 {date_str}。")
    lines.append("我们用几分钟，帮你梳理今天 AI 领域最值得关注的主线与精选。")
    lines.append("")

    # ── 今日主线（事件聚类，与邮件/公开页同源）──
    if stories:
        lines.append("先说今天的几条主线。")
        for i, s in enumerate(stories, 1):
            title = (s.get("title") or "今日 AI 动态").strip()
            entity = s.get("entity")
            summary = (s.get("summary") or "").strip()
            head = f"主线 {i}，{title}。"
            if entity:
                head += f"围绕{entity}展开。"
            lines.append(head)
            if summary:
                lines.append(summary)
            hung = s.get("articles") or []
            if hung:
                titles = "、".join(
                    (a.get("title") or "") for a in hung[:3] if a.get("title")
                )
                if titles:
                    lines.append(f"相关报道包括：{titles}。")
            lines.append("")
    else:
        lines.append("今天没有特别突出的单一主线，我们直接进入精选文章。")
        lines.append("")

    # ── 今日精选（Top N，含 so_what 观点层）──
    lines.append("接下来是今天的精选文章。")
    for a in top:
        t = (a.title or "").strip()
        src = (a.source_name or "").strip()
        line = f"{t}。"
        if src:
            line += f"来自{src}。"
        sw = getattr(a, "so_what", None)
        if sw:
            line += f"So What，对你意味着什么：{sw}"
        else:
            summ = (a.summary or "").strip()
            if summ:
                line += summ
        lines.append(line)
    lines.append("")

    # ── 收尾 ──
    lines.append(
        "以上就是今天的 Signal 每日 AI 情报播客。把复杂的 AI 世界，"
        "压缩成你通勤路上的一段声音。我们明天见。"
    )

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 3. 生成：build_script → text_to_mp3 → media/podcast/{date}.mp3
# ──────────────────────────────────────────────────────────────

def generate(report_date: Optional[date] = None, top_n: int = DEFAULT_TOP_N,
             demo: bool = False) -> Optional[str]:
    """生成指定日期的播客 mp3。

    优雅降级（返回 None，不抛错，不写坏文件）：
      - 取数失败（DB 不可达）
      - 当天无任何文章
      - 播报稿为空
      - TTS 失败（依赖缺失 / 网络 / 服务错误）

    Args:
        report_date: 简报日期（缺省今天）。
        top_n: 精选文章条数。
        demo: True 时用合成文章（无需 Supabase），便于本地验收全流程。

    Returns:
        Optional[str]: 成功时返回 mp3 绝对路径；被跳过时返回 None。
    """
    report_date = report_date or date.today()
    date_str = report_date.isoformat()

    # 1) 取数
    if demo:
        articles = _demo_articles(report_date)
    else:
        try:
            db = _get_db()
            articles = _fetch_day_articles(db, report_date)
        except Exception as e:
            print(f"[PODCAST] 取数失败，跳过 {date_str}: {e}")
            return None

    if not articles:
        print(f"[PODCAST] 当天无文章，跳过 {date_str}")
        return None

    # 2) 拼播报稿（纯函数）
    script = build_script(articles, report_date, top_n=top_n)
    if not script.strip():
        print(f"[PODCAST] 播报稿为空，跳过 {date_str}")
        return None

    # 3) TTS → mp3（失败则清理半成品并跳过，避免坏 enclosure）
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = MEDIA_DIR / f"{date_str}.mp3"
    try:
        size = text_to_mp3(script, str(out_path))
    except Exception as e:
        print(f"[PODCAST] TTS 生成失败，跳过 {date_str}: {e}")
        if out_path.exists():
            try:
                out_path.unlink()
            except OSError:
                pass
        return None

    print(f"[PODCAST] 已生成 {out_path}（{size} bytes）")
    return str(out_path)


# ──────────────────────────────────────────────────────────────
# 4. CLI
# ──────────────────────────────────────────────────────────────

def _date_type(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main():
    parser = argparse.ArgumentParser(description="Signal 播客音频生成（§2.2）")
    sub = parser.add_subparsers(dest="cmd")

    p_gen = sub.add_parser("generate", help="生成当日播客 mp3 到 media/podcast/")
    p_gen.add_argument("--date", type=_date_type, default=date.today())
    p_gen.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    p_gen.add_argument("--demo", action="store_true",
                       help="用合成文章（无需 Supabase），便于本地验收全流程")

    p_script = sub.add_parser("script", help="仅打印播报稿（不调 TTS，便于调试）")
    p_script.add_argument("--date", type=_date_type, default=date.today())
    p_script.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    p_script.add_argument("--demo", action="store_true",
                          help="用合成文章（无需 Supabase）")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "generate":
        generate(args.date, top_n=args.top_n, demo=args.demo)
    elif args.cmd == "script":
        if args.demo:
            articles = _demo_articles(args.date)
        else:
            try:
                db = _get_db()
                articles = _fetch_day_articles(db, args.date)
            except Exception as e:
                print(f"[PODCAST] 取数失败: {e}")
                return
        print(build_script(articles, args.date, top_n=args.top_n))


if __name__ == "__main__":
    main()
