"""
图片描述生成服务（F-13 多模态支持）

功能：
  1. OCR 模式: 使用 pytesseract 提取图片中的文字
  2. 上下文模式: 使用图片在文档中的上下文文本生成描述
  3. 降级策略: OCR 不可用时 -> 上下文模式 -> 通用占位符

设计原则：
  - 零硬依赖: OCR 为可选功能，不阻塞主流程
  - 所有异常被捕获并降级
  - 输出格式统一为字符串
"""

import os
import subprocess
from typing import List, Dict, Optional


class ImageCaptionService:
    """图片描述生成器"""

    def __init__(self):
        self._ocr_available = self._check_ocr()

    def _check_ocr(self) -> bool:
        """检测 OCR 是否可用（pytesseract + tesseract 命令行）"""
        try:
            import pytesseract
            # 验证 tesseract 命令可用
            subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                timeout=3,
            )
            return True
        except Exception:
            return False

    def describe(self, image_path: str, context_text: str = "") -> str:
        """
        生成图片描述
        
        优先级: OCR > 上下文模式 > 通用占位符
        """
        # 优先使用 OCR
        if self._ocr_available:
            ocr_text = self._ocr(image_path)
            if ocr_text:
                return ocr_text

        # 使用上下文文本
        if context_text and len(context_text) > 10:
            return f"[图片内容: 位于上下文 '{context_text[:80]}' 附近]"

        # 通用占位符
        return "[图片内容]"

    def _ocr(self, image_path: str) -> Optional[str]:
        """使用 pytesseract 执行 OCR"""
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            text = text.strip()
            if text:
                return text
        except Exception as e:
            print(f"[ImageCaptionService] OCR 失败: {e}")
        return None

    def describe_batch(self, images: List[Dict]) -> List[Dict]:
        """
        批量生成图片描述
        
        输入: [{path, context_text, ...}, ...]
        输出: [{..., "description": str}, ...]
        """
        results = []
        for img in images:
            desc = self.describe(img["path"], img.get("context_text", ""))
            results.append({**img, "description": desc})
        return results


# 单例
_captioner = None


def get_image_caption_service() -> ImageCaptionService:
    global _captioner
    if _captioner is None:
        _captioner = ImageCaptionService()
    return _captioner
