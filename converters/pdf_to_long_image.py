# -*- coding: utf-8 -*-
"""
PDF转长图转换器

该模块提供PDF转长图功能，支持：
- 将PDF所有页面合并为一张长图
- DPI设置
- 页面间隔设置
- 输出格式选择（PNG/JPG）

使用方式：
    from converters.pdf_to_long_image import PdfToLongImageConverter

    converter = PdfToLongImageConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfToLongImageConverter(BaseConverter):
    """
    PDF转长图转换器

    将PDF所有页面垂直拼接为一张长图。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF转长图"
    description = "将PDF所有页面合并为一张长图"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["png", "jpg"]

    def __init__(self):
        """初始化PDF转长图转换器"""
        super().__init__()
        self._dpi = 150
        self._spacing = 0
        self._output_format = "png"

    def set_dpi(self, dpi: int):
        """
        设置DPI

        Args:
            dpi: DPI值（默认150）
        """
        self._dpi = dpi

    def set_spacing(self, spacing: int):
        """
        设置页面间隔

        Args:
            spacing: 间隔像素（默认0）
        """
        self._spacing = spacing

    def set_output_format(self, format_name: str):
        """
        设置输出格式

        Args:
            format_name: 输出格式（png/jpg）
        """
        self._output_format = format_name.lower()

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF转长图

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - dpi: DPI值
                - spacing: 页面间隔像素
                - output_format: 输出格式

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        dpi = kwargs.get('dpi', self._dpi)
        spacing = kwargs.get('spacing', self._spacing)
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
                message=f"正在转换: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行转换
            result = self._convert_to_long_image(input_file, output_dir, dpi, spacing, output_format)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="转换完成"
            )
            self._report_progress(progress)

        return results

    def _convert_to_long_image(self, input_file: Path, output_dir: Path,
                                dpi: int, spacing: int, output_format: str) -> ConversionResult:
        """
        将PDF转换为长图

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            dpi: DPI值
            spacing: 页面间隔
            output_format: 输出格式

        Returns:
            转换结果
        """
        try:
            from pdf2image import convert_from_path
            from PIL import Image

            # 转换PDF为图片列表
            images = convert_from_path(
                str(input_file),
                dpi=dpi,
                thread_count=4
            )

            if not images:
                return ConversionResult(
                    input_file=input_file,
                    status=ConversionStatus.FAILED,
                    error="PDF没有可转换的页面"
                )

            # 计算长图尺寸
            total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
            max_width = max(img.width for img in images)

            # 创建长图画布
            long_image = Image.new('RGB', (max_width, total_height), 'white')

            # 拼接页面
            y_offset = 0
            for img in images:
                # 居中放置
                x_offset = (max_width - img.width) // 2
                long_image.paste(img, (x_offset, y_offset))
                y_offset += img.height + spacing

            # 保存长图
            ext = output_format.lower()
            output_path = output_dir / f"{input_file.stem}_long.{ext}"

            if ext == 'jpg':
                long_image.save(output_path, 'JPEG', quality=95)
            else:
                long_image.save(output_path, 'PNG')

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"长图尺寸: {max_width}x{total_height}"
            )
            logger.info(f"PDF转长图成功: {input_file.name} -> {output_path.name}")
            return result

        except ImportError as e:
            logger.error(f"PDF转长图失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF转长图失败: {input_file.name} - {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )

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