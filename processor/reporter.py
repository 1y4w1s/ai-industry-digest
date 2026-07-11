"""
Signal - 日报生成器
按重要性分组、提取热点关键词、生成概览、写入数据库
"""

from datetime import date, datetime
from typing import List, Dict, Tuple
from collections import Counter
import json
import re

from collector.base import Article
from processor.ai_processor import AIProcessor


class DailyReportGenerator:
    """日报生成器"""

    def __init__(self, db_manager=None, ai_processor: AIProcessor = None):
        """
        Args:
            db_manager: DatabaseManager 实例
            ai_processor: AIProcessor 实例
        """
        self.db = db_manager
        self.ai = ai_processor

    def generate(self, articles: List[Article], report_date: date = None) -> dict:
        """生成单日日报数据
        Returns:
            dict: 日报数据，包含概览、分组文章、关键词等
        """
        if not articles:
            return self._empty_report(report_date)

        report_date = report_date or date.today()
        print(f"   📰 生成日报: {report_date}")

        # 1. 按重要性分组
        grouped = self._group_by_importance(articles)
        print(f"      高: {len(grouped['high'])} | 中: {len(grouped['medium'])} | 低: {len(grouped['low'])}")

        # 2. 提取热点关键词
        keywords = self._extract_keywords(articles)
        print(f"      热点关键词: {', '.join(keywords[:5])}")

        # 3. 生成概览
        insight = ""
        if self.ai:
            try:
                insight = self.ai.generate_summary_insight(articles)
                print(f"      概览已生成")
            except Exception as e:
                print(f"       [WARN] 概览生成失败: {e}")
                insight = self._generate_fallback_insight(articles)

        # 4. 构建日报数据
        report = {
            "report_date": report_date.isoformat(),
            "total_articles": len(articles),
            "source_count": len(set(a.source_name for a in articles)),
            "summary_insight": insight,
            "trending_keywords": keywords[:10],
            "articles": {
                "high": self._serialize_articles(grouped["high"]),
                "medium": self._serialize_articles(grouped["medium"]),
                "low": self._serialize_articles(grouped["low"]),
            }
        }

        # 5. 写入数据库
        if self.db:
            try:
                self._save_to_db(report, articles)
                print(f"      💾 日报已写入数据库")
            except Exception as e:
                print(f"       [ERROR] 写入数据库失败: {e}")

        return report

    def generate_grouped_by_date(self, articles: List[Article]) -> Dict[str, dict]:
        """按文章实际发布日期分组，每组生成一个独立日报

        Args:
            articles: 采集到的文章列表（可能跨多个日期）

        Returns:
            dict: {date_str: report_dict, ...}
        """
        if not articles:
            today = date.today().isoformat()
            return {today: self._empty_report(date.today())}

        # 1. 按 published_at 分组
        date_groups: Dict[str, List[Article]] = {}
        for a in articles:
            key = a.published_at.date().isoformat() if a.published_at else date.today().isoformat()
            date_groups.setdefault(key, []).append(a)

        print(f"\n📅 按发布日期分组，共 {len(date_groups)} 个日期:")
        for d in sorted(date_groups.keys()):
            print(f"   {d}: {len(date_groups[d])} 篇")

        # 2. 每组独立生成日报
        reports = {}
        for day in sorted(date_groups.keys()):
            day_date = datetime.strptime(day, "%Y-%m-%d").date()
            reports[day] = self.generate(date_groups[day], report_date=day_date)

        return reports

    # ── 按重要性分组 ──────────────────────────

    def _group_by_importance(self, articles: List[Article]) -> Dict[str, List[Article]]:
        """按重要性分组"""
        groups = {"high": [], "medium": [], "low": []}
        for a in articles:
            imp = a.importance or "low"
            if imp in groups:
                groups[imp].append(a)
            else:
                groups["low"].append(a)
        return groups

    # ── 提取热点关键词 ────────────────────────

    def _extract_keywords(self, articles: List[Article]) -> List[str]:
        """从文章标签和标题中提取热点关键词"""
        tag_counter = Counter()
        word_counter = Counter()

        # 统计标签
        for a in articles:
            for tag in (a.tags or []):
                tag_counter[tag] += 1

        # 从标题中提取关键词（取高频词）
        import jieba
        import re
        # 停用词表（精简版）
        stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不",
                      "人", "都", "一", "一个", "上", "也", "很", "到",
                      "说", "要", "去", "你", "会", "着", "没有", "看",
                      "好", "自己", "这", "他", "她", "它", "们", "与",
                      "及", "或", "等", "从", "被", "把", "对", "为",
                      "the", "a", "an", "and", "or", "for", "of", "in",
                      "to", "is", "it", "on", "with", "by", "as", "at",
                      "that", "this", "from", "are", "was", "be", "has",
                      "have", "not", "but", "we", "its", "their"}

        def is_meaningful_word(w: str) -> bool:
            """判断是否为有意义的词：中文词（长度>=2）或英文词（长度>=4）"""
            if not w:
                return False
            if re.match(r'^[\u4e00-\u9fff]+$', w):  # 中文
                return len(w) >= 2
            if re.match(r'^[a-zA-Z]+$', w):  # 英文
                return len(w) >= 4
            return False

        for a in articles:
            words = jieba.lcut(a.title)
            for w in words:
                w = w.strip().lower()
                if is_meaningful_word(w) and w not in stop_words:
                    word_counter[w] += 1

        # 合并标签和标题关键词
        combined = tag_counter + word_counter
        # 过滤掉单次出现的词
        keywords = [w for w, c in combined.most_common(20) if c >= 2]
        return keywords[:10] if keywords else [w for w, _ in combined.most_common(10)]

    # ── 概览（备选） ─────────────────────────

    def _generate_fallback_insight(self, articles: List[Article]) -> str:
        """当 AI 概览失败时，用规则生成简单概览"""
        high_count = sum(1 for a in articles if a.importance == "high")
        sources = set(a.source_name for a in articles)
        keywords = self._extract_keywords(articles)

        insight = (
            f"今日共收录 {len(articles)} 篇文章，"
            f"覆盖 {len(sources)} 个信息源，"
            f"其中高重要性文章 {high_count} 篇。"
        )
        if keywords:
            insight += f" 热点关键词: {'、'.join(keywords[:5])}。"
        return insight

    # ── 序列化 ─────────────────────────────

    def _serialize_articles(self, articles: List[Article]) -> List[dict]:
        """将 Article 对象转为可 JSON 序列化的字典"""
        return [
            {
                "title": a.title,
                "url": a.url,
                "source_name": a.source_name,
                "summary": a.summary or "",
                "tags": a.tags or [],
                "importance": a.importance or "low",
                "reason": a.importance_reason or "",
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ]

    # ── 写入数据库 ─────────────────────────

    def _save_to_db(self, report: dict, articles: List[Article]):
        """将日报写入 daily_reports 表"""
        if not self.db:
            return

        # 从数据库查询文章的 UUID
        article_uuids = []
        for article in articles:
            try:
                result = self.db.client.table("articles") \
                    .select("id") \
                    .eq("url", article.url) \
                    .execute()
                if result.data:
                    article_uuids.append(result.data[0]["id"])
            except Exception:
                pass

        data = {
            "report_date": report["report_date"],
            "article_ids": article_uuids if article_uuids else None,
            "summary_insight": report["summary_insight"],
            "trending_keywords": report["trending_keywords"],
            "trend_analysis": "",
        }
        self.db.client.table("daily_reports").upsert(
            data,
            on_conflict="report_date"
        ).execute()

    # ── 空日报 ─────────────────────────────

    def _empty_report(self, report_date: date = None) -> dict:
        """生成空日报"""
        report_date = report_date or date.today()
        return {
            "report_date": report_date.isoformat(),
            "total_articles": 0,
            "source_count": 0,
            "summary_insight": "今日暂无收录内容。",
            "trending_keywords": [],
            "articles": {"high": [], "medium": [], "low": []}
        }


# ════════════════════════════════════════════════════════════
# 2.1 事件聚类 / 今日主线（改造计划 §2.1）
# 纯函数、无 DB / LLM 依赖、确定性可复现（同输入同输出）。
# 口径：规则启发式——「实体共现」为主强信号，辅以「具体标签 + 标题实义词重叠」。
# 同一事件的多篇报道（如「GPT-6 发布」+「媒体解读稿」）因共享实体而被拧成一条主线。
# ════════════════════════════════════════════════════════════

# 通用 / 弱区分度标签：不靠它们做强合并，避免把整页文章揉成一条。
_GENERIC_TAGS = {
    "行业", "新闻", "资讯", "快讯", "动态", "要闻", "今日", "日报", "汇总",
    "综述", "观点", "AI", "人工智能", "大模型", "科技", "科技圈", "热点",
    "推荐", "精选", "话题", "观察", "分析", "解读", "报告", "数据",
}

# 实体词典：canonical -> [正则模式...]（均以 IGNORECASE 预编译）
# 用「实体共现」作为强合并信号。覆盖 AI 公司 / 模型族 / 产品 / 人物。
_ENTITY_SPEC = [
    ("GPT",          [r"gpt[-\s]?\d+(?:\.\d+)?", r"\bgpt\b"]),
    ("ChatGPT",      [r"chatgpt"]),
    ("Claude",       [r"claude[-\s]?\d+(?:\.\d+)?", r"\bclaude\b"]),
    ("Llama",        [r"llama[-\s]?\d+(?:\.\d+)?", r"\bllama\b"]),
    ("Fable",        [r"fable[-\s]?\d+(?:\.\d+)?", r"\bfable\b"]),
    ("Gemini",       [r"gemini[-\s]?\d+(?:\.\d+)?", r"\bgemini\b"]),
    ("Qwen",         [r"qwen", r"通义"]),
    ("DeepSeek",     [r"deepseek", r"深度求索"]),
    ("OpenAI",       [r"openai"]),
    ("Google",       [r"google", r"谷歌"]),
    ("Anthropic",    [r"anthropic"]),
    ("Meta",         [r"\bmeta\b"]),                 # 词边界，避免误并 metadata / meta-learning
    ("Microsoft",    [r"microsoft", r"微软"]),
    ("NVIDIA",       [r"nvidia", r"英伟达"]),
    ("Mistral",      [r"mistral"]),
    ("xAI",          [r"\bxai\b", r"grok"]),
    ("Perplexity",   [r"perplexity"]),
    ("Hugging Face", [r"hugging[\s-]?face", r"\bhf\b"]),
    ("Stable Diffusion", [r"stable[\s-]?diffusion", r"sdxl", r"sd3"]),
    ("Midjourney",   [r"midjourney"]),
    ("Runway",       [r"runway"]),
    ("百度",          [r"百度", r"文心", r"ernie"]),
    ("腾讯",          [r"腾讯", r"混元", r"hunyuan"]),
    ("字节跳动",       [r"字节", r"豆包", r"doubao", r"coze", r"扣子"]),
    ("华为",          [r"华为", r"盘古", r"pangu"]),
    ("月之暗面",       [r"月之暗面", r"kimi", r"moonshot"]),
    ("智谱",          [r"智谱", r"chatglm", r"\bglm\b", r"zhipu"]),
    ("MiniMax",      [r"minimax", r"abab"]),
    ("百川",          [r"百川", r"baichuan"]),
    ("Cursor",       [r"cursor"]),
    ("Apple",        [r"apple", r"苹果"]),
    ("Tesla",        [r"tesla", r"特斯拉"]),
    ("马斯克",         [r"马斯克", r"\bmusk\b"]),
    ("Sora",         [r"sora"]),
    ("DALL·E",  [r"dall"]),
    ("Agent",        [r"\bagent\b", r"智能体"]),
]

_ENTITY_RE = [
    (name, [re.compile(p, re.IGNORECASE) for p in pats])
    for name, pats in _ENTITY_SPEC
]

# 弱聚类（具体标签 + 标题实义词重叠）时忽略的高频词，减少噪声合并。
_WEAK_STOP = {
    "发布", "正式", "宣布", "推出", "公司", "模型", "今日", "我们", "已经", "表示",
    "消息", "报道", "一个", "可以", "支持", "能力", "用户", "产品", "团队", "版本",
    "最新", "全新", "全球", "国内", "国际", "研究", "论文", "训练", "数据", "系统",
    "平台", "服务", "技术", "应用", "行业", "市场", "旗下", "重磅", "首发", "首款",
    "亮相", "上线", "官宣", "回应", "计划", "对比", "评测", "实测", "体验", "盘点",
    "整理", "速览", "一文", "读懂", "深度", "全面", "完整", "进展", "如何", "为什么",
    "怎么", "即将", "开启", "内测", "公测", "测试", "体验版", "本轮", "知名",
}

# 单条主线挂文上限（超过则按实体子图拆分，避免一条主线塞太多无关文章）。
_MAX_STORY_ARTICLES = 12

# 重要性权重（用于热度计算，纯确定性）。
_IMPORTANCE_WEIGHT = {"high": 3, "medium": 2, "low": 1}


def _extract_entities(text: str) -> set:
    """从文本中抽出命中的 canonical 实体集合（确定性）。"""
    if not text:
        return set()
    low = text.lower()
    found = set()
    for name, regs in _ENTITY_RE:
        for r in regs:
            if r.search(low):
                found.add(name)
                break
    return found


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.\-]{3,}|[一-鿿]{2,}")


