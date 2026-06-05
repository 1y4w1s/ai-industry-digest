"""
Signal - 数据采集基类
定义 Article 数据模型和采集器抽象基类
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from abc import ABC, abstractmethod


@dataclass
class Article:
    """统一文章数据模型"""
    title: str                             # 文章标题
    url: str                               # 原文链接
    source_name: str                       # 来源名称（如"机器之心"）
    raw_content: str                       # 原始正文/描述
    published_at: Optional[datetime] = None  # 原文发布时间
    summary: Optional[str] = None          # AI 摘要（后续填充）
    tags: List[str] = field(default_factory=list)  # 标签（后续填充）
    importance: Optional[str] = None       # 重要性（后续填充）
    importance_reason: Optional[str] = None
    source_refs: List[str] = field(default_factory=list)  # 同事件其他来源
    created_at: datetime = field(default_factory=datetime.utcnow)


class BaseCollector(ABC):
    """采集器抽象基类
    所有采集器（RSS、API、网页抓取）都继承此类
    """

    def __init__(self, source_config: dict):
        """
        Args:
            source_config: sources.yaml 中对应信息源的配置字典
        """
        self.name = source_config.get("name", "unknown")
        self.source_id = source_config.get("id", "unknown")
        self.priority = source_config.get("priority", 3)
        self.enabled = source_config.get("enabled", True)
        self.config = source_config

    @abstractmethod
    def collect(self) -> List[Article]:
        """采集文章列表
        每个子类必须实现此方法

        Returns:
            List[Article]: 采集到的文章列表
        """
        pass

    def _make_article(self, title: str, url: str, content: str,
                      published_at: Optional[datetime] = None) -> Article:
        """快捷创建 Article 对象"""
        return Article(
            title=self._clean_text(title),
            url=url.strip(),
            source_name=self.name,
            raw_content=self._clean_text(content),
            published_at=published_at or datetime.utcnow()
        )

    def _clean_text(self, text: str) -> str:
        """清理文本：去除多余空白（保留段落间距）"""
        if not text:
            return ""
        import re
        # 保留换行，只压缩连续空白
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
