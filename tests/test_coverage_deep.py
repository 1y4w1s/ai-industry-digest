"""
深度覆盖测试：补齐 retrieval/graph_retrieval/reranker 的剩余路径

策略：
  - 在模块级 mock supabase，避免模块级 get_db() 触发真实连接
  - 所有数据库查询返回 mock 数据
  - 测试 search() 全流程
"""

import os
import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

# ── 先 mock supabase 再 import ──
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key-12345")
sys.modules["supabase"] = MagicMock()
sys.modules["supabase._sync"] = MagicMock()
sys.modules["supabase._sync.client"] = MagicMock()
sys.modules["supabase._sync.client.SupabaseException"] = Exception

from api.services.retrieval import AdvancedRetrievalService
from api.services.graph_retrieval import GraphRetrievalService
from api.services.reranker import RerankerService, RerankerConfig
from api.services.compression import CompressionService
from api.models.database import DatabaseManager


# ============================================================
# Helpers
# ============================================================

def make_mock_db():
    """构造一个 mock DatabaseManager"""
    db = MagicMock(spec=DatabaseManager)
    db.client = MagicMock()
    return db


def mock_table_query(db, return_data=None, return_count=0):
    """设置 db.client.table() 的链式调用统一返回 mock 数据"""
    chain = MagicMock()
    chain.execute.return_value.data = return_data or []
    chain.execute.return_value.count = return_count
    chain.eq.return_value = chain
    chain.or_.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.in_.return_value = chain
    chain.gte.return_value = chain
    chain.contains.return_value = chain
    chain.ilike.return_value = chain
    chain.select.return_value = chain

    table_mock = MagicMock()
    table_mock.select.return_value = chain
    table_mock.insert.return_value = chain
    table_mock.update.return_value = chain
    table_mock.delete.return_value = chain
    db.client.table.return_value = table_mock
    return table_mock


class _MockSelectChain:
    """可针对不同 table 返回不同 execute 结果的 mock chain"""

    def __init__(self, data_map=None, eq=True, order=True):
        self._data_map = data_map or {}
        self._chain = MagicMock()
        self._chain.execute.return_value.data = []
        self._chain.execute.return_value.count = 0
        self._chain.eq.return_value = self._chain
        self._chain.or_.return_value = self._chain
        self._chain.order.return_value = self._chain
        self._chain.limit.return_value = self._chain
        self._chain.in_.return_value = self._chain
        self._chain.gte.return_value = self._chain
        self._chain.ilike.return_value = self._chain
        self._chain.select.return_value = self._chain

    def for_table(self, table_name):
        if table_name in self._data_map:
            data, count = self._data_map[table_name]
            self._chain.execute.return_value.data = data
            self._chain.execute.return_value.count = count
        return self._chain


def make_graph_db(entities=None, chunks=None):
    """构造按 table 名返回不同数据的 DB mock"""
    entities = entities or []
    chunks = chunks or []
    db = make_mock_db()

    def make_chain(data):
        chain = MagicMock()
        chain.execute.return_value.data = data
        chain.execute.return_value.count = len(data)
        chain.eq.return_value = chain
        chain.or_.return_value = chain
        chain.order.return_value = chain
        chain.limit.return_value = chain
        chain.in_.return_value = chain
        chain.gte.return_value = chain
        chain.contains.return_value = chain
        chain.ilike.return_value = chain
        chain.select.return_value = chain
        return chain

    def select_table(name):
        tbl = MagicMock()
        if name == "kb_entities":
            tbl.select.return_value = make_chain(entities)
        elif name == "kb_chunks":
            tbl.select.return_value = make_chain(chunks)
        else:
            tbl.select.return_value = make_chain([])
        return tbl

    db.client.table.side_effect = select_table
    return db


def make_retrieval_svc():
    """构造 AdvancedRetrievalService，mock embedding_service 避免真实连接"""
    with patch("api.services.retrieval.get_embedding_service") as m:
        fake_emb = MagicMock()
        fake_emb.get_embedding = AsyncMock(return_value=[0.1] * 1024)
        m.return_value = fake_emb
        svc = AdvancedRetrievalService()
        svc.embedding_service = fake_emb
        return svc


# ============================================================
# Part A: retrieval.py — search() 全流程
# ============================================================