def _title_tokens(text: str) -> set:
    """标题中的实义词（英文 4+ 字符 / 中文 2+ 字），剔除高频噪声词。"""
    if not text:
        return set()
    toks = {m.group(0) for m in _TOKEN_RE.finditer(text.lower())}
    toks -= _WEAK_STOP
    return toks


def _imp_weight(a) -> int:
    return _IMPORTANCE_WEIGHT.get((getattr(a, "importance", None) or "low").lower(), 1)


def _serialize_article(a) -> dict:
    """将 Article 对象序列化为聚类主线下的挂文条目。"""
    pa = a.published_at.isoformat() if getattr(a, "published_at", None) else None
    return {
        "title": a.title,
        "url": a.url,
        "source_name": a.source_name,
        "summary": a.summary or "",
        "tags": a.tags or [],
        "importance": a.importance or "low",
        "reason": getattr(a, "importance_reason", None) or "",
        "published_at": pa,
        "so_what": getattr(a, "so_what", None),
    }


def _build_story(idxs: list, feats: list, report_date: date) -> dict:
    """由一组文章索引构建一个事件主线。"""
    arts = [feats[i]["art"] for i in idxs]
    # 确定性排序：重要性降序 -> 发布时间升序 -> 标题升序
    arts_sorted = sorted(arts, key=lambda a: (
        -_imp_weight(a),
        a.published_at.isoformat() if getattr(a, "published_at", None) else "9999",
        (a.title or "").lower(),
    ))
    # 实体频次 -> 代表实体（多数文章共享才作为主线实体）
    ent_counter = Counter()
    for i in idxs:
        ent_counter.update(feats[i]["ents"])
    dominant = None
    if ent_counter:
        # 确定性：先按频次降序，再按实体名升序。
        # （set 迭代顺序受 Python 进程内字符串哈希随机化影响，不能依赖 most_common 的插入序）
        best, best_c = sorted(ent_counter.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        if best_c >= max(1, len(idxs) // 2) or len(idxs) == 1:
            dominant = best

    rep = arts_sorted[0]
    size = len(arts_sorted)
    heat = sum(_imp_weight(a) for a in arts_sorted) * 10 + size
    rep_summary = rep.summary or ""
    if dominant:
        summary = f"围绕「{dominant}」的 {size} 篇相关报道。" + ((" " + rep_summary) if rep_summary else "")
    else:
        summary = rep_summary or f"今日 {size} 篇相关报道。"

    return {
        "title": (rep.title or "").strip() or "今日 AI 动态",
        "entity": dominant,
        "summary": summary,
        "heat": heat,
        "article_ids": [a.url for a in arts_sorted],
        "articles": [_serialize_article(a) for a in arts_sorted],
    }


def _story_sort_key(s: dict):
    """主线排序：热度降序 -> 最早发布升序（None 置后）-> 标题升序。"""
    earliest = "9999"
    for a in s.get("articles", []):
        pa = a.get("published_at") or ""
        if pa and (earliest == "9999" or pa < earliest):
            earliest = pa
    return (-s.get("heat", 0), earliest, s.get("title", ""))


def _split_by_entities(idxs: list, feats: list) -> list:
    """超大分量：仅在 idxs 内按实体共现重新聚类；仍超上限则按重要性截断。"""
    m = len(idxs)
    parent = list(range(m))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a in range(m):
        for b in range(a + 1, m):
            if feats[idxs[a]]["ents"] & feats[idxs[b]]["ents"]:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb
    groups: dict = {}
    for a in range(m):
        groups.setdefault(find(a), []).append(idxs[a])

    result = []
    for grp in groups.values():
        if len(grp) > _MAX_STORY_ARTICLES:
            grp_sorted = sorted(
                grp,
                key=lambda i: -_imp_weight(feats[i]["art"]),
            )
            result.append(grp_sorted[:_MAX_STORY_ARTICLES])
            for r in grp_sorted[_MAX_STORY_ARTICLES:]:
                result.append([r])
        else:
            result.append(grp)
    return result


def cluster_stories(articles: List[Article], report_date: date = None) -> dict:
    """跨文章按实体/主题/关键词聚类，产出「今日 N 条主线」。

    纯函数：不依赖数据库或 LLM，输入确定则输出确定（便于单测与每日复现）。
    若日后接入 LLM，应在此函数外层做降级——本实现为可独立单测的规则版。

    Args:
        articles: Article 对象列表（通常已是当日文章）。
        report_date: 简报日期（仅用于回显，不影响聚类）。

    Returns:
        dict: {
            "report_date": str,
            "stories": [ {title, entity, summary, heat, article_ids, articles}, ... ],
            "total_stories": int,
            "method": str,
        }
    """
    report_date = report_date or date.today()
    method = "rule-based heuristic (entity co-occurrence + specific tags)"

    if not articles:
        return {
            "report_date": report_date.isoformat(),
            "stories": [],
            "total_stories": 0,
            "method": method,
        }

    # 1. 抽取每篇文章特征
    feats = []
    for a in articles:
        text = " ".join(filter(None, [
            a.title or "", a.summary or "", " ".join(a.tags or []),
        ]))
        feats.append({
            "ents": _extract_entities(text),
            "spec": set(a.tags or []) - _GENERIC_TAGS,
            "toks": _title_tokens(a.title or ""),
            "art": a,
        })

    n = len(articles)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # 2. 建边：实体共现（强）优先；具体标签 + 标题实义词重叠（中）次之
    for i in range(n):
        for j in range(i + 1, n):
            fi, fj = feats[i], feats[j]
            if fi["ents"] & fj["ents"]:
                union(i, j)
                continue
            if (fi["spec"] & fj["spec"]) and (fi["toks"] & fj["toks"]):
                union(i, j)
                continue

    # 3. 收集连通分量
    comps: dict = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(i)

    # 4. 组装主线（超大连通分量按实体子图拆分）
    stories = []
    for idxs in comps.values():
        if len(idxs) > _MAX_STORY_ARTICLES:
            for sub in _split_by_entities(idxs, feats):
                stories.append(_build_story(sub, feats, report_date))
        else:
            stories.append(_build_story(idxs, feats, report_date))

    # 5. 排序：热度优先，其余确定性兜底
    stories.sort(key=_story_sort_key)
    return {
        "report_date": report_date.isoformat(),
        "stories": stories,
        "total_stories": len(stories),
        "method": method,
    }
