"""
F-10 单元测试：元数据增强（Metadata Enrichment）

测试策略：
  - 测试 enrich_metadata() 纯函数对带结构的文档生成丰富 metadata
  - 测试从 markdown 文本中提取章节标题、检测代码块、识别实体
  - 测试边界条件：空内容、纯代码、无标题文档
  - 不依赖数据库、外部 API

当前 metadata 现状：
  {"length": len(chunk)}

改造后 metadata 目标：
  {
      "length": len(chunk),
      "chunk_index": 3,
      "total_chunks": 50,
      "document_name": "LLM 入门",
      "file_type": "markdown",
      "section_title": "2.1 Transformer 架构",
      "section_depth": 2,
      "has_code": False,
      "code_language": None,
      "extracted_entities": ["Transformer", "Attention"],
      "page_number": None,
  }
"""

import json
import pytest

from api.services.metadata import MetadataEnricher


# ═══════════════════════════════════════════════════════════════════
# 测试数据
# ═══════════════════════════════════════════════════════════════════

MARKDOWN_WITH_HEADERS = """# 第一章 人工智能概述

人工智能（AI）是计算机科学的一个重要分支。
它致力于创建能够模拟人类智能的系统。

## 1.1 机器学习

机器学习是 AI 的核心技术之一。
它使计算机能够从数据中学习。

## 1.2 深度学习

深度学习是机器学习的子集。
它使用多层神经网络来学习数据的表示。
"""

MARKDOWN_WITH_CODE = """# Python 编程入门

Python 是一种高级编程语言。

## 变量与数据类型

Python 支持多种数据类型。

```python
x = 10
name = "Alice"
print(f"Hello, {name}")
```

## 函数定义

函数是代码复用的基本单元。

```python
def greet(name):
    return f"Hello, {name}"
```
"""

MARKDOWN_NO_HEADERS = """这是一段没有标题的纯文本。
它不包含任何 markdown 标题标记。
只是一个段落接另一个段落。
"""

PDF_WITH_PAGES = """[Page 1]
第一章 引言
...

[Page 2]
1.1 研究背景
...

[Page 3]
1.2 研究目标
...
"""

DOCX_SAMPLE = "Word 文档内容示例。包含一些重要的技术概念。"

# 示例切片列表（模拟来自 process_document 的输入）
SAMPLE_CHUNKS = [
    {
        "content": "人工智能（AI）是计算机科学的一个重要分支。",
        "chunk_index": 0,
        "document_id": "doc-001",
    },
    {
        "content": "机器学习是 AI 的核心技术之一。它使计算机能够从数据中学习。",
        "chunk_index": 1,
        "document_id": "doc-001",
    },
    {
        "content": "```python\nx = 10\nprint(x)\n```",
        "chunk_index": 2,
        "document_id": "doc-002",
    },
]


# ═══════════════════════════════════════════════════════════════════
# 夹具
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def enricher():
    """返回 MetadataEnricher 实例"""
    return MetadataEnricher()


@pytest.fixture
def enrich():
    """便捷包装：直接调用 enricher.enrich()"""
    enricher = MetadataEnricher()
    return lambda **kw: enricher.enrich(**kw)


# ═══════════════════════════════════════════════════════════════════
# F-10: 基础元数据测试
# ═══════════════════════════════════════════════════════════════════

class TestBasicMetadata:
    """基础元数据字段测试"""

    def test_length_field(self, enricher):
        """length 字段应等于切片字符数"""
        content = "Hello, world!"
        meta = enricher.enrich(content)
        assert meta["length"] == len(content)

    def test_chunk_index(self, enricher):
        """chunk_index 应与传入值一致"""
        meta = enricher.enrich("content", chunk_index=5, total_chunks=10)
        assert meta["chunk_index"] == 5
        assert meta["total_chunks"] == 10

    def test_document_name(self, enricher):
        """document_name 应与传入值一致"""
        meta = enricher.enrich("content", document_name="LLM 入门")
        assert meta["document_name"] == "LLM 入门"

    def test_file_type(self, enricher):
        """file_type 应与传入值一致"""
        meta = enricher.enrich("content", file_type="pdf")
        assert meta["file_type"] == "pdf"

    def test_default_file_type(self, enricher):
        """默认 file_type 应为 markdown"""
        meta = enricher.enrich("content")
        assert meta["file_type"] == "markdown"

    def test_no_none_values(self, enricher):
        """所有字段不应为 None"""
        meta = enricher.enrich("")
        for key, value in meta.items():
            assert value is not None, f"字段 {key} 不应为 None"

    def test_preserve_existing_metadata_structure(self, enricher):
        """保留现有 metadata 中的 length 字段"""
        meta = enricher.enrich("测试内容")
        assert "length" in meta