class TestSearchFullFlow:
    """search() 全路径测试（mock 所有外部依赖）"""

    @staticmethod
    def make_recommend_strategy():
        s = MagicMock()
        s.intent_label = "推荐类"
        s.intent.name = "RECOMMEND"
        s.use_rewrite = False
        s.use_hybrid = False
        s.use_reranker = False
        s.limit_multiplier = 1.0
        return s

    @pytest.mark.asyncio
    async def test_recommend_mode_returns_results(self):
        """推荐模式：查询到数据时返回"""
        svc = make_retrieval_svc()
        db = make_mock_db()
        mock_table_query(db, return_data=[
            {"id": "c1", "content": "test", "document_id": "d1",
             "is_public": True, "user_id": "u1", "name": "doc1", "file_type": "md"}
        ])

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_router_service") as mr:
                mr.return_value.route.return_value = self.make_recommend_strategy()
                results = await svc.search("推荐最新文章", "user-1", use_routing=True)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_recommend_mode_empty_returns_suggestions(self):
        """推荐模式：无数据时返回建议"""
        svc = make_retrieval_svc()
        db = make_mock_db()
        mock_table_query(db, return_data=[])

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_router_service") as mr:
                mr.return_value.route.return_value = self.make_recommend_strategy()
                with patch("api.services.query_suggestion.get_query_suggestion_service") as ms:
                    ms.return_value.suggest.return_value = {
                        "correction": None, "correction_confidence": 0.0,
                        "topics": ["AI"], "related_queries": []
                    }
                    results = await svc.search("推荐最新", "user-1", use_routing=True)

        assert len(results) == 1
        assert results[0].get("_suggestions", {}).get("topics") == ["AI"]

    @pytest.mark.asyncio
    async def test_hybrid_mode_with_results(self):
        """混合检索：正常返回结果"""
        svc = make_retrieval_svc()

        db = make_mock_db()
        # 构造按 table 名区分 data 的 mock
        doc_chain = MagicMock()
        doc_chain.execute.return_value.data = [{"id": "d1"}]
        doc_chain.execute.return_value.count = 1
        doc_chain.eq.return_value = doc_chain
        doc_chain.order.return_value = doc_chain
        doc_chain.limit.return_value = doc_chain
        doc_chain.in_.return_value = doc_chain

        chunk_chain = MagicMock()
        chunk_chain.execute.return_value.data = [{
            "id": "c1", "content": "测试内容", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "doc1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }]
        chunk_chain.eq.return_value = chunk_chain
        chunk_chain.order.return_value = chunk_chain
        chunk_chain.limit.return_value = chunk_chain
        chunk_chain.in_.return_value = chunk_chain

        def sel(name):
            return doc_chain if name == "kb_documents" else chunk_chain

        tab = MagicMock()
        tab.select.side_effect = sel
        tab.insert = MagicMock()
        tab.update = MagicMock()
        tab.delete = MagicMock()
        db.client.table.return_value = tab

        rpc_mock = MagicMock()
        rpc_mock.execute.return_value.data = [{
            "id": "c1", "content": "测试内容", "document_id": "d1",
            "document_name": "doc1", "file_type": "md",
            "is_public": True, "doc_user_id": "user-1", "similarity": 0.85
        }]
        db.client.rpc = lambda n, p: rpc_mock

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_reranker_service") as mrr:
                mrr.return_value.rerank.return_value = [{
                    "chunk": {"id": "c1", "content": "测试内容", "document_id": "d1"},
                    "document": {"id": "d1", "name": "doc1", "file_type": "md"},
                    "score": 0.85, "fused_score": 0.85
                }]
                with patch("api.services.retrieval.get_graph_retrieval_service") as mg:
                    mg.return_value.graph_search.return_value = []
                    results = await svc.search("测试查询", "user-1",
                                               use_routing=False, use_hybrid=True,
                                               use_reranker=True)

        assert len(results) > 0
        assert results[0]["chunk"]["id"] == "c1"

    @pytest.mark.asyncio
    async def test_vector_only_mode(self):
        """仅向量检索模式"""
        svc = make_retrieval_svc()
        db = make_mock_db()

        rpc_mock = MagicMock()
        rpc_mock.execute.return_value.data = [{
            "id": "c1", "content": "test", "document_id": "d1",
            "document_name": "doc1", "file_type": "md",
            "is_public": True, "doc_user_id": "user-1", "similarity": 0.85
        }]
        db.client.rpc = lambda n, p: rpc_mock
        mock_table_query(db, return_data=[])

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_reranker_service") as mrr:
                mrr.return_value.rerank.return_value = [{
                    "chunk": {"id": "c1", "content": "test", "document_id": "d1"},
                    "document": {"id": "d1", "name": "doc1", "file_type": "md"},
                    "score": 0.85, "fused_score": 0.85
                }]
                results = await svc.search("test", "user-1",
                                           use_routing=False, use_hybrid=False,
                                           use_reranker=True)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_embedding_failure_fallback(self):
        """向量获取失败时 keyword search 仍工作"""
        svc = make_retrieval_svc()
        svc.embedding_service.get_embedding = AsyncMock(return_value=None)

        db = make_mock_db()
        mock_table_query(db, return_data=[{
            "id": "c1", "content": "test keyword", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "doc1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }])

        with patch("api.services.retrieval.db", db):
            with patch("api.services.retrieval.get_graph_retrieval_service") as mg:
                mg.return_value.graph_search.return_value = []
                results = await svc.search("keyword", "user-1",
                                           use_routing=False, use_hybrid=True,
                                           use_reranker=False)
        assert len(results) > 0


# ============================================================
# Part B: graph_retrieval.py — DB 方法
# ============================================================

class TestGraphFindMatchedEntities:
    """_find_matched_entities 测试"""
    TARGET = "api.services.graph_retrieval.GraphRetrievalService._db"

    def make_svc(self):
        return GraphRetrievalService.__new__(GraphRetrievalService)

    def test_matched_entities_found(self):
        """找到匹配的实体"""
        svc = self.make_svc()
        db = make_graph_db(entities=[{"id": "e1", "name": "OpenAI", "type": "company", "document_id": "d1"}])
        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc._find_matched_entities(["OpenAI"], "user-1")
        assert len(result) == 1
        assert result[0]["name"] == "OpenAI"

    def test_matched_entities_not_found(self):
        """没有匹配实体"""
        svc = self.make_svc()
        db = make_graph_db(entities=[])
        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc._find_matched_entities(["NoSuchEntity"], "user-1")
        assert result == []

    def test_deduplication(self):
        """重复实体名去重"""
        svc = self.make_svc()
        db = make_graph_db(entities=[{"id": "e1", "name": "OpenAI", "type": "company", "document_id": "d1"}])
        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc._find_matched_entities(["OpenAI", "OpenAI"], "user-1")
        assert len(result) == 1


class TestGraphFindChunksByEntities:
    """_find_chunks_by_entities 测试"""
    TARGET = "api.services.graph_retrieval.GraphRetrievalService._db"

    def make_svc(self):
        return GraphRetrievalService.__new__(GraphRetrievalService)

    def test_find_chunks_with_mock_data(self):
        """根据实体 ID 查找切片"""
        svc = self.make_svc()
        db = make_mock_db()

        # kb_entities → 返回 document_id
        entity_chain = MagicMock()
        entity_chain.execute.return_value.data = [{"document_id": "d1"}]
        entity_chain.execute.return_value.count = 1
        entity_chain.eq.return_value = entity_chain
        entity_chain.in_.return_value = entity_chain
        entity_chain.select.return_value = entity_chain
        entity_chain.limit.return_value = entity_chain
        entity_chain.order.return_value = entity_chain
        entity_chain.or_.return_value = entity_chain
        entity_chain.gte.return_value = entity_chain
        entity_chain.ilike.return_value = entity_chain

        # kb_chunks → 返回切片
        chunk_chain = MagicMock()
        chunk_chain.execute.return_value.data = [{
            "id": "c1", "content": "test content", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "doc1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }]
        chunk_chain.execute.return_value.count = 1
        chunk_chain.eq.return_value = chunk_chain
        chunk_chain.in_.return_value = chunk_chain
        chunk_chain.select.return_value = chunk_chain
        chunk_chain.limit.return_value = chunk_chain
        chunk_chain.order.return_value = chunk_chain
        chunk_chain.or_.return_value = chunk_chain
        chunk_chain.gte.return_value = chunk_chain
        chunk_chain.ilike.return_value = chunk_chain

        def get_tbl(name):
            t = MagicMock()
            if name == "kb_entities":
                t.select.return_value = entity_chain
            elif name == "kb_chunks":
                t.select.return_value = chunk_chain
            else:
                t.select.return_value = entity_chain
            return t

        db.client.table.side_effect = get_tbl

        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc._find_chunks_by_entities(["e1"], ["OpenAI"], "user-1", 5)
        assert len(result) > 0
        assert result[0]["chunk"]["id"] == "c1"

    def test_no_doc_ids_returns_empty(self):
        """没有文档 ID 返回空"""
        svc = self.make_svc()
        db = make_graph_db(entities=[])
        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc._find_chunks_by_entities([], ["test"], "user-1", 5)
        assert result == []


class TestGraphSearchFull:
    """graph_search 全流程测试"""
    TARGET = "api.services.graph_retrieval.GraphRetrievalService._db"

    def make_svc(self):
        return GraphRetrievalService.__new__(GraphRetrievalService)

    def test_graph_search_success(self):
        """图谱检索全流程"""
        svc = self.make_svc()

        entities = [
            {"id": "e1", "name": "OpenAI", "type": "company", "document_id": "d1"}
        ]
        chunks = [{
            "id": "c1", "content": "OpenAI 发布最新模型", "document_id": "d1",
            "kb_documents": {"id": "d1", "name": "doc1", "file_type": "md",
                             "is_public": True, "user_id": "user-1"}
        }]
        db = make_graph_db(entities=entities, chunks=chunks)

        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc.graph_search("OpenAI的投资方是谁", "user-1", limit=5)
        assert len(result) > 0
        assert "graph_info" in result[0]

    def test_graph_search_no_entities(self):
        """查询中没有可提取的实体"""
        svc = self.make_svc()
        db = make_graph_db()
        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc.graph_search("你好", "user-1")
        assert result == []

    def test_graph_search_no_matched_entities(self):
        """实体未在数据库中找到"""
        svc = self.make_svc()
        db = make_graph_db(entities=[])
        with patch(self.TARGET, new_callable=PropertyMock, return_value=db):
            result = svc.graph_search("OpenAI 模型", "user-1")
        assert result == []


# ============================================================
# Part C: reranker.py — 模型加载 + 超时降级
# ============================================================

class TestRerankerModelPaths:
    """reranker 模型加载路径测试"""

    def test_force_fallback_skips_model(self):
        """force_fallback 跳过模型加载"""
        svc = RerankerService(RerankerConfig(force_fallback=True))
        assert not svc._load_model()

    def test_load_model_success(self):
        """模型加载成功"""
        svc = RerankerService(RerankerConfig(force_fallback=False))
        with patch("sentence_transformers.CrossEncoder"):
            svc._load_model()
            assert svc._model_loaded is True

    def test_load_model_failure(self):
        """模型加载失败，_load_error 被设置"""
        svc = RerankerService(RerankerConfig(force_fallback=False))
        with patch("sentence_transformers.CrossEncoder", side_effect=Exception("Download failed")):
            svc._load_model()
            assert svc._model_loaded is False
            assert svc._load_error is not None

    def test_load_error_cached(self):
        """重复失败不重复尝试"""
        svc = RerankerService(RerankerConfig(force_fallback=False))
        svc._load_error = "previous error"
        assert not svc._load_model()


class TestRerankerRerank:
    """rerank 全路径测试"""

    @staticmethod
    def make_item(content="test", score=0.5):
        return {
            "chunk": {"id": "c1", "content": content, "document_id": "d1"},
            "document": {"id": "d1", "name": "doc1", "file_type": "md"},
            "score": score, "fused_score": score,
        }

    def test_rerank_single_item(self):
        """单元素直接返回"""
        svc = RerankerService(RerankerConfig(force_fallback=True))
        result = asyncio.run(svc.rerank("query", [self.make_item()], top_k=5))
        assert len(result) == 1
        assert "re_score" in result[0]

    def test_rerank_empty(self):
        """空输入"""
        svc = RerankerService(RerankerConfig(force_fallback=True))
        assert asyncio.run(svc.rerank("query", [], top_k=5)) == []

    def test_rerank_model_timeout(self):
        """模型推理超时降级"""
        svc = RerankerService(RerankerConfig(force_fallback=False))
        with patch.object(svc, "_load_model", return_value=True):
            with patch.object(svc, "_rerank_with_model", side_effect=asyncio.TimeoutError("timeout")):
                result = asyncio.run(svc.rerank("query", [self.make_item()], top_k=5))
                assert len(result) == 1

    def test_rerank_model_exception(self):
        """模型推理异常降级"""
        svc = RerankerService(RerankerConfig(force_fallback=False))
        with patch.object(svc, "_load_model", return_value=True):
            with patch.object(svc, "_rerank_with_model", side_effect=Exception("runtime error")):
                result = asyncio.run(svc.rerank("query", [self.make_item()], top_k=5))
                assert len(result) == 1


# ============================================================
# Part D: retrieval.py — keyword_search, vector_search
# ============================================================

class TestRetrievalSubMethods:
    """检索子方法独立测试"""

    def test_keyword_search_no_docs(self):
        """无可用文档时返回空"""
        svc = make_retrieval_svc()
        db = make_mock_db()
        mock_table_query(db, return_data=[])
        with patch("api.services.retrieval.db", db):
            result = svc.keyword_search("test", "user-1")
        assert result == []

    def test_keyword_search_exception(self):
        """异常时返回空"""
        svc = make_retrieval_svc()
        db = make_mock_db()
        db.client.table.side_effect = Exception("DB error")
        with patch("api.services.retrieval.db", db):
            result = svc.keyword_search("test", "user-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_no_embedding(self):
        """向量获取失败时返回空"""
        svc = make_retrieval_svc()
        svc.embedding_service.get_embedding = AsyncMock(return_value=None)
        result = await svc.vector_search("test", "user-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_rpc_failure(self):
        """RPC 调用失败时返回空"""
        svc = make_retrieval_svc()
        db = make_mock_db()
        db.client.rpc = lambda n, p: (_ for _ in ()).throw(Exception("RPC error"))
        with patch("api.services.retrieval.db", db):
            result = await svc.vector_search("test", "user-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_empty_response(self):
        """RPC 返回空数据时返回空"""
        svc = make_retrieval_svc()
        db = make_mock_db()
        rpc_mock = MagicMock()
        rpc_mock.execute.return_value.data = []
        db.client.rpc = lambda n, p: rpc_mock
        mock_table_query(db, return_data=[])
        with patch("api.services.retrieval.db", db):
            result = await svc.vector_search("test", "user-1")
        assert result == []


# ============================================================
# Part E: compression.py — compress 方法全路径
# ============================================================

class TestCompressFullFlow:
    """compress 全路径测试"""

    @staticmethod
    def make_chunk(content):
        return {"chunk": {"content": content}}

    def test_compress_empty_chunks(self):
        """空切片返回空"""
        assert asyncio.run(CompressionService().compress("query", [])) == ""

    def test_compress_max_chars_zero(self):
        """max_chars=0 返回空"""
        assert asyncio.run(CompressionService().compress("query", [self.make_chunk("t")], max_chars=0)) == ""

    def test_compress_empty_query(self):
        """空查询时截断"""
        text = "A" * 200
        r = asyncio.run(CompressionService().compress("", [self.make_chunk(text)], max_chars=100))
        assert len(r) == 100
        assert r == text[:100]

    def test_compress_under_limit(self):
        """原文不超限时原样返回"""
        r = asyncio.run(CompressionService().compress("test", [self.make_chunk("Hello")], max_chars=100))
        assert r == "Hello"

    def test_compress_truncate_mode(self):
        """truncate 模式"""
        r = asyncio.run(CompressionService().compress("t", [self.make_chunk("A" * 200)], max_chars=50, mode="truncate"))
        assert len(r) == 50

    def test_compress_unknown_mode(self):
        """未知模式降级"""
        r = asyncio.run(CompressionService().compress("t", [self.make_chunk("A" * 200)], max_chars=50, mode="x"))
        assert len(r) == 50

    def test_compress_summarize_no_api_key(self):
        """summarize 无 API key 降级 extract"""
        content = "大语言模型是一种深度学习模型。Transformer 架构是关键。"
        with patch.dict(os.environ, {}, clear=True):
            r = asyncio.run(CompressionService().compress("LLM", [self.make_chunk(content)], max_chars=500, mode="summarize"))
        assert "大语言模型" in r or "Transformer" in r
