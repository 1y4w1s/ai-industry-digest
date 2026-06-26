"""
元数据增强服务：为文档切片生成丰富的 metadata 信息

改造前 metadata:  {"length": len(chunk)}
改造后 metadata:  {
    "length": len(chunk),
    "chunk_index": i,
    "total_chunks": N,
    "document_name": "...",
    "file_type": "markdown",
    "section_title": "2.1 Transformer 架构",
    "section_depth": 2,
    "has_code": False,
    "code_language": "",
    "extracted_entities": ["Transformer", "Attention"],
    "page_number": 0,
}
"""

import re
from typing import List, Dict, Any, Optional


class MetadataEnricher:
    """文档切片元数据增强器"""
    
    # markdown 标题正则
    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    
    # 代码围栏正则
    _FENCE_PATTERN = re.compile(r"```(\w*)\n", re.DOTALL)
    
    def enrich(
        self,
        chunk_content: str,
        *,
        chunk_index: int = 0,
        total_chunks: int = 1,
        document_name: str = "",
        file_type: str = "markdown",
        full_document: str = "",
        extracted_entities: Optional[List[str]] = None,
        page_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        对单个切片进行元数据增强
        
        参数:
            chunk_content: 切片文本内容
            chunk_index: 切片序号（从 0 开始）
            total_chunks: 总切片数
            document_name: 文档名称
            file_type: 文件类型（markdown / pdf / docx / txt）
            full_document: 完整的原始文档文本（用于推导章节上下文）
            extracted_entities: 文档级别已提取的实体列表
            page_number: 页码（仅 PDF 来源的切片有此信息）
        
        返回:
            增强后的 metadata 字典，所有字段不为 None
        """
        metadata: Dict[str, Any] = {}
        
        # 1. 基础信息
        metadata["length"] = len(chunk_content)
        metadata["chunk_index"] = chunk_index
        metadata["total_chunks"] = total_chunks
        metadata["document_name"] = document_name or ""
        metadata["file_type"] = file_type or "markdown"
        
        # 2. 章节信息
        section_title, section_depth = self._extract_section_info(
            chunk_content, full_document, chunk_index, total_chunks
        )
        metadata["section_title"] = section_title
        metadata["section_depth"] = section_depth
        
        # 3. 代码块检测
        has_code, code_language = self._detect_code_block(chunk_content)
        metadata["has_code"] = has_code
        metadata["code_language"] = code_language if code_language else ""
        
        # 4. 实体信息（去重）
        if extracted_entities:
            seen = set()
            chunk_entities = []
            for e in extracted_entities:
                if e.lower() in chunk_content.lower() and e not in seen:
                    seen.add(e)
                    chunk_entities.append(e)
            metadata["extracted_entities"] = chunk_entities
        else:
            metadata["extracted_entities"] = []
        
        # 5. 页码信息
        metadata["page_number"] = page_number if page_number is not None else 0
        
        return metadata
    
    def _extract_section_info(
        self,
        chunk_content: str,
        full_document: str,
        chunk_index: int,
        total_chunks: int = 1,
    ) -> tuple:
        """
        从文档中提取最近的章节标题和层级
        
        策略：
        1. 先检查 chunk 自身是否包含标题
        2. 如果 chunk 不包含标题，从 full_document 中寻找出现在 chunk 之前的最近标题
        3. 如果都没有，返回空
        """
        # 先检查 chunk 自身是否包含标题
        chunk_heading = self._HEADING_PATTERN.search(chunk_content)
        if chunk_heading:
            depth = len(chunk_heading.group(1))
            title = chunk_heading.group(2).strip()
            return title, depth
        
        # 再从 full_document 中搜索
        if not full_document:
            return "", 0
        
        headings = list(self._HEADING_PATTERN.finditer(full_document))
        if not headings:
            return "", 0
        
        # 通过 chunk_index 估算切片在文档中的大致位置
        # 估算方式：假设文档均匀切片，chunk_index / total_chunks ≈ 字符偏移比例
        if chunk_index > 0 and headings:
            total_chars = len(full_document)
            # 估算当前切片的起始字符偏移
            estimated_offset = int(total_chars * chunk_index / max(total_chunks, 1))
            
            # 找出现在估算位置之前的最近标题
            closest_heading = None
            closest_distance = float("inf")
            for h in headings:
                dist = estimated_offset - h.start()
                if 0 <= dist < closest_distance:
                    closest_distance = dist
                    closest_heading = h
            
            if closest_heading:
                depth = len(closest_heading.group(1))
                title = closest_heading.group(2).strip()
                return title, depth
        
        # 取第一个标题作为当前切片的上下文
        h = headings[0]
        depth = len(h.group(1))
        title = h.group(2).strip()
        return title, depth
    
    def _detect_code_block(self, content: str) -> tuple:
        """
        检测内容中是否包含代码块
        
        返回:
            (has_code: bool, language: Optional[str])
            - has_code: 是否包含 ``` 围栏代码块
            - language: 代码语言（如 "python"、"javascript"），无标注时为 "unknown"
            - 行内 `code` 不视为代码块
        """
        if not content:
            return False, None
        
        match = self._FENCE_PATTERN.search(content)
        if match:
            lang = match.group(1).strip()
            return True, lang if lang else "unknown"
        
        return False, None


# 单例
_enricher = None


def get_metadata_enricher() -> MetadataEnricher:
    """获取元数据增强器单例"""
    global _enricher
    if _enricher is None:
        _enricher = MetadataEnricher()
    return _enricher