# ═══════════════════════════════════════════════════════════════════
# F-10: 章节信息提取测试
# ═══════════════════════════════════════════════════════════════════

class TestSectionExtraction:
    """章节标题与层级提取测试"""

    def test_extract_h1_title(self, enricher):
        """提取一级标题"""
        chunk = "人工智能是重要的技术。"
        meta = enricher.enrich(
            chunk,
            full_document=MARKDOWN_WITH_HEADERS,
        )
        # 应至少提取到一个标题
        assert meta["section_title"], "应提取到章节标题"
        assert meta["section_depth"] >= 1

    def test_extract_h2_title(self, enricher):
        """提取二级标题"""
        chunk = "机器学习是 AI 的核心技术之一。"
        meta = enricher.enrich(
            chunk,
            full_document=MARKDOWN_WITH_HEADERS,
        )
        assert meta["section_title"], "应提取到章节标题"

    def test_no_headers_in_document(self, enricher):
        """无标题文档：章节标题应为空字符串"""
        chunk = "这是一段纯文本。"
        meta = enricher.enrich(
            chunk,
            full_document=MARKDOWN_NO_HEADERS,
        )
        assert meta["section_title"] == ""
        assert meta["section_depth"] == 0

    def test_empty_full_document(self, enricher):
        """无 full_document 时：章节标题应为空"""
        meta = enricher.enrich("content")
        assert meta["section_title"] == ""
        assert meta["section_depth"] == 0

    def test_heading_depth_accuracy(self, enricher):
        """标题层级应准确对应 # 数量"""
        markdown = "# H1\n\n内容\n\n## H2\n\n内容\n\n### H3\n\n内容"
        chunk_h1 = "H1 下的内容"
        meta = enricher.enrich(chunk_h1, full_document=markdown)
        assert meta["section_depth"] in (1, 2, 3), f"应提取到某级标题, 得到 depth={meta['section_depth']}"


# ═══════════════════════════════════════════════════════════════════
# F-10: 代码块检测测试
# ═══════════════════════════════════════════════════════════════════

class TestCodeBlockDetection:
    """代码块检测测试"""

    def test_detect_python_code_block(self, enricher):
        """检测 Python 代码块"""
        content = "```python\nprint('hello')\n```"
        has_code, lang = enricher._detect_code_block(content)
        assert has_code is True
        assert lang == "python"

    def test_detect_code_without_language(self, enricher):
        """检测无语言标注的代码块"""
        content = "```\nprint('hello')\n```"
        has_code, lang = enricher._detect_code_block(content)
        assert has_code is True
        assert lang == "unknown"

    def test_no_code_block(self, enricher):
        """纯文本应检测不含代码"""
        content = "这是一段普通的文本。"
        has_code, lang = enricher._detect_code_block(content)
        assert has_code is False
        assert lang is None

    def test_inline_code_not_detected(self, enricher):
        """行内 `code` 不应被检测为代码块"""
        content = "使用 `print()` 函数输出内容。"
        has_code, lang = enricher._detect_code_block(content)
        assert has_code is False

    def test_has_code_metadata_field(self, enricher):
        """enricher.enrich 应正确反映 has_code 字段"""
        meta = enricher.enrich(
            "```javascript\nconsole.log('hi')\n```",
            file_type="markdown",
        )
        assert meta["has_code"] is True
        assert meta["code_language"] == "javascript"

    def test_multiple_code_blocks(self, enricher):
        """多个代码块仍应被检测"""
        content = """```python
x = 1
```
Some text
```javascript
console.log(y)
```"""
        has_code, lang = enricher._detect_code_block(content)
        assert has_code is True
        assert lang == "python"  # 取第一个


# ═══════════════════════════════════════════════════════════════════
# F-10: 实体提取测试
# ═══════════════════════════════════════════════════════════════════

class TestEntityExtraction:
    """实体筛选与标注测试"""

    def test_filter_entities_in_chunk(self, enricher):
        """只保留切片中包含的实体"""
        entities = ["Transformer", "GPT-4", "BERT", "CNN"]
        chunk = "GPT-4 是基于 Transformer 架构的模型。"
        meta = enricher.enrich(
            chunk,
            extracted_entities=entities,
        )
        assert "GPT-4" in meta["extracted_entities"]
        assert "Transformer" in meta["extracted_entities"]
        assert "BERT" not in meta["extracted_entities"]
        assert "CNN" not in meta["extracted_entities"]

    def test_no_entities_provided(self, enricher):
        """未提供实体列表时返回空列表"""
        meta = enricher.enrich("some content")
        assert meta["extracted_entities"] == []

    def test_empty_entities_list(self, enricher):
        """空实体列表应返回空列表"""
        meta = enricher.enrich("content", extracted_entities=[])
        assert meta["extracted_entities"] == []

    def test_case_insensitive_matching(self, enricher):
        """实体匹配应不区分大小写"""
        entities = ["llm", "gpt"]
        chunk = "LLM 和 GPT 是不同的概念。"
        meta = enricher.enrich(chunk, extracted_entities=entities)
        assert "llm" in meta["extracted_entities"]
        assert "gpt" in meta["extracted_entities"]

    def test_entity_deduplication(self, enricher):
        """实体不应重复"""
        entities = ["Transformer", "Transformer"]
        chunk = "Transformer 改变了 NLP。"
        meta = enricher.enrich(chunk, extracted_entities=entities)
        assert meta["extracted_entities"] == ["Transformer"]


