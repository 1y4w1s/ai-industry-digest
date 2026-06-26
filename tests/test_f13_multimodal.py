"""
F-13 单元测试：多模态支持（图片提取 + 描述生成）

测试策略：
  - 纯函数测试：ImageExtractor 输出格式、ImageCaptionService 描述格式
  - 边界测试：空文档、无图片文档、OCR 不可用时的降级行为
  - 注：真实图片提取需要实际的 PDF/DOCX 文件，单元测试不进行

由于 ImageExtractor 需要实际的 PDF/DOCX 文件来提取图片，
本测试文件主要覆盖：
  1. 服务构造函数、输出格式、降级逻辑
  2. describe_batch 批量处理逻辑
  3. 集成后的 content 追加逻辑
"""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from api.services.image_extractor import ImageExtractor, get_image_extractor
from api.services.image_caption import ImageCaptionService, get_image_caption_service


class TestImageExtractor:
    """ImageExtractor 单元测试"""

    def test_init_default_output_dir(self):
        """默认输出目录应为 uploads/images"""
        extractor = ImageExtractor()
        assert "uploads" in extractor._output_dir
        assert "images" in extractor._output_dir

    def test_init_custom_output_dir(self):
        """自定义输出目录"""
        extractor = ImageExtractor(output_dir="/custom/path")
        assert extractor._output_dir == "/custom/path"

    def test_extract_from_pdf_no_fitz(self, tmp_path):
        """缺少 fitz 时返回空列表"""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("fake pdf")
        
        extractor = ImageExtractor(output_dir=str(tmp_path))
        result = extractor.extract_from_pdf(str(pdf_path), "doc-1")
        assert result == []

    def test_extract_from_pdf_exception(self, tmp_path):
        """PDF 提取异常时返回空列表"""
        pdf_path = tmp_path / "invalid.pdf"
        pdf_path.write_bytes(b"not a real pdf")
        
        extractor = ImageExtractor(output_dir=str(tmp_path))
        result = extractor.extract_from_pdf(str(pdf_path), "doc-1")
        assert result == []

    def test_extract_from_docx_no_docx(self, tmp_path):
        """缺少 python-docx 时返回空列表"""
        docx_path = tmp_path / "test.docx"
        docx_path.write_text("fake docx")
        
        extractor = ImageExtractor(output_dir=str(tmp_path))
        result = extractor.extract_from_docx(str(docx_path), "doc-2")
        assert result == []

    def test_singleton(self):
        """get_image_extractor 返回单例"""
        e1 = get_image_extractor()
        e2 = get_image_extractor()
        assert e1 is e2


class TestImageCaptionService:
    """ImageCaptionService 单元测试"""

    def test_init_ocr_check(self):
        """初始化时检查 OCR 可用性"""
        captioner = ImageCaptionService()
        assert hasattr(captioner, "_ocr_available")

    def test_ocr_check_no_tesseract(self):
        """tesseract 不可用时 _ocr_available 为 False"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            captioner = ImageCaptionService()
            assert captioner._ocr_available is False

    def test_describe_ocr_available_with_text(self, tmp_path):
        """OCR 可用且提取到文字时返回 OCR 文本"""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image")
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=True):
            with patch.object(ImageCaptionService, "_ocr", return_value="OCR result"):
                captioner = ImageCaptionService()
                result = captioner.describe(str(img_path), "context")
                assert result == "OCR result"

    def test_describe_ocr_available_no_text(self, tmp_path):
        """OCR 可用但无文字时回退到上下文模式"""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image")
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=True):
            with patch.object(ImageCaptionService, "_ocr", return_value=None):
                captioner = ImageCaptionService()
                result = captioner.describe(str(img_path), "附近有重要图表展示了性能对比")
                assert "重要图表" in result

    def test_describe_ocr_unavailable_with_context(self, tmp_path):
        """OCR 不可用时使用上下文文本"""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image")
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            result = captioner.describe(str(img_path), "本图展示了GPT-4性能对比")
            assert "GPT-4性能对比" in result

    def test_describe_no_context(self, tmp_path):
        """无 OCR 也无上下文时返回通用占位符"""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image")
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            result = captioner.describe(str(img_path), "")
            assert result == "[图片内容]"

    def test_describe_short_context(self, tmp_path):
        """上下文太短时也使用上下文"""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake image")
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            result = captioner.describe(str(img_path), "图")
            assert "图" in result

    def test_describe_batch(self, tmp_path):
        """批量处理返回完整结构"""
        images = [
            {"index": 0, "path": str(tmp_path / "img1.png"), "context_text": "图表1"},
            {"index": 1, "path": str(tmp_path / "img2.png"), "context_text": "图表2"},
        ]
        for img in images:
            open(img["path"], "w").close()
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            results = captioner.describe_batch(images)
            
            assert len(results) == 2
            for r in results:
                assert "description" in r
                assert r["index"] in (0, 1)
                assert r["path"] in (images[0]["path"], images[1]["path"])

    def test_describe_batch_empty(self):
        """空列表返回空"""
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            results = captioner.describe_batch([])
            assert results == []

    def test_singleton(self):
        """get_image_caption_service 返回单例"""
        c1 = get_image_caption_service()
        c2 = get_image_caption_service()
        assert c1 is c2

    def test_ocr_import_error(self, tmp_path):
        """pytesseract 未安装时不崩溃"""
        img_path = tmp_path / "test.png"
        img_path.write_bytes(b"fake")
        
        with patch.object(ImageCaptionService, "_check_ocr", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                captioner = ImageCaptionService()
                # 即使 check_ocr 为 True，_ocr 在 import 失败时应返回 None
                result = captioner._ocr(str(img_path))
                assert result is None


class TestDescribeNormalBehavior:
    """正常场景测试"""

    def test_describe_preserves_description(self):
        """描述文本不应为空字符串"""
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            desc = captioner.describe("/fake/path.png", "上下文文本")
            assert len(desc) > 0

    def test_context_truncation(self):
        """上下文文本过长时截断"""
        long_context = "x" * 300
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            result = captioner.describe("/fake/path.png", long_context)
            # 应该包含上下文文本的一部分（被截断到80字符）
            assert "x" * 80 in result

    def test_batch_result_order(self):
        """批量结果顺序与输入一致"""
        images = [
            {"index": 0, "path": "/a.png", "context_text": "ctx1"},
            {"index": 1, "path": "/b.png", "context_text": "ctx2"},
            {"index": 2, "path": "/c.png", "context_text": "ctx3"},
        ]
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            results = captioner.describe_batch(images)
            assert results[0]["index"] == 0
            assert results[1]["index"] == 1
            assert results[2]["index"] == 2


class TestEdgeCases:
    """边界情况测试"""

    def test_extractor_output_format(self):
        """extract_from_pdf 返回格式检查"""
        extractor = ImageExtractor()
        result = extractor.extract_from_pdf("/fake.pdf", "doc-1")
        assert isinstance(result, list)

    def test_extractor_docx_output_format(self):
        """extract_from_docx 返回格式检查"""
        extractor = ImageExtractor()
        result = extractor.extract_from_docx("/fake.docx", "doc-1")
        assert isinstance(result, list)

    def test_captioner_describe_format(self):
        """describe 返回字符串"""
        with patch.object(ImageCaptionService, "_check_ocr", return_value=False):
            captioner = ImageCaptionService()
            result = captioner.describe("/fake.png", "context")
            assert isinstance(result, str)
