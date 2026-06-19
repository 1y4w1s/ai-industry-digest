"""
意图分类器

使用规则 + 权重打分的方式判断用户意图
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Tuple, Optional
from config.intent_config import (
    INTENT_TYPES, 
    CHAT_ONLY_KEYWORDS, 
    INTENT_INDICATORS, 
    CONFIDENCE_THRESHOLD
)


class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        self.intent_types = INTENT_TYPES
        self.chat_only_keywords = CHAT_ONLY_KEYWORDS
        self.intent_indicators = INTENT_INDICATORS
        self.confidence_threshold = CONFIDENCE_THRESHOLD
    
    def classify(self, message: str) -> Tuple[str, float]:
        """
        分类用户意图
        
        返回：(意图类型, 置信度)
        - 意图类型: "chat", "kb", "article", "daily", "general", "unknown"
        - 置信度: 0.0 - 1.0
        """
        message_lower = message.lower().strip()
        
        # 第一阶段：判断是否是纯闲聊
        has_chat = any(kw in message_lower for kw in self.chat_only_keywords)
        has_intent = any(kw in message_lower for kw in self.intent_indicators)
        
        if has_chat and not has_intent:
            return ("chat", 0.9)  # 高置信度
        
        # 第二阶段：权重打分
        scores = {intent: 0 for intent in self.intent_types}
        matched_keywords = {intent: [] for intent in self.intent_types}
        
        for intent, config in self.intent_types.items():
            for keyword in config["keywords"]:
                if keyword in message_lower:
                    scores[intent] += config["weight"]
                    matched_keywords[intent].append(keyword)
        
        # 找出最高分
        if max(scores.values()) == 0:
            return ("unknown", 0.0)  # 无法判断
        
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # 计算置信度
        total_keywords = len(self.intent_types[best_intent]["keywords"])
        matched_count = len(matched_keywords[best_intent])
        confidence = min(matched_count / max(total_keywords, 1), 1.0)
        
        # 如果最高分和次高分差距太小，置信度降低
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] < 2:
            confidence *= 0.7  # 降低置信度
        
        return (best_intent, confidence)
    
    def classify_with_fallback(self, message: str) -> Optional[str]:
        """
        分类用户意图，带兜底策略
        
        返回：意图类型，如果置信度太低则返回 None（让 LLM 自己判断）
        """
        intent, confidence = self.classify(message)
        
        if confidence < self.confidence_threshold:
            return None  # 不确定，让 LLM 自己判断
        
        return intent


# 单例
classifier = IntentClassifier()


def classify_intent(message: str) -> Optional[str]:
    """便捷函数"""
    return classifier.classify_with_fallback(message)


def get_classifier() -> IntentClassifier:
    """获取分类器实例"""
    return classifier
