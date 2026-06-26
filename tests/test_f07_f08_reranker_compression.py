"""
F-07 / F-08 单元测试：Re-ranker（重排序）和 Context Compression（上下文压缩）

- F-07 Re-ranker: 使用 RerankerService（Cross-encoder 精排，降级为轻量评分）
- F-08 Context Compression: 纯函数，从检索结果中提取与查询相关的句子

不依赖数据库、外部 API，仅依赖 sentence-transformers（模型懒加载）
"""

import copy
import pytest

from api.services.reranker import RerankerService, RerankerConfig
from api.services.compression import CompressionService


# ═══════════════════════════════════════════════════════════════════
# 测试数据
# ═══════════════════════════════════════════════════════════════════

SAMPLE_CHUNKS = [
    {
        "chunk": {
            "id": "chunk-001",
            "content": (
                "大语言模型（LLM）是指使用海量文本数据训练的大型神经网络模型。"
                "这类模型通常拥有数十亿到数千亿个参数，能够理解并生成自然语言。"
                "代表性模型包括 GPT-4、Claude、Gemini 等。"
            ),
            "document_id": "doc-001",
        },
        "document": {"id": "doc-001", "name": "LLM 入门", "file_type": "markdown"},
        "score": 85.0,
        "fused_score": 0.85,
    },
    {
        "chunk": {
            "id": "chunk-002",
            "content": (
                "Transformer 架构是当前大语言模型的基础架构。"
                "它由编码器和解码器组成，通过自注意力机制捕获序列中不同位置间的依赖关系。"
                "2017 年由 Vaswani 等人在《Attention Is All You Need》论文中提出。"
            ),
            "document_id": "doc-001",
        },
        "document": {"id": "doc-001", "name": "LLM 入门", "file_type": "markdown"},
        "score": 72.0,
        "fused_score": 0.72,
    },
    {
        "chunk": {
            "id": "chunk-003",
            "content": (
                "微调（Fine-tuning）是在预训练模型基础上，使用特定领域的数据进一步训练，"
                "使模型适应特定任务的技术。常用的微调方法包括全参数微调和 LoRA 等参数高效微调方法。"
            ),
            "document_id": "doc-002",
        },
        "document": {"id": "doc-002", "name": "模型训练指南", "file_type": "markdown"},
        "score": 68.0,
        "fused_score": 0.68,
    },
    {
        "chunk": {
            "id": "chunk-004",
            "content": (
                "RAG（Retrieval-Augmented Generation）是一种将检索与生成相结合的架构。"
                "它先从知识库中检索相关文档片段，再将检索结果作为上下文注入到大语言模型中，"
                "从而生成更准确、更可靠的回答。"
            ),
            "document_id": "doc-003",
        },
        "document": {"id": "doc-003", "name": "RAG 系统设计", "file_type": "markdown"},
        "score": 45.0,
        "fused_score": 0.45,
    },
    {
        "chunk": {
            "id": "chunk-005",
            "content": (
                "Python 是一种广泛使用的高级编程语言，以其简洁易读的语法著称。"
                "它支持多种编程范式，包括面向对象、函数式和过程式编程。"
            ),
            "document_id": "doc-004",
        },
        "document": {"id": "doc-004", "name": "Python 教程", "file_type": "markdown"},
        "score": 12.0,
        "fused_score": 0.12,
    },
]

SAMPLE_QUERY = "大语言模型的工作原理是什么"


