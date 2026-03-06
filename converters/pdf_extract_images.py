# -*- coding: utf-8 -*-
"""
PDF提取图片转换器

该模块提供从PDF中提取内嵌图片的功能，支持：
- 提取PDF中所有嵌入的图片资源
- 最小图片尺寸过滤
- 输出格式选择（PNG/JPG）

使用方式：
    from converters.pdf_extract_images import PdfExtractImagesConverter

    converter = PdfExtractImagesConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfExtractImagesConverter(BaseConverter):
    """
    PDF提取图片转换器

    从PDF文件中提取嵌入的图片资源，支持尺寸过滤和格式选择。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF提取图片"
    description = "从PDF中提取内嵌的图片资源"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["png", "jpg"]

    def __init__(self):
        """初始化PDF提取图片转换器"""
        super().__init__()
        self._min_width = 100
        self._min_height = 100
        self._output_format = "png"

    def set_min_size(self, width: int, height: int):
        """
        设置最小图片尺寸

        Args:
            width: 最小宽度（像素）
            height: 最小高度（像素）
        """
        self._min_width = width
        self._min_height = height

    def set_output_format(self, format_name: str):
        """
        设置输出格式

        Args:
            format_name: 输出格式名称（png/jpg）
        """
        self._output_format = format_name.lower()

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF图片提取

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - min_width: 最小宽度（默认100）
                - min_height: 最小高度（默认100）
                - output_format: 输出格式（默认png）

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        min_width = kwargs.get('min_width', self._min_width)
        min_height = kwargs.get('min_height', self._min_height)
        output_format = kwargs.get('output_format', self._output_format)

        # 确保输出目录存在
        ensure_dir(output_dir)

        total_files = len(input_files)

        for i, input_file in enumerate(input_files):
            if self._check_cancelled():
                break

            # 报告进度
            progress = ConversionProgress(
                current=i + 1,
                total=total_files,
                current_file=input_file.name,
                message=f"正在提取图片: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行提取
            result = self._extract_images(input_file, output_dir, min_width, min_height, output_format)
            results.extend(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="提取完成"
            )
            self._report_progress(progress)

        return results

    def _extract_images(self, input_file: Path, output_dir: Path,
                        min_width: int, min_height: int,
                        output_format: str) -> List[ConversionResult]:
        """
        从单个PDF文件中提取图片

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            min_width: 最小宽度
            min_height: 最小高度
            output_format: 输出格式

        Returns:
            转换结果列表
        """
        results = []

        try:
            import fitz  # PyMuPDF

            # 创建输出子目录
            pdf_output_dir = output_dir / input_file.stem
            ensure_dir(pdf_output_dir)

            doc = fitz.open(str(input_file))
            image_count = 0

            for page_num in range(len(doc)):
                if self._check_cancelled():
                    break

                page = doc[page_num]
                images = page.get_images()

                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    if base_image:
                        # 检查图片尺寸
                        img_width = base_image["width"]
                        img_height = base_image["height"]

                        if img_width >= min_width and img_height >= min_height:
                            # 保存图片
                            image_data = base_image["image"]
                            ext = output_format
                            output_filename = f"{input_file.stem}_p{page_num + 1}_img{img_index + 1}.{ext}"
                            output_path = pdf_output_dir / output_filename

                            with open(output_path, "wb") as f:
                                f.write(image_data)

                            image_count += 1

            doc.close()

            result = ConversionResult(
                input_file=input_file,
                output_file=pdf_output_dir,
                status=ConversionStatus.COMPLETED,
                message=f"提取了 {image_count} 张图片"
            )
            results.append(result)
            logger.info(f"PDF提取图片成功: {input_file.name} -> {image_count} 张图片")

        except ImportError:
            result = ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error="缺少PyMuPDF库，请安装: pip install PyMuPDF"
            )
            results.append(result)
            logger.error(f"PDF提取图片失败: {input_file.name} - 缺少PyMuPDF库")
        except Exception as e:
            result = ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )
            results.append(result)
            logger.error(f"PDF提取图片失败: {input_file.name} - {e}")

        return results

    def validate_input(self, file_path: Path) -> bool:
        """
        验证输入文件

        Args:
            file_path: 文件路径

        Returns:
            如果文件有效返回 True
        """
        if not file_path.exists():
            return False

        return file_path.suffix.lower() == '.pdf'