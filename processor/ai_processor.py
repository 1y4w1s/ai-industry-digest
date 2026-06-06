"""
Signal - AI 处理器
调用 DeepSeek API 实现：摘要生成、标签分类、重要性判断
支持批处理优化
"""

import asyncio
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

            # 将结果写回 Article 对象
            for article, result in zip(batch, results):
                if result:
                    article.summary = result.summary
                    article.tags = [t for t in result.tags if t in self.TAG_CANDIDATES or t.startswith("其他")]
                    article.importance = result.importance
                    article.importance_reason = result.reason
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
            content = article.raw_content[:1500]  # 单篇限制 1500 字
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

    # ── API 调用 ──────────────────────────────────

    def _call_api(self, prompt: str, max_retries: int = 2) -> Optional[dict]:
        """调用 DeepSeek API，带重试机制"""
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
            "temperature": 0.3,   # 低温度，保证输出一致性
            "max_tokens": 4096     # 足够容纳批处理结果
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

    # ── 知识抽取（用于知识库） ──────────────────────────

    async def extract_knowledge(self, content: str) -> tuple:
        """从文本中提取实体和关系（知识图谱构建）
        
        Returns:
            (entities, relations): 实体列表和关系列表
        """
        # 实体识别
        entities = await self._extract_entities(content)
        
        # 关系抽取（如果有实体）
        relations = []
        if entities:
            relations = await self._extract_relations(content, entities)
        
        return entities, relations

    async def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """使用 DeepSeek API 进行实体识别（NER）"""
        prompt = f"""从以下文本中识别出实体，并进行分类。

文本：
{content[:3000]}  # 限制长度

实体类型及示例：
- concept: 概念（如：大语言模型、机器学习、人工智能）
- technology: 技术（如：Transformer、GPT、RAG）
- person: 人名（如：Sam Altman、吴恩达）
- organization: 机构（如：OpenAI、Google、阿里巴巴）
- product: 产品（如：GPT-4、Claude、文心一言）

请以 JSON 数组格式输出，不要包含其他文字：
[
  {{"name": "实体名", "type": "类型"}},
  ...
]

只返回 JSON，不要其他内容。"""

        response = await self._call_api_async(prompt)
        if response is None:
            return []

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
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, KeyError, IndexError):
            return []

    async def _extract_relations(self, content: str, entities: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """使用 DeepSeek API 进行关系抽取（RE）"""
        entity_names = [e["name"] for e in entities]
        
        prompt = f"""从以下文本中抽取实体之间的关系。

文本：
{content[:3000]}

已识别实体：
{", ".join(entity_names)}

关系类型及说明：
- is_a: A 是一种 B（如：GPT-4 is_a 大语言模型）
- part_of: A 是 B 的一部分
- based_on: A 基于 B（如：GPT 基于 Transformer）
- related_to: A 与 B 相关
- author_of: A 是 B 的作者
- published_by: A 由 B 发布
- developed_by: A 由 B 开发

请以 JSON 数组格式输出，不要包含其他文字：
[
  {{"source": "实体A", "target": "实体B", "relation": "关系类型", "label": "中文标签"}},
  ...
]

只返回 JSON，不要其他内容。"""

        response = await self._call_api_async(prompt)
        if response is None:
            return []

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
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, KeyError, IndexError):
            return []

    async def _call_api_async(self, prompt: str, max_retries: int = 2) -> Optional[dict]:
        """异步调用 DeepSeek API，带重试机制"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的知识图谱构建助手，擅长实体识别和关系抽取。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        }

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)

                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(self.base_url, headers=headers, json=payload)
                    resp.raise_for_status()
                    return resp.json()

            except httpx.TimeoutException as e:
                last_error = f"超时: {e}"
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}"
                if e.response.status_code == 401:
                    return None
            except Exception as e:
                last_error = str(e)

        return None
