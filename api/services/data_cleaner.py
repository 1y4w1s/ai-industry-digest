"""
数据清洗服务：为知识库文档提供全面的数据清洗和预处理

功能清单：
  1. 重复文档检测（基于内容 hash，跨用户去重）
  2. 短文本/低质量过滤（最少字符数、中文字符占比）
  3. Unicode 规范化（零宽字符、全角/半角、各类空白字符）
  4. 噪音清理（URL/邮箱/电话号码/特殊符号）
  5. 文档级别清洗管线（一次调用即可完成所有清洗步骤）

使用方式：
  from api.services.data_cleaner import get_data_cleaner, DocumentQuality

  cleaner = get_data_cleaner()
  
  # 完整清洗管线
  result = cleaner.clean_document(content)
  
  # 单独检测质量
  quality = cleaner.check_quality(content)
  if quality.is_low_quality:
      print(f"低质量文档: {quality.reasons}")
  
  # 检查重复
  dup = cleaner.check_duplicate(content, user_id)
  if dup["is_duplicate"]:
      print(f"与文档 {dup['duplicate_of']} 重复")
"""

import re
import hashlib
import unicodedata
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field


# ── 正则表达式常量 ────────────────────────────

# HTML 注释
_RE_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# 样式/脚本块
_RE_STYLE_SCRIPT = re.compile(r"<(style|script)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
# 块级标签换行（转为 \n 而非移除）
_RE_BLOCK_TAGS = re.compile(r"</?(?:p|div|br|h[1-6]|blockquote|li|tr|td|th|section|article|header|footer|nav|aside)\s*/?>", re.IGNORECASE)
# 剩余 HTML 标签
_RE_HTML_TAG = re.compile(r"<[^>]+>")
# HTML entity 解码（常见）
_HTML_ENTITIES = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">",
    "&nbsp;": " ", "&quot;": '"', "&apos;": "'",
    "&ndash;": "–", "&mdash;": "—",
    "&hellip;": "…", "&middot;": "·",
    "&bull;": "•", "&raquo;": "»", "&laquo;": "«",
}
# HTML numeric entity 匹配 &#123; 或 &#x1F;
_RE_NUMERIC_ENTITY = re.compile(r"&#(\d{2,5});")
_RE_HEX_ENTITY = re.compile(r"&#x([0-9a-fA-F]{2,4});")

# URL（http/https/ftp 协议开头的完整 URL）
_RE_URL = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w$.+!*'(),;:@&=?/~#%]*)?", re.IGNORECASE)
# 纯域名匹配（匹配域名本身，避免误伤代码中的标识符）
_RE_DOMAIN = re.compile(r"(?:[a-zA-Z0-9-]+\.)+(?:com|cn|org|net|io|gov|edu|me|cc|top|xyz|ai|app|dev|info|biz)(?=[/\s,.;:!?)}\]])", re.IGNORECASE)
# 邮箱
_RE_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# 中国大陆手机号（11 位数字，1 开头）
_RE_PHONE_CN = re.compile(r"1[3-9]\d{9}")
# 固话（区号-号码）
_RE_PHONE_LANDLINE = re.compile(r"0\d{2,3}[-]\d{7,8}")
# IPv4 地址
_RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Markdown 图片/链接标记（保留标题文本）
_RE_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
# 零宽字符集合
_ZERO_WIDTH_CHARS = re.compile(
    "[\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064"
    "\ufeff\ufff9\ufffa\ufffb]"
)
# 空白行合并（3 行以上 → 2 行）
_RE_EMPTY_LINES = re.compile(r"\n{3,}")
# 行首/行尾空白
_RE_LINE_WS = re.compile(r"[^\S\n]+(?=\n)|(?<=\n)[^\S\n]+")
# 连续空白字符（非换行）→ 单个空格
_RE_CONSECUTIVE_SPACES = re.compile(r"[^\S\n]{2,}")
# 连续分隔符（---、===、*** 等，常见于 markdown 分隔线和冗余装饰）
_RE_SEPARATORS = re.compile(r"\n[=*#\-\s]{10,}\n")
# 文件路径/Windows 路径痕迹
_RE_FILE_PATH = re.compile(r"[a-zA-Z]:\\[^\\\s]{3,}(?:\\[^\\\s]+)*")


