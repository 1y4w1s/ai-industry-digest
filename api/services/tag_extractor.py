"""
Signal - 标签提取器
从用户的 AI 对话提示词中提取关键词，匹配已有文章标签
零额外 API 成本 — 仅做字符串匹配
"""

import re
from typing import List, Set


class TagExtractor:
    """从用户消息中提取匹配文章标签的关键词"""

    # 常见中文停用词（不参与匹配）
    STOP_WORDS: Set[str] = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她",
        "它", "们", "那", "这个", "那个", "什么", "怎么", "如何", "为什么",
        "可以", "能", "吗", "吧", "呢", "啊", "哦", "嗯", "比如", "例如",
        "还是", "或者", "比较", "哪个", "哪些", "告诉", "请问", "帮忙",
        "帮", "想", "知道", "了解", "介绍", "推荐", "解释", "总结",
        "分析", "对比", "区别", "关系", "影响", "意义", "作用",
        "今天", "昨天", "明天", "最近", "最新", "现在", "目前",
        "文章", "新闻", "消息", "内容", "信息", "报道", "资讯",
        "关于", "相关", "所有", "各种", "不同", "一些",
        "觉得", "感觉", "认为", "以为", "看来",
        "谢谢", "感谢", "谢谢", "好的", "ok", "嗯嗯",
        "还有", "另外", "其他", "以及",
        "一个", "一种", "这个", "这些", "那个", "那些",
    }

    def __init__(self, known_tags: List[str]):
        """
        Args:
            known_tags: 数据库中所有已有标签列表（来自 articles.tags）
        """
        self._known_tags = known_tags
        # 预处理标签：小写化 + 去空格，用于快速匹配
        self._tag_index = {tag.strip().lower(): tag for tag in known_tags if tag.strip()}

    @classmethod
    def from_database(cls, db) -> "TagExtractor":
        """从数据库获取所有标签并创建提取器"""
        known_tags = db.get_tags()
        return cls(known_tags)

    def extract(self, message: str) -> List[str]:
        """从用户消息中提取匹配的标签

        Args:
            message: 用户发送的对话消息

        Returns:
            匹配到的标签列表（原始大小写，来自数据库）
        """
        if not message or not self._tag_index:
            return []

        cleaned = self._clean_message(message)
        matched = set()

        for word in self._tokenize(cleaned):
            word_lower = word.lower()
            # 精确匹配
            if word_lower in self._tag_index:
                matched.add(self._tag_index[word_lower])
                continue
            # 包含匹配（如 "transformer" 匹配 "Transformer"）
            # 限制双方至少 2 字符，避免单字母误匹配
            for tag_lower, tag_original in self._tag_index.items():
                if len(tag_lower) < 2 or len(word_lower) < 2:
                    continue
                if tag_lower in word_lower or word_lower in tag_lower:
                    matched.add(tag_original)

        return list(matched)

    def _clean_message(self, message: str) -> str:
        """清理消息：移除标点、数字、停用词等"""
        # 移除常见标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', message)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _tokenize(self, text: str) -> List[str]:
        """分词：按空格拆分为单词 + 提取连续中文词组"""
        tokens = []
        # 提取英文单词和数字
        for word in text.split():
            w = word.strip()
            if w and w.lower() not in self.STOP_WORDS and len(w) > 1:
                # 纯中文由下方 bigram 处理，跳过整体加入
                if re.fullmatch(r'[\u4e00-\u9fff]+', w):
                    continue
                tokens.append(w)

        # 提取中文 2 字词组（滑动窗口）
        # 注意：不加完整长句到 tokens，避免包含匹配误判停用词
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        for chunk in chinese_chars:
            for i in range(len(chunk) - 1):
                bigram = chunk[i:i + 2]
                if bigram not in self.STOP_WORDS and len(bigram) > 1:
                    tokens.append(bigram)

        return tokens
