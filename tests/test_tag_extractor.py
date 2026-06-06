"""
测试 TagExtractor — 零成本标签提取逻辑
运行: python -m pytest tests/test_tag_extractor.py -v
"""

import sys
sys.path.insert(0, '.')

from api.services.tag_extractor import TagExtractor


def test_exact_tag_match():
    """精确匹配：用户消息中包含已有标签"""
    extractor = TagExtractor(["LLM", "GPT", "RAG", "多模态", "Agent"])
    
    result = extractor.extract("GPT-5 和 Claude 哪个更强？")
    assert "GPT" in result, f"应匹配 GPT，实际: {result}"


def test_partial_tag_match():
    """模糊匹配：用户消息中包含标签的子串"""
    extractor = TagExtractor(["Transformer", "Diffusion", "LoRA"])
    
    result = extractor.extract("transformer 架构有什么优势？")
    assert "Transformer" in result, f"应匹配 Transformer，实际: {result}"


def test_chinese_tag_match():
    """中文标签匹配"""
    extractor = TagExtractor(["大模型", "多模态", "强化学习", "模型压缩"])
    
    result = extractor.extract("最近多模态大模型有什么新进展？")
    assert "多模态" in result, f"应匹配 多模态，实际: {result}"
    assert "大模型" in result, f"应匹配 大模型，实际: {result}"


def test_no_match():
    """不匹配时返回空列表"""
    extractor = TagExtractor(["LLM", "GPT", "RAG"])
    
    result = extractor.extract("今天天气怎么样？")
    assert result == [], f"应返回 []，实际: {result}"


def test_empty_message():
    """空消息不报错"""
    extractor = TagExtractor(["LLM", "GPT"])
    
    assert extractor.extract("") == []
    assert extractor.extract(None) == []


def test_stop_words_filtered():
    """停用词不参与匹配"""
    extractor = TagExtractor(["一个", "今天", "好的"])
    
    # 这些都是停用词，不应匹配
    result = extractor.extract("今天是一个好的开始")
    assert result == [], f"停用词不应匹配，实际: {result}"


def test_case_insensitive():
    """大小写不敏感匹配"""
    extractor = TagExtractor(["GPT", "LLM", "MoE"])
    
    result = extractor.extract("gpt-4o 和 moe 架构")
    assert "GPT" in result, f"应匹配 GPT，实际: {result}"
    assert "MoE" in result, f"应匹配 MoE，实际: {result}"


def test_multiple_tags_in_one_message():
    """一条消息匹配多个标签"""
    extractor = TagExtractor(["LLM", "RAG", "Agent", "工具调用"])
    
    result = extractor.extract("用 RAG 增强 LLM 的 Agent 能力")
    assert "LLM" in result, f"应匹配 LLM"
    assert "RAG" in result, f"应匹配 RAG"
    assert "Agent" in result, f"应匹配 Agent"


def test_no_duplicate_matches():
    """重复匹配只返回一次"""
    extractor = TagExtractor(["GPT"])
    
    result = extractor.extract("GPT 和 GPT-4 和 GPT-4o 的区别")
    # GPT 只应出现一次
    assert result == ["GPT"], f"应只有一个 GPT，实际: {result}"


def test_short_words_ignored():
    """长度 <= 1 的 token 跳过"""
    extractor = TagExtractor(["A", "B"])
    
    result = extractor.extract("A and B test")
    assert result == [], "单字符不应匹配"


if __name__ == "__main__":
    # 手动运行
    test_exact_tag_match()
    test_partial_tag_match()
    test_chinese_tag_match()
    test_no_match()
    test_empty_message()
    test_stop_words_filtered()
    test_case_insensitive()
    test_multiple_tags_in_one_message()
    test_no_duplicate_matches()
    test_short_words_ignored()
    print("✅ 所有 TagExtractor 测试通过")
