"""
图片提取服务（F-13 多模态支持）

功能：
  1. 从 PDF 中提取嵌入的图片（PyMuPDF）
  2. 从 DOCX 中提取嵌入的图片（python-docx）
  3. 保存图片到 uploads/images/ 目录
  4. 返回 [图片索引, 保存路径, 上下文文本] 列表

设计原则：
  - 所有提取异常被捕获并降级（不影响主流程）
  - 图片保存为 PNG 格式
  - 输出路径统一管理
"""

import os
import uuid
from typing import List, Dict, Optional, Tuple


class ImageExtractor:
    """从文档文件中提取嵌入图片"""

    def __init__(self, output_dir: str = None):
        if output_dir is None:
            base = os.path.join(os.path.dirname(__file__), "..", "uploads", "images")
        else:
            base = output_dir
        self._output_dir = base

    def extract_from_pdf(self, pdf_path: str, document_id: str) -> List[Dict]:
        """
        从 PDF 中提取图片
        
        返回:
            [{index, path, page, context_text}, ...]
        """
        images = []
        doc_dir = os.path.join(self._output_dir, document_id)
        os.makedirs(doc_dir, exist_ok=True)

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 提取当前页的上下文文本
                page_text = page.get_text().strip()[:200]

                # 方法1: 提取内嵌图片
                image_list = page.get_images(full=True)
                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    img_filename = f"p{page_num + 1}_i{img_idx}_{uuid.uuid4().hex[:8]}.png"
                    img_path = os.path.join(doc_dir, img_filename)
                    
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)

                    images.append({
                        "index": len(images),
                        "path": img_path,
                        "page": page_num + 1,
                        "context_text": page_text,
                        "format": base_image.get("ext", "png"),
                    })

            doc.close()
        except ImportError:
            print("[ImageExtractor] 缺少 PyMuPDF 依赖")
        except Exception as e:
            print(f"[ImageExtractor] PDF 图片提取失败: {e}")

        return images

    def extract_from_docx(self, docx_path: str, document_id: str) -> List[Dict]:
        """
        从 DOCX 中提取图片
        
        返回:
            [{index, path, page, context_text}, ...]
        """
        images = []
        doc_dir = os.path.join(self._output_dir, document_id)
        os.makedirs(doc_dir, exist_ok=True)

        try:
            from docx import Document
            from docx.opc.constants import RELATIONSHIP_TYPE as RT
            import io

            doc = Document(docx_path)

            # DOCX 中图片是嵌入在 run 中的 inline shape
            # 使用 rels 提取所有图片
            img_rel_count = 0
            for rel in doc.part.rels.values():
                if "image" in rel.reltype:
                    img_rel_count += 1

            # 遍历段落，提取 inline 图片
            para_index = 0
            for para in doc.paragraphs:
                para_text = para.text.strip()[:200]
                for run in para.runs:
                    # 检查 run 中的 drawing 元素
                    drawing_elements = run._element.findall(
                        './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing'
                    )
                    for drawing in drawing_elements:
                        # 找到 blip 元素获取图片引用
                        blips = drawing.findall(
                            './/{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
                        )
                        for blip in blips:
                            embed_id = blip.get(
                                '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
                            )
                            if embed_id:
                                try:
                                    image_part = doc.part.related_parts[embed_id]
                                    image_bytes = image_part.blob
                                    
                                    img_filename = f"docx_p{para_index + 1}_{uuid.uuid4().hex[:8]}.png"
                                    img_path = os.path.join(doc_dir, img_filename)
                                    
                                    with open(img_path, "wb") as f:
                                        f.write(image_bytes)

                                    images.append({
                                        "index": len(images),
                                        "path": img_path,
                                        "page": para_index + 1,
                                        "context_text": para_text,
                                        "format": "png",
                                    })
                                except Exception:
                                    pass

                para_index += 1

        except ImportError:
            print("[ImageExtractor] 缺少 python-docx 依赖")
        except Exception as e:
            print(f"[ImageExtractor] DOCX 图片提取失败: {e}")

        return images


# 单例
_extractor = None


def get_image_extractor() -> ImageExtractor:
    global _extractor
    if _extractor is None:
        _extractor = ImageExtractor()
    return _extractor