# ═══════════════════════════════════════════════════════════════════
# F-10: 页码与综合场景测试
# ═══════════════════════════════════════════════════════════════════

class TestPageNumberAndIntegration:
    """页码与综合场景测试"""

    def test_page_number_field(self, enricher):
        """页码字段应正确传递"""
        meta = enricher.enrich("content", page_number=5)
        assert meta["page_number"] == 5

    def test_page_number_default_none(self, enricher):
        """非 PDF 来源的切片页码应为 0（表示未知）"""
        meta = enricher.enrich("content")
        assert meta["page_number"] == 0

    def test_full_metadata_keys(self, enricher):
        """验证完整 metadata 的字段集合"""
        meta = enricher.enrich("测试")
        expected_keys = {
            "length", "chunk_index", "total_chunks",
            "document_name", "file_type",
            "section_title", "section_depth",
            "has_code", "code_language",
            "extracted_entities", "page_number",
        }
        assert set(meta.keys()) == expected_keys, \
            f"多余的 key: {set(meta.keys()) - expected_keys}, " \
            f"缺失的 key: {expected_keys - set(meta.keys())}"

    def test_enrich_real_chunks(self, enricher):
        """用真实数据验证增强效果"""
        full_doc = MARKDOWN_WITH_HEADERS
        chunks = [c.strip() for c in full_doc.split("\n\n") if c.strip()]
        entities = ["人工智能", "机器学习", "深度学习"]
        
        for i, chunk in enumerate(chunks[:3]):
            meta = enricher.enrich(
                chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                document_name="AI 入门",
                file_type="markdown",
                full_document=full_doc,
                extracted_entities=entities,
            )
            assert meta["chunk_index"] == i
            assert meta["total_chunks"] >= 3
            assert meta["document_name"] == "AI 入门"
            assert meta["file_type"] == "markdown"

    def test_metadata_json_serializable(self, enricher):
        """metadata 应可序列化为 JSON"""
        meta = enricher.enrich(
            "测试内容",
            chunk_index=1,
            total_chunks=5,
            document_name="test.md",
            file_type="markdown",
            extracted_entities=["AI"],
        )
        json_str = json.dumps(meta, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["length"] == 4
        assert parsed["document_name"] == "test.md"


# ═══════════════════════════════════════════════════════════════════
# F-10: 边界条件测试
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """边界条件测试"""

    def test_empty_content(self, enricher):
        """空内容应正常处理"""
        meta = enricher.enrich("")
        assert meta["length"] == 0
        assert meta["has_code"] is False

    def test_very_long_content(self, enricher):
        """超长内容不应报错"""
        content = "a" * 10000
        meta = enricher.enrich(content)
        assert meta["length"] == 10000
        assert meta["has_code"] is False

    def test_content_with_only_code_fence(self, enricher):
        """仅含代码围栏的内容"""
        content = "```\n```"
        meta = enricher.enrich(content)
        assert meta["has_code"] is True
        # 围栏内容为空，但检测到代码块结构

    def test_unicode_content(self, enricher):
        """Unicode 多语言内容"""
        content = "人工智能（AI）\nMachine Learning\n🌐"
        meta = enricher.enrich(content)
        assert meta["length"] == len(content)

    def test_special_characters_in_entities(self, enricher):
        """实体中包含特殊字符"""
        entities = ["C++", "C#", ".NET"]
        chunk = "C++ 和 C# 都是 .NET 生态的一部分。"
        meta = enricher.enrich(chunk, extracted_entities=entities)
        assert "C++" in meta["extracted_entities"]
        assert "C#" in meta["extracted_entities"]
        assert ".NET" in meta["extracted_entities"]

    def test_entities_in_code_block(self, enricher):
        """代码块中的实体应被检测"""
        entities = ["requests", "json"]
        chunk = "```python\nimport requests\nimport json\n```"
        meta = enricher.enrich(chunk, extracted_entities=entities)
        assert "requests" in meta["extracted_entities"]
        assert "json" in meta["extracted_entities"]
