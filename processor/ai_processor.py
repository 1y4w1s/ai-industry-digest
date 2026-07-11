"""
Signal - AI 处理器
调用 DeepSeek API 实现：摘要生成、标签分类、重要性判断
支持批处理优化
"""

import json
import os
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

from collector.base import Article

load_dotenv()


@dataclass
class AIResult:
    """AI 处理结果"""
    summary: str
    tags: List[str]
    importance: str          # high / medium / low
    reason: str
    so_what: Optional[str] = None   # 观点层：So What / 对你意味着什么（独立步骤产出，可空）
    article_index: int = 0   # 批处理中的文章序号


class AIProcessor:
    """DeepSeek AI 处理器"""

    # 标签候选列表（限制 AI 的输出范围，提高一致性）
    TAG_CANDIDATES = [
        "技术突破", "产品发布", "融资", "政策法规",
        "人物变动", "观点评论", "开源项目", "学术论文",
        "行业趋势", "安全", "其他"
    ]

    # 重要性判断标准（作为 Prompt 的一部分）
    IMPORTANCE_GUIDE = """
    - high: 头部公司重大动作、技术里程碑、影响行业格局的事件
    - medium: 常规产品更新、普通融资、行业常规动态
    - low: 边缘信息、重复性内容、非核心技术新闻
    """

    def __init__(self, batch_size: int = 10):
        """
        Args:
            batch_size: 每批处理的文章数（默认 10）
        """
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "请设置环境变量 DEEPSEEK_API_KEY\n"
                "在 .env 文件中添加: DEEPSEEK_API_KEY=your-key"
            )

        self.batch_size = batch_size
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"  # DeepSeek-V4 模型

    # ── 公开调用方法 ──────────────────────────────────

    def process_articles(self, articles: List[Article]) -> List[Article]:
        """批量处理文章（主入口）
        自动分批调用，每批 batch_size 篇
        """
        total = len(articles)
        if total == 0:
            return articles

        print(f"\n🤖 AI 处理: 共 {total} 篇文章，每批 {self.batch_size} 篇")
        print(f"   预估调用次数: {(total + self.batch_size - 1) // self.batch_size} 次")

        processed = 0
        failed = 0

        for start_idx in range(0, total, self.batch_size):
            batch = articles[start_idx:start_idx + self.batch_size]
            batch_num = start_idx // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size

            print(f"\n  批次 {batch_num}/{total_batches} ({len(batch)} 篇)...")
            results = self._process_batch(batch)

            if results is None:
                print(f"  [ERROR] 批次 {batch_num} 处理失败，跳过")
                failed += len(batch)
                continue

            # 观点层（So What）独立步骤：与 summary 解耦，避免污染事实字段
            so_whats = self._generate_so_what(batch)

            # 将结果写回 Article 对象
            for article, result, so_what in zip(batch, results, so_whats):
                if result:
                    article.summary = result.summary
                    article.tags = [t for t in result.tags if t in self.TAG_CANDIDATES or t.startswith("其他")]
                    article.importance = result.importance
                    article.importance_reason = result.reason
                    article.so_what = so_what  # 可空：LLM 失败时为 None，旧文兼容
                    processed += 1
                else:
                    failed += 1

            # 批次间短暂停顿，避免触发限流
            if batch_num < total_batches:
                time.sleep(1)

        print(f"\n📊 AI 处理完成: 成功 {processed} 篇, 失败 {failed} 篇")
        return articles

    # ── 内部批处理 ──────────────────────────────────

    def _process_batch(self, articles: List[Article]) -> Optional[List[Optional[AIResult]]]:
        """处理一批文章"""
        prompt = self._build_batch_prompt(articles)
        response = self._call_api(prompt)

        if response is None:
            return None

        return self._parse_batch_response(response, len(articles))

    def _build_batch_prompt(self, articles: List[Article]) -> str:
        """构建批处理 Prompt"""
        articles_text = ""
        for i, article in enumerate(articles, 1):
            content = article.raw_content[:800]  # 单篇限制 800 字（从1500减少）
            articles_text += f"""
--- 文章 {i} ---
标题: {article.title}
来源: {article.source_name}
内容: {content}

"""

        prompt = f"""你是一个 AI 行业分析师。请分析以下 {len(articles)} 篇 AI 行业新闻，为每篇生成摘要、标签和重要性判断。

{articles_text}
请严格按照以下 JSON 数组格式输出，不要包含其他文字：
[
  {{
    "article_index": 1,
    "summary": "不超过 150 字的中文摘要，保留关键信息，只说事实",
    "tags": ["标签1", "标签2"],
    "importance": "high/medium/low",
    "reason": "一句话解释重要性判断理由"
  }},
  ...
]

标签只能从以下选择：{", ".join(self.TAG_CANDIDATES)}

重要性判断标准：
{self.IMPORTANCE_GUIDE}

注意：
1. 输出的 JSON 数组长度必须等于 {len(articles)}
2. 每篇文章的 article_index 从 1 开始
3. 如果某篇文章内容不足以分析，tags 设为 ["其他"]，importance 设为 "low"
"""
        return prompt

    def _parse_batch_response(self, response: dict, expected_count: int) -> List[Optional[AIResult]]:
        """解析 API 返回的 JSON 结果"""
        try:
            content = response["choices"][0]["message"]["content"]
            # 清理可能的 markdown 代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)

            if not isinstance(data, list):
                print(f"  [WARN] API 返回非数组，尝试提取数组")
                return [None] * expected_count

            results = []
            for item in data:
                results.append(AIResult(
                    summary=item.get("summary", ""),
                    tags=item.get("tags", []),
                    importance=item.get("importance", "low"),
                    reason=item.get("reason", ""),
                    article_index=item.get("article_index", 0)
                ))

            # 补足缺失的结果
            while len(results) < expected_count:
                results.append(None)

            return results[:expected_count]

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"  [ERROR] 解析 AI 响应失败: {e}")
            print(f"  [DEBUG] 原始响应: {response.get('choices', [{}])[0].get('message', {}).get('content', '')[:200]}")
            return [None] * expected_count

    # ── 观点层（So What）独立步骤 ────────────────
    # 与 summary 完全解耦：事实底由 _process_batch 产出，观点层单独调用 LLM，
    # 即使观点生成失败也绝不回填到 summary，避免污染事实字段。

    # 标题党 / 夸张词汇黑名单（用于 prompt 约束 + 测试可复用的判定）
    CLICKBAIT_WORDS = [
        "核弹级", "炸裂", "颠覆", "史诗级", "逆天", "封神", "王炸", "炸场",
        "惊呆", "震惊", "狂飙", "杀疯了", "绝绝子", "炸天", "逆天改命",
        "史上最", "吊打", "完爆", "一雪前耻", "原地封神",
    ]

    def _generate_so_what(self, articles: List[Article]) -> List[Optional[str]]:
        """为一批文章生成「So What / 对你意味着什么」观点层。

        返回与 articles 等长的列表，逐篇对齐；任意一篇失败则该篇为 None。
        观点基于已生成的事实底（title/summary/source），不接触原始摘要字段。
        """
        if not articles:
            return []

        prompt = self._build_so_what_prompt(articles)
        # 观点层用稍高温度更自然，但限制重试与 token 以控成本
        response = self._call_api(prompt, max_retries=1, temperature=0.5, max_tokens=1024)
        if response is None:
            print(f"  [WARN] So What 观点层生成失败（{len(articles)} 篇置空，不影响事实底）")
            return [None] * len(articles)

        return self._parse_so_what_response(response, len(articles))

    def _build_so_what_prompt(self, articles: List[Article]) -> str:
        """构建观点层 Prompt（独立于事实层）"""
        items_text = ""
        for i, article in enumerate(articles, 1):
            # 观点必须基于事实底：优先用已生成的 summary，缺失时退回原文片段
            base = article.summary or article.raw_content[:400]
            items_text += f"""
--- 文章 {i} ---
标题: {article.title}
来源: {article.source_name}
事实底（已核实摘要）: {base}
"""

        banned = "、".join(self.CLICKBAIT_WORDS)
        prompt = f"""你是一个有经验的 AI 行业编辑，负责写「So What / 对你意味着什么」观点层。

为下面 {len(articles)} 篇文章各写一句「So What」——用大白话告诉关注 AI 的读者：这条新闻**对你（或你所在行业）实际意味着什么**，有什么值得留意、能用上、或要警惕的点。

下面是各篇文章的「事实底」（已核实，请仅据此生发观点，不要编造）：
{items_text}
要求：
1. 像编辑对读者说的"人话"，口语自然，不要新闻稿腔、不要说教。
2. 严格 1-2 句，中文，不超过 60 字。
3. 必须基于上面的「事实底」，不编造文章里没有的信息；不输出主观立场或情绪煽动。
4. **绝对禁止**标题党 / 夸张词汇，例如：{banned}。
5. 不要简单重复标题本身，要往前走一步点出"所以呢"。
6. 若内容实在无法判断实际意义，写一句平实的"这条信息的实际影响暂不明确"。

请严格按以下 JSON 数组格式输出（长度必须等于 {len(articles)}，article_index 从 1 开始，不要包含其他文字）：
[
  {{"article_index": 1, "so_what": "..."}},
  ...
]
"""
        return prompt

    def _parse_so_what_response(self, response: dict, expected_count: int) -> List[Optional[str]]:
        """解析观点层 API 返回的 JSON 结果（容错：解析失败整批置空）"""
        try:
            content = response["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
            if not isinstance(data, list):
                print(f"  [WARN] So What 返回非数组，整批置空")
                return [None] * expected_count

            so_whats = []
            for item in data:
                sw = item.get("so_what")
                so_whats.append(sw if isinstance(sw, str) and sw.strip() else None)

            # 补足缺失的结果
            while len(so_whats) < expected_count:
                so_whats.append(None)

            return so_whats[:expected_count]

        except (json.JSONDecodeError, KeyError, TypeError, IndexError) as e:
            print(f"  [ERROR] 解析 So What 响应失败: {e}")
            return [None] * expected_count

    # ── API 调用 ──────────────────────────────────

    def _call_api(self, prompt: str, max_retries: int = 2,
                  temperature: float = 0.3, max_tokens: int = 2048) -> Optional[dict]:
        """调用 DeepSeek API，带重试机制

        Args:
            temperature: 采样温度（事实层用 0.3 保一致；观点层可略高更自然）
            max_tokens: 输出上限
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的 AI 行业分析师，擅长信息摘要和分析。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,   # 低温度，保证输出一致性
            "max_tokens": max_tokens     # 减少输出限制（从4096减少）
        }

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait = 2 ** attempt  # 指数退避: 2s, 4s
                    print(f"  [RETRY] 第 {attempt} 次重试，等待 {wait}s...")
                    time.sleep(wait)

                with httpx.Client(timeout=120) as client:
                    resp = client.post(self.base_url, headers=headers, json=payload)
                    resp.raise_for_status()
                    return resp.json()

            except httpx.TimeoutException as e:
                last_error = f"超时: {e}"
                print(f"  [WARN] API 请求超时 (尝试 {attempt + 1}/{max_retries + 1})")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}"
                if e.response.status_code == 401:
                    print(f"  [ERROR] API 密钥无效，请检查 DEEPSEEK_API_KEY")
                    return None
                elif e.response.status_code == 429:
                    print(f"  [WARN] 触发限流 (尝试 {attempt + 1}/{max_retries + 1})")
                else:
                    print(f"  [WARN] API 返回错误 {e.response.status_code}: {e.response.text[:200]}")
                    if attempt == max_retries:
                        return None
            except Exception as e:
                last_error = str(e)
                print(f"  [WARN] API 请求异常: {e}")
                if attempt == max_retries:
                    return None

        print(f"  [ERROR] API 请求最终失败: {last_error}")
        return None

    # ── 单篇文章处理（备选，用于 AI 辅助去重） ──────────

    def judge_duplicate(self, title_a: str, title_b: str) -> bool:
        """判断两篇文章是否描述同一事件（用于去重第三层）"""
        prompt = f"""判断以下两个新闻标题是否描述同一事件。
标题A: {title_a}
标题B: {title_b}

只输出 "yes" 或 "no"："""

        response = self._call_api(prompt, max_retries=1)
        if response is None:
            return False  # 判断失败时保守处理，不合并

        try:
            content = response["choices"][0]["message"]["content"].strip().lower()
            return content.startswith("yes")
        except (KeyError, IndexError):
            return False

    def generate_summary_insight(self, articles: List[Article]) -> str:
        """生成今日概览（一段话总结）"""
        # 取重要文章作为概览依据
        top_articles = [
            a for a in articles if a.importance == "high"
        ][:5]
        if not top_articles:
            top_articles = articles[:5]

        articles_summary = "\n".join([
            f"- [{a.importance}] {a.title}: {a.summary[:100] if a.summary else '(无摘要)'}"
            for a in top_articles
        ])

        prompt = f"""以下是今天最重要的 {len(top_articles)} 篇 AI 行业新闻。请写一段 150 字以内的"今日概览"，总结今天最值得关注的趋势。

{articles_summary}

今日概览："""

        response = self._call_api(prompt)
        if response is None:
            return "今日概览生成失败。"

        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            return "今日概览生成失败。"
