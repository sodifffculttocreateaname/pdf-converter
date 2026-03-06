# -*- coding: utf-8 -*-
"""
PDF旋转转换器

该模块提供PDF页面旋转功能，支持：
- 旋转角度选择：90°、180°、270°
- 页码范围选择

使用方式：
    from converters.pdf_rotate import PdfRotateConverter

    converter = PdfRotateConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfRotateConverter(BaseConverter):
    """
    PDF旋转转换器

    旋转PDF页面的角度。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF旋转页面"
    description = "旋转PDF页面（90°/180°/270°）"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        """初始化PDF旋转转换器"""
        super().__init__()
        self._rotate_angle = 90

    def set_rotate_angle(self, angle: int):
        """
        设置旋转角度

        Args:
            angle: 旋转角度（90/180/270）
        """
        if angle in [90, 180, 270]:
            self._rotate_angle = angle
        else:
            raise ValueError("旋转角度必须是 90、180 或 270")

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF旋转

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - rotate_angle: 旋转角度（90/180/270）
                - page_range: 页码范围（如 "1-5,8,10-12" 或 "all"）

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        rotate_angle = kwargs.get('rotate_angle', self._rotate_angle)
        page_range = kwargs.get('page_range', 'all')

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
                message=f"正在旋转: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行旋转
            result = self._rotate_pdf(input_file, output_dir, rotate_angle, page_range)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="旋转完成"
            )
            self._report_progress(progress)

        return results

    def _parse_page_range(self, range_str: str, total_pages: int) -> List[int]:
        """
        解析页码范围字符串

        Args:
            range_str: 页码范围字符串（如 "1-5,8,10-12" 或 "all"）
            total_pages: 总页数

        Returns:
            页码列表（0-based索引）
        """
        if range_str.lower() == 'all' or not range_str.strip():
            return list(range(total_pages))

        pages = []
        parts = range_str.split(',')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if '-' in part:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                for p in range(start, min(end + 1, total_pages + 1)):
                    pages.append(p - 1)
            else:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.append(p - 1)

        return sorted(set(pages))

    def _rotate_pdf(self, input_file: Path, output_dir: Path,
                    angle: int, page_range: str) -> ConversionResult:
        """
        旋转PDF页面

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            angle: 旋转角度
            page_range: 页码范围

        Returns:
            转换结果
        """
        try:
            reader = PdfReader(str(input_file))
            writer = PdfWriter()
            total_pages = len(reader.pages)

            pages_to_rotate = self._parse_page_range(page_range, total_pages)
            rotate_count = 0

            for i, page in enumerate(reader.pages):
                if i in pages_to_rotate:
                    # 旋转页面
                    rotated_page = page
                    rotated_page.rotate(angle)
                    writer.add_page(rotated_page)
                    rotate_count += 1
                else:
                    writer.add_page(page)

            output_path = output_dir / f"{input_file.stem}_rotated.pdf"
            with open(output_path, 'wb') as f:
                writer.write(f)

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"旋转了 {rotate_count} 页（{angle}°）"
            )
            logger.info(f"PDF旋转成功: {input_file.name} -> 旋转 {rotate_count} 页")
            return result

        except Exception as e:
            logger.error(f"PDF旋转失败: {input_file.name} - {e}")
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