class TestContextCompression:
    """F-08 Context Compression 单元测试"""

    @pytest.mark.asyncio
    async def test_empty_chunks(self, compressor):
        """边界：空 chunks 应返回空字符串"""
        result = await compressor.compress(SAMPLE_QUERY, [])
        assert result == ""

    @pytest.mark.asyncio
    async def test_empty_query(self, compressor):
        """边界：空 query 应截取前 max_chars 字符"""
        result = await compressor.compress("", SAMPLE_CHUNKS, max_chars=50)
        assert len(result) <= 50
        assert result

    @pytest.mark.asyncio
    async def test_max_chars_zero(self, compressor):
        """边界：max_chars=0 应返回空字符串"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=0)
        assert result == ""

    @pytest.mark.asyncio
    async def test_max_chars_negative(self, compressor):
        """边界：max_chars 为负数应返回空字符串"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=-100)
        assert result == ""

    @pytest.mark.asyncio
    async def test_output_length_bound(self, compressor):
        """契约：输出长度 ≤ max_chars"""
        for max_c in [100, 200, 500, 1000]:
            result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=max_c)
            assert len(result) <= max_c, \
                f"输出长度 {len(result)} 超过 max_chars={max_c}"

    @pytest.mark.asyncio
    async def test_compression_ratio(self, compressor):
        """契约：压缩比应 ≥ 0.40（减少 40% 以上）"""
        raw = "".join(c["chunk"]["content"] for c in SAMPLE_CHUNKS)
        max_chars = int(len(raw) * 0.5)
        compressed = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=max_chars)
        ratio = 1 - len(compressed) / len(raw)
        assert ratio >= 0.40, \
            f"压缩比 {ratio:.2%} 不足 40%（原始 {len(raw)} → 压缩 {len(compressed)}）"

    @pytest.mark.asyncio
    async def test_truncate_mode_fallback(self, compressor):
        """异常：truncate 模式应简单截断"""
        raw = "".join(c["chunk"]["content"] for c in SAMPLE_CHUNKS)
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=50, mode="truncate")
        assert result == raw[:50]

    @pytest.mark.asyncio
    async def test_extract_mode_keeps_relevant(self, compressor):
        """正常：extract 模式应保留与查询相关的内容"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=500)
        assert any(kw in result for kw in ["大语言模型", "LLM", "神经网络"]), \
            f"压缩结果应包含与查询相关的关键词\n结果: {result}"

    @pytest.mark.asyncio
    async def test_single_chunk_no_compression_needed(self, compressor):
        """边界：单个短切片无需压缩"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS[:1], max_chars=9999)
        raw = SAMPLE_CHUNKS[0]["chunk"]["content"]
        assert result == raw

    @pytest.mark.asyncio
    async def test_compress_very_small_max_chars(self, compressor):
        """边界：极小的 max_chars 应能返回至少一些内容"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=10)
        assert len(result) <= 10
        assert len(result) > 0, "即使 max_chars=10 也应返回非空结果"

    @pytest.mark.asyncio
    async def test_summarize_mode_fallback(self, compressor):
        """异常：summarize 模式（无 API Key）应降级到 extract 级别"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=300, mode="summarize")
        assert len(result) <= 300
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_chunks_order_independence(self, compressor):
        """契约：压缩结果质量不应过度依赖输入顺序"""
        reversed_chunks = list(reversed(SAMPLE_CHUNKS))
        result_normal = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=300)
        result_reversed = await compressor.compress(SAMPLE_QUERY, reversed_chunks, max_chars=300)
        for kw in ["大语言模型", "LLM"]:
            assert kw in result_normal or kw in result_reversed

    @pytest.mark.asyncio
    async def test_preserve_critical_terms(self, compressor):
        """正常：压缩结果应保留关键术语"""
        result = await compressor.compress(SAMPLE_QUERY, SAMPLE_CHUNKS, max_chars=300)
        assert "大语言模型" in result, f"关键术语应被保留\n结果: {result}"


# ═══════════════════════════════════════════════════════════════════
# 集成场景测试
# ═══════════════════════════════════════════════════════════════════

class TestRerankerAndCompression:
    """F-07 + F-08 集成场景测试"""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, reranker, compressor):
        """模拟完整的 RAG 检索后处理流程"""
        reranked = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=5)
        assert len(reranked) >= 1
        for item in reranked:
            assert "re_score" in item
            assert 0.0 <= item["re_score"] <= 1.0

        compressed = await compressor.compress(SAMPLE_QUERY, reranked, max_chars=600)
        assert len(compressed) <= 600
        assert len(compressed) > 0
        assert any(phrase in compressed for phrase in ["大语言模型", "LLM"]), \
            "流水线处理后应保留核心信息"

    @pytest.mark.asyncio
    async def test_pipeline_with_empty_intermediate(self, reranker, compressor):
        """边界：流水线中间步骤返回空结果"""
        reranked = await reranker.rerank(SAMPLE_QUERY, [], top_k=5)
        assert reranked == []
        compressed = await compressor.compress(SAMPLE_QUERY, reranked, max_chars=500)
        assert compressed == ""

    @pytest.mark.asyncio
    async def test_pipeline_compression_reduces_token_count(self, reranker, compressor):
        """性能：压缩应显著减少送入 LLM 的 token 数量"""
        reranked = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=3)
        raw = "".join(c["chunk"]["content"] for c in reranked)
        target_len = int(len(raw) * 0.5)
        compressed = await compressor.compress(SAMPLE_QUERY, reranked, max_chars=target_len)
        reduction = 1 - len(compressed) / len(raw)
        assert reduction >= 0.40, \
            f"压缩减少量 {reduction:.1%} 不足 40%"


@pytest.fixture
def reranker():
    """返回使用 fallback 模式的 RerankerService（不加载 Cross-encoder 模型）"""
    config = RerankerConfig(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        timeout=2.0,
        batch_size=8,
        top_k=5,
        device="cpu",
        force_fallback=True,
    )
    service = RerankerService(config)
    return service


@pytest.fixture
def compressor():
    """返回 CompressionService 实例（使用默认配置）"""
    return CompressionService()


# ═══════════════════════════════════════════════════════════════════
# F-07: Re-ranker 测试
# ═══════════════════════════════════════════════════════════════════

class TestReranker:
    """F-07 Re-ranker 单元测试"""

    @pytest.mark.asyncio
    async def test_empty_chunks(self, reranker):
        """边界：空列表应返回空列表"""
        result = await reranker.rerank(SAMPLE_QUERY, [], top_k=5)
        assert result == [], f"空列表应返回 [], 实际得到 {result}"

    @pytest.mark.asyncio
    async def test_single_chunk(self, reranker):
        """边界：单一切片应直接返回（无需排序）"""
        single = [SAMPLE_CHUNKS[0]]
        result = await reranker.rerank(SAMPLE_QUERY, single, top_k=5)
        assert len(result) == 1
        assert result[0]["chunk"]["id"] == "chunk-001"
        assert "re_score" in result[0], "单一切片也应增加 re_score 字段"

    @pytest.mark.asyncio
    async def test_rerank_order(self, reranker):
        """正常流程：重排序后最相关的文档应排在前面"""
        result = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=5)
        assert len(result) <= 5
        for item in result:
            assert "re_score" in item, f"结果缺少 re_score: {item['chunk']['id']}"
            assert 0.0 <= item["re_score"] <= 1.0, \
                f"re_score 超出范围 [0,1]: {item['re_score']}"
        scores = [item["re_score"] for item in result]
        assert scores == sorted(scores, reverse=True), \
            f"re_score 应降序排列: {scores}"

    @pytest.mark.asyncio
    async def test_top_k_limit(self, reranker):
        """边界：top_k 限制应生效"""
        result = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=3)
        assert len(result) <= 3, f"top_k=3 应返回 ≤3 个结果, 实际 {len(result)}"

    @pytest.mark.asyncio
    async def test_top_k_larger_than_input(self, reranker):
        """边界：top_k 大于输入列表长度"""
        result = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=999)
        assert len(result) <= len(SAMPLE_CHUNKS)

    @pytest.mark.asyncio
    async def test_top_k_zero(self, reranker):
        """边界：top_k=0 应返回空列表"""
        result = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=0)
        assert result == []

    @pytest.mark.asyncio
    async def test_all_same_scores(self, reranker):
        """边界：所有切片分数相同时，排序稳定"""
        same_score_chunks = []
        for i, item in enumerate(SAMPLE_CHUNKS):
            item_copy = copy.deepcopy(item)
            item_copy["fused_score"] = 0.5
            item_copy["chunk"]["id"] = f"same-{i:03d}"
            same_score_chunks.append(item_copy)
        result = await reranker.rerank(SAMPLE_QUERY, same_score_chunks, top_k=5)
        assert len(result) == 5
        # 即使 fused_score 相同，re_score 也应反映真实相关性差异
        assert result[0]["re_score"] >= result[-1]["re_score"]

    @pytest.mark.asyncio
    async def test_re_score_range(self, reranker):
        """契约：re_score 必须在 [0.0, 1.0] 范围内"""
        result = await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=10)
        for item in result:
            assert 0.0 <= item["re_score"] <= 1.0, \
                f"chunk {item['chunk']['id']} 的 re_score={item['re_score']} 超出 [0,1]"

    @pytest.mark.asyncio
    async def test_no_side_effects(self, reranker):
        """契约：函数不应修改原始输入数据"""
        original = copy.deepcopy(SAMPLE_CHUNKS)
        await reranker.rerank(SAMPLE_QUERY, SAMPLE_CHUNKS, top_k=5)
        for orig, curr in zip(original, SAMPLE_CHUNKS):
            assert orig["chunk"]["id"] == curr["chunk"]["id"]
            assert orig["chunk"]["content"] == curr["chunk"]["content"]

