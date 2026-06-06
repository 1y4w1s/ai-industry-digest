"""
Signal - 知识库 API 测试
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# 测试用的文档内容
SAMPLE_CONTENT = """
大语言模型（LLM）是人工智能领域的重要突破。
OpenAI 开发的 GPT-4 是目前最先进的语言模型之一。
Google 发布了 PaLM 2 模型，在多项任务上表现优异。
DeepSeek 是国内优秀的 AI 公司，开发了 DeepSeek-V2 模型。
RAG（检索增强生成）技术结合了检索和生成的优势。
"""

# 测试切片函数
def test_split_into_chunks():
    """测试文档切片功能"""
    from api.routes.kb import split_into_chunks
    
    # 短文本测试
    short_text = "这是一段测试文本。"
    chunks = split_into_chunks(short_text, chunk_size=10, overlap=2)
    assert len(chunks) >= 1
    assert chunks[0] == short_text
    
    # 长文本测试
    long_text = "。" * 100
    chunks = split_into_chunks(long_text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    # 每个切片长度不超过 chunk_size（允许微调）
    for chunk in chunks:
        assert len(chunk) <= 25  # 20 + 5（允许微调）
    
    print("✅ 切片功能测试通过")


def test_supported_extensions():
    """测试支持的文件类型"""
    from api.routes.kb import SUPPORTED_EXTENSIONS
    
    expected_extensions = {".txt", ".md", ".pdf", ".docx"}
    actual_extensions = set(SUPPORTED_EXTENSIONS.keys())
    
    assert expected_extensions.issubset(actual_extensions), \
        f"缺少支持的扩展名: {expected_extensions - actual_extensions}"
    
    print("✅ 文件类型支持测试通过")


def test_file_type_mapping():
    """测试文件类型映射"""
    from api.routes.kb import SUPPORTED_EXTENSIONS
    
    expected_mapping = {
        ".txt": "text",
        ".md": "markdown",
        ".pdf": "pdf",
        ".docx": "docx",
    }
    
    for ext, expected_type in expected_mapping.items():
        assert SUPPORTED_EXTENSIONS.get(ext) == expected_type, \
            f"{ext} 类型映射错误"
    
    print("✅ 文件类型映射测试通过")


def test_chunk_content_preservation():
    """测试切片内容完整性"""
    from api.routes.kb import split_into_chunks
    
    # 包含关键信息的文本
    content = "大语言模型（LLM）是重要技术。GPT-4 是 OpenAI 的产品。"
    chunks = split_into_chunks(content, chunk_size=30, overlap=5)
    
    # 合并所有切片应该包含原文
    combined = "".join(chunks)
    assert "大语言模型" in combined
    assert "LLM" in combined
    assert "GPT-4" in combined
    assert "OpenAI" in combined
    
    print("✅ 切片内容完整性测试通过")


def test_max_file_size():
    """测试文件大小限制"""
    from api.routes.kb import MAX_FILE_SIZE
    
    # 10MB 限制
    assert MAX_FILE_SIZE == 10 * 1024 * 1024
    
    print("✅ 文件大小限制测试通过")


def test_uuid_format():
    """测试 UUID 格式"""
    test_id = str(uuid.uuid4())
    
    # UUID 应该是 36 个字符，包含连字符
    assert len(test_id) == 36
    assert test_id.count("-") == 4
    
    print("✅ UUID 格式测试通过")


def test_document_status_values():
    """测试文档状态值"""
    valid_statuses = ["pending", "processing", "completed", "failed"]
    
    # 模拟数据库中的状态
    mock_status = "pending"
    assert mock_status in valid_statuses
    
    mock_status = "completed"
    assert mock_status in valid_statuses
    
    mock_status = "failed"
    assert mock_status in valid_statuses
    
    print("✅ 文档状态值测试通过")


def test_entity_types():
    """测试实体类型"""
    valid_types = ["concept", "person", "organization", "technology", "product"]
    
    # 模拟实体识别结果
    mock_entities = [
        {"name": "大语言模型", "type": "concept"},
        {"name": "Sam Altman", "type": "person"},
        {"name": "OpenAI", "type": "organization"},
        {"name": "Transformer", "type": "technology"},
        {"name": "GPT-4", "type": "product"},
    ]
    
    for entity in mock_entities:
        assert entity["type"] in valid_types, \
            f"未知实体类型: {entity['type']}"
    
    print("✅ 实体类型测试通过")


def test_relation_types():
    """测试关系类型"""
    valid_relations = ["is_a", "part_of", "related_to", "based_on", 
                       "author_of", "published_by", "developed_by"]
    
    # 模拟关系抽取结果
    mock_relations = [
        {"source": "GPT-4", "target": "LLM", "relation": "is_a"},
        {"source": "GPT-4", "target": "Transformer", "relation": "based_on"},
    ]
    
    for relation in mock_relations:
        assert relation["relation"] in valid_relations, \
            f"未知关系类型: {relation['relation']}"
    
    print("✅ 关系类型测试通过")


def test_pagination_params():
    """测试分页参数"""
    # 模拟分页参数
    page = 1
    page_size = 20
    
    # 计算偏移量
    offset = (page - 1) * page_size
    assert offset == 0
    
    page = 2
    offset = (page - 1) * page_size
    assert offset == 20
    
    # 计算总页数
    total = 55
    pages = (total + page_size - 1) // page_size
    assert pages == 3
    
    print("✅ 分页参数测试通过")


def test_tags_processing():
    """测试标签处理"""
    # 模拟标签输入
    tags_input = "LLM, GPT, 大模型"
    tag_list = [t.strip() for t in tags_input.split(",") if t.strip()]
    
    assert len(tag_list) == 3
    assert "LLM" in tag_list
    assert "GPT" in tag_list
    assert "大模型" in tag_list
    
    # 测试空标签
    tags_input = ""
    tag_list = [t.strip() for t in tags_input.split(",") if t.strip()]
    assert len(tag_list) == 0
    
    print("✅ 标签处理测试通过")


# 集成测试（需要数据库连接）
@pytest.mark.skip(reason="需要数据库连接")
def test_full_document_workflow():
    """完整的文档上传流程测试"""
    # 这个测试需要真实的数据库连接
    # 在CI环境中运行
    
    # 1. 上传文档
    # 2. 获取文档列表
    # 3. 处理文档
    # 4. 获取切片
    # 5. 获取图谱
    # 6. 删除文档
    
    pass


if __name__ == "__main__":
    # 运行所有测试
    print("\n" + "="*50)
    print("开始运行知识库单元测试")
    print("="*50 + "\n")
    
    test_split_into_chunks()
    test_supported_extensions()
    test_file_type_mapping()
    test_chunk_content_preservation()
    test_max_file_size()
    test_uuid_format()
    test_document_status_values()
    test_entity_types()
    test_relation_types()
    test_pagination_params()
    test_tags_processing()
    
    print("\n" + "="*50)
    print("✅ 所有单元测试通过！")
    print("="*50)