@dataclass
class DocumentQuality:
    """文档质量评估结果"""
    is_low_quality: bool = False
    reasons: List[str] = field(default_factory=list)
    char_count: int = 0
    chinese_ratio: float = 0.0
    noise_ratio: float = 0.0


class DataCleaner:
    """数据清洗器

    提供知识库文档的全流程清洗能力，包括：
    - 文档级的质量检查（短文本、低信息密度）
    - 内容规范化（Unicode、空白字符、全角/半角）
    - 噪音去除（URL、邮箱、电话、HTML 残留）
    - 重复检测（基于 MD5 哈希）
    - 切片级质量过滤
    """

    # 质量阈值
    MIN_CHAR_COUNT: int = 30           # 少于 30 个有效字 → 低质量
    MIN_CHINESE_RATIO: float = 0.05    # 中文字符占比低于 5%，且非纯英文 → 低质量
    MAX_NOISE_RATIO: float = 0.30      # 噪音字符占比超过 30% → 低质量
    MAX_URL_COUNT: int = 3             # 超过 3 个独立 URL → 低质量（可能是 URL 收藏夹）

    # 切片级阈值
    MIN_CHUNK_CHARS: int = 10          # 切片少于 10 个有效字符 → 跳过
    MAX_CHUNK_NOISE_RATIO: float = 0.5  # 切片噪音超过 50% → 跳过

    def __init__(self):
        self._hash_cache: Dict[str, str] = {}

    # ════════════════════════════════════════════
    # 1. 完整清洗管线
    # ════════════════════════════════════════════

    def clean_document(self, content: str) -> str:
        """完整文档清洗管线：HTML 剥离 → 规范化 → 噪音清理 → 美化

        Args:
            content: 原始文档内容

        Returns:
            清洗后的纯文本内容
        """
        if not content:
            return ""

        # 步骤 1: 剥离 HTML 标签
        text = self._strip_html(content)

        # 步骤 2: Unicode 规范化
        text = self._normalize_unicode(text)

        # 步骤 3: 噪音清理
        text = self._remove_noise(text)

        # 步骤 4: 清理零宽字符
        text = _ZERO_WIDTH_CHARS.sub("", text)

        # 步骤 5: 美化（空行合并、首尾清理）
        text = self._beautify(text)

        return text.strip()

    def clean_chunk(self, chunk_content: str) -> str:
        """清洗单个切片（轻量版，保留上下文完整性）"""
        if not chunk_content:
            return ""
        text = _ZERO_WIDTH_CHARS.sub("", chunk_content)
        text = _RE_CONSECUTIVE_SPACES.sub(" ", text)
        return text.strip()

    # ════════════════════════════════════════════
    # 2. 质量评估
    # ════════════════════════════════════════════

    def check_quality(self, content: str) -> DocumentQuality:
        """评估文档整体质量

        Returns:
            DocumentQuality 对象，包含是否低质量及原因
        """
        quality = DocumentQuality()

        if not content or not content.strip():
            quality.is_low_quality = True
            quality.reasons.append("内容为空")
            return quality

        stats = self._compute_stats(content)
        quality.char_count = stats["char_count"]
        quality.chinese_ratio = stats["chinese_ratio"]
        quality.noise_ratio = stats["noise_ratio"]

        # 检查：空内容
        if stats["char_count"] < self.MIN_CHAR_COUNT:
            quality.is_low_quality = True
            quality.reasons.append(
                f"有效字符数 {stats['char_count']} 低于阈值 {self.MIN_CHAR_COUNT}"
            )

        # 检查：中文占比过低且非纯英文文档
        if (stats["chinese_ratio"] < self.MIN_CHINESE_RATIO
                and not stats["is_english_dominant"]
                and stats["char_count"] > self.MIN_CHAR_COUNT * 2):
            quality.is_low_quality = True
            quality.reasons.append(
                f"中文字符占比 {stats['chinese_ratio']:.1%} 过低"
            )

        # 检查：噪音占比过高
        if stats["noise_ratio"] > self.MAX_NOISE_RATIO and stats["char_count"] > 50:
            quality.is_low_quality = True
            quality.reasons.append(
                f"噪音字符占比 {stats['noise_ratio']:.1%} 超过阈值 {self.MAX_NOISE_RATIO:.0%}"
            )

        # 检查：URL 过多（可能是收藏夹/书签）
        if stats["url_count"] > self.MAX_URL_COUNT:
            quality.is_low_quality = True
            quality.reasons.append(
                f"URL 数量 {stats['url_count']} 超过阈值 {self.MAX_URL_COUNT}，可能是链接收藏"
            )

        return quality

    def check_chunk_quality(self, chunk_content: str) -> bool:
        """检查单个切片是否可以通过质量过滤

        Returns:
            True = 合格（保留），False = 低质量（跳过）
        """
        if not chunk_content or not chunk_content.strip():
            return False
        cleaned = self.clean_chunk(chunk_content)
        stats = self._compute_stats(cleaned)
        if stats["char_count"] < self.MIN_CHUNK_CHARS:
            return False
        if stats["noise_ratio"] > self.MAX_CHUNK_NOISE_RATIO:
            return False
        return True

    def filter_chunks(self, chunks: List[str]) -> List[str]:
        """过滤低质量切片

        Args:
            chunks: 原始切片列表

        Returns:
            过滤后的切片列表（保留索引顺序）
        """
        return [c for c in chunks if self.check_chunk_quality(c)]

    # ════════════════════════════════════════════
    # 3. 重复检测
    # ════════════════════════════════════════════

    def compute_hash(self, content: str) -> str:
        """计算内容 MD5"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def check_duplicate(
        self,
        content: str,
        user_id: str,
        exclude_document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """检测文档是否与已有文档重复（内容 hash 匹配）

        查询数据库中同用户已处理的文档，匹配 content_hash。

        Args:
            content: 文档内容
            user_id: 当前用户 ID
            exclude_document_id: 排除的文档 ID（更新文档时排除自身）

        Returns:
            {
                "is_duplicate": bool,
                "duplicate_of": Optional[str],  # 重复文档的 ID
                "duplicate_name": Optional[str],  # 重复文档的名称
                "hash": str,
            }
        """
        content_hash = self.compute_hash(content)

        # 构建查询
        from api.models.database import get_db
        db = get_db()

        query = db.client.table("kb_documents") \
            .select("id, name") \
            .eq("user_id", user_id) \
            .eq("content_hash", content_hash) \
            .neq("status", "failed")

        if exclude_document_id:
            query = query.neq("id", exclude_document_id)

        result = query.execute()

        if result.data:
            dup = result.data[0]
            return {
                "is_duplicate": True,
                "duplicate_of": dup["id"],
                "duplicate_name": dup["name"],
                "hash": content_hash,
            }

        return {
            "is_duplicate": False,
            "duplicate_of": None,
            "duplicate_name": None,
            "hash": content_hash,
        }

    # ════════════════════════════════════════════
    # 4. 内部方法
    # ════════════════════════════════════════════

    def _strip_html(self, text: str) -> str:
        """剥离 HTML/XML 标签，保留纯文本"""
        if not text:
            return text
        # 移除注释
        text = _RE_HTML_COMMENT.sub("", text)
        # 移除样式/脚本
        text = _RE_STYLE_SCRIPT.sub("", text)
        # 块级标签 → 换行
        text = _RE_BLOCK_TAGS.sub("\n", text)
        # 移除剩余标签
        text = _RE_HTML_TAG.sub("", text)
        # HTML entity 解码
        for entity, char in _HTML_ENTITIES.items():
            text = text.replace(entity, char)
        text = _RE_NUMERIC_ENTITY.sub(lambda m: chr(int(m.group(1))), text)
        text = _RE_HEX_ENTITY.sub(lambda m: chr(int(m.group(1), 16)), text)
        return text

    def _normalize_unicode(self, text: str) -> str:
        """Unicode 规范化

        - 全角字母/数字 → 半角
        - NFKC 规范化（兼容组合字符）
        - 各类空白字符 → 标准空格或换行
        """
        if not text:
            return text

        # 全角字母/数字/符号 → 半角（保留全角中文标点，如。？！等）
        result = []
        for char in text:
            cp = ord(char)
            # 全角字母/数字（FF01-FF5E 范围）→ 半角（21-7E）
            if 0xFF01 <= cp <= 0xFF5E:
                result.append(chr(cp - 0xFEE0))
            # 全角空格 → 半角空格
            elif cp == 0x3000:
                result.append(" ")
            else:
                result.append(char)
        text = "".join(result)

        # NFKC 规范化
        text = unicodedata.normalize("NFKC", text)

        return text

    def _remove_noise(self, text: str) -> str:
        """移除/替换各类噪音内容

        噪音包括：
        - URL 链接（保留域名可读文本）
        - 邮箱地址
        - 电话号码
        - IP 地址
        - 文件路径痕迹
        - 连续分隔线
        - Markdown 图片标记（保留方括号内描述文本）
        """
        if not text:
            return text

        # Markdown 图片 ![](url) → [图片描述]
        text = _RE_MD_IMAGE.sub(r"[图片: \1]", text)

        # Markdown 链接 [文本](url) → 文本（保留链接显示文本）
        text = _RE_MD_LINK.sub(r"\1", text)

        # URL → 替换为 [链接]
        text = _RE_URL.sub("[链接]", text)

        # 纯域名（与上下文无关的）→ 替换
        text = _RE_DOMAIN.sub("[域名]", text)

        # 邮箱 → 替换
        text = _RE_EMAIL.sub("[邮箱]", text)

        # 手机号 → 替换
        text = _RE_PHONE_CN.sub("[电话]", text)

        # 固话 → 替换
        text = _RE_PHONE_LANDLINE.sub("[电话]", text)

        # IP 地址 → 替换
        text = _RE_IPV4.sub("[IP]", text)

        # 文件路径 → 替换
        text = _RE_FILE_PATH.sub("[文件路径]", text)

        # 连续分隔线 → 移除
        text = _RE_SEPARATORS.sub("\n", text)

        return text

    def _beautify(self, text: str) -> str:
        """文本美化：行首尾空白、空行合并、连续空格"""
        if not text:
            return text
        # 行首/行尾空白
        text = _RE_LINE_WS.sub("", text)
        # 合并空行
        text = _RE_EMPTY_LINES.sub("\n\n", text)
        # 连续空格 → 单个空格
        text = _RE_CONSECUTIVE_SPACES.sub(" ", text)
        return text.strip()

    def _compute_stats(self, text: str) -> Dict[str, Any]:
        """计算文本统计信息"""
        total = len(text)
        if total == 0:
            return {
                "char_count": 0,
                "chinese_ratio": 0.0,
                "noise_ratio": 0.0,
                "url_count": 0,
                "is_english_dominant": False,
            }

        # 统计有效字符（非空白、非噪音）
        cjk_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf")
        noise_chars = sum(1 for c in text if c in '●■◆▲▼※→←↑↓□○◎☆★◇◆＠＃＄％＾＆＊')
        noise_chars += len(_RE_URL.findall(text)) * 20  # URL 自身字符也算噪音
        noise_chars += len(_RE_EMAIL.findall(text)) * 15
        noise_chars += len(_RE_PHONE_CN.findall(text)) * 11

        # 不包含空白字符的"有效"总字数
        non_ws_chars = sum(1 for c in text if not c.isspace())

        # 英文占比评估：统计字母数量
        alpha_count = sum(1 for c in text if c.isascii() and c.isalpha())
        is_english_dominant = (
            alpha_count > cjk_chars * 2 and alpha_count > 100
        )

        # URL 计数
        url_count = len(_RE_URL.findall(text))

        return {
            "char_count": non_ws_chars,
            "chinese_ratio": cjk_chars / max(total, 1),
            "noise_ratio": min(noise_chars / max(non_ws_chars, 1), 1.0),
            "url_count": url_count,
            "is_english_dominant": is_english_dominant,
        }


# ── 单例 ─────────────────────────────────────

_cleaner = None


def get_data_cleaner() -> DataCleaner:
    """获取数据清洗器单例"""
    global _cleaner
    if _cleaner is None:
        _cleaner = DataCleaner()
    return _cleaner
