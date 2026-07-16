"""
Signal · 中文分词工具
使用 jieba 对中文文本做分词预处理，用于 PostgreSQL 全文搜索。
将连续的中文字符序列用空格分隔，使 'simple' 分词器能正确建立词条索引。
"""

import re

# 尝试导入 jieba，若不可用则降级为单字分割
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


# 匹配中文字符（CJK统一表意文字）
CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]+')


def tokenize_chinese(text: str) -> str:
    """对文本中的中文部分做分词，非中文部分保持原样

    示例：
        "OpenAI发布GPT-4模型影响人工智能发展"
        → "OpenAI 发布 GPT-4 模型 影响 人工智能 发展"
    """
    if not text:
        return ""

    def _replace_cjk(match):
        segment = match.group(0)
        if JIEBA_AVAILABLE:
            return " " + " ".join(jieba.cut(segment, cut_all=False)) + " "
        else:
            # 降级：单字分割（"人工智能" → "人 工 智 能"）
            return " " + " ".join(segment) + " "

    return CHINESE_PATTERN.sub(_replace_cjk, text).strip()


def tokenize_article_fields(title: str = "", summary: str = "",
                            source_name: str = "", tags_str: str = "") -> dict:
    """对文章的搜索相关字段做中文分词

    返回分词后的字段字典，用于构建 search_vector 的输入文本。
    """
    return {
        "title_tokens": tokenize_chinese(title),
        "summary_tokens": tokenize_chinese(summary),
        "source_tokens": tokenize_chinese(source_name),
        "tags_tokens": tokenize_chinese(tags_str),
    }


def build_search_text(title: str = "", summary: str = "",
                      source_name: str = "", tags: list = None) -> str:
    """构建用于 to_tsvector 的完整搜索文本

    所有中文文本经过 jieba 分词，非中文文本保持不变。
    """
    tags_str = " ".join(tags or [])
    tokens = tokenize_article_fields(title, summary, source_name, tags_str)
    parts = [
        tokens["title_tokens"],
        tokens["summary_tokens"],
        tokens["source_tokens"],
        tokens["tags_tokens"],
    ]
    return " ".join(p for p in parts if p)
