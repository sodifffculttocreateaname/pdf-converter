# -*- coding: utf-8 -*-
"""
PDF拆分转换器
"""
from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfSplitConverter(BaseConverter):
    """PDF拆分转换器"""

    name = "PDF拆分"
    description = "将PDF文件拆分为单页或多页文件"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 拆分模式
    MODE_SINGLE_PAGE = "single"      # 每页一个文件
    MODE_PAGE_RANGE = "range"        # 按页码范围拆分
    MODE_EVEN_ODD = "even_odd"       # 奇偶页拆分

    def __init__(self):
        super().__init__()
        self._split_mode = self.MODE_SINGLE_PAGE
        self._page_ranges = []  # 页码范围列表，如 [(1, 3), (4, 6)]

    def set_split_mode(self, mode: str):
        """设置拆分模式"""
        self._split_mode = mode

    def set_page_ranges(self, ranges: List[tuple]):
        """设置页码范围"""
        self._page_ranges = ranges

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF拆分

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数 (mode, ranges)

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        mode = kwargs.get('mode', self._split_mode)
        ranges = kwargs.get('ranges', self._page_ranges)

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
                message=f"正在拆分: {input_file.name}"
            )
            self._report_progress(progress)

            if mode == self.MODE_SINGLE_PAGE:
                file_results = self._split_single_pages(input_file, output_dir)
            elif mode == self.MODE_PAGE_RANGE:
                file_results = self._split_by_ranges(input_file, output_dir, ranges)
            elif mode == self.MODE_EVEN_ODD:
                file_results = self._split_even_odd(input_file, output_dir)
            else:
                file_results = [ConversionResult(
                    input_file=input_file,
                    status=ConversionStatus.FAILED,
                    error=f"未知的拆分模式: {mode}"
                )]

            results.extend(file_results)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="拆分完成"
            )
            self._report_progress(progress)

        return results

    def _split_single_pages(self, input_file: Path, output_dir: Path) -> List[ConversionResult]:
        """
        将PDF拆分为单页文件

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录

        Returns:
            转换结果列表
        """
        results = []

        try:
            # 创建输出子目录
            pdf_output_dir = output_dir / input_file.stem
            ensure_dir(pdf_output_dir)

            reader = PdfReader(str(input_file))
            total_pages = len(reader.pages)

            for page_num in range(total_pages):
                if self._check_cancelled():
                    break

                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])

                output_filename = f"{input_file.stem}_page_{page_num + 1:03d}.pdf"
                output_path = pdf_output_dir / output_filename

                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                result = ConversionResult(
                    input_file=input_file,
                    output_file=output_path,
                    status=ConversionStatus.COMPLETED,
                    message=f"第 {page_num + 1} 页"
                )
                results.append(result)

            logger.info(f"PDF拆分成功(单页): {input_file.name} -> {total_pages} 个文件")

        except Exception as e:
            result = ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )
            results.append(result)
            logger.error(f"PDF拆分失败: {input_file.name} - {e}")

        return results

    def _split_by_ranges(self, input_file: Path, output_dir: Path,
                         ranges: List[tuple]) -> List[ConversionResult]:
        """
        按页码范围拆分PDF

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            ranges: 页码范围列表 [(开始页, 结束页), ...]

        Returns:
            转换结果列表
        """
        results = []

        try:
            reader = PdfReader(str(input_file))
            total_pages = len(reader.pages)

            # 如果没有指定范围，使用默认范围
            if not ranges:
                ranges = [(1, total_pages)]

            for i, (start, end) in enumerate(ranges):
                if self._check_cancelled():
                    break

                # 验证范围
                start = max(1, start)
                end = min(total_pages, end)

                if start > end:
                    continue

                writer = PdfWriter()

                for page_num in range(start - 1, end):
                    writer.add_page(reader.pages[page_num])

                output_filename = f"{input_file.stem}_pages_{start}-{end}.pdf"
                output_path = output_dir / output_filename

                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                result = ConversionResult(
                    input_file=input_file,
                    output_file=output_path,
                    status=ConversionStatus.COMPLETED,
                    message=f"第 {start}-{end} 页"
                )
                results.append(result)

            logger.info(f"PDF拆分成功(范围): {input_file.name} -> {len(results)} 个文件")

        except Exception as e:
            result = ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )
            results.append(result)
            logger.error(f"PDF拆分失败: {input_file.name} - {e}")

        return results

    def _split_even_odd(self, input_file: Path, output_dir: Path) -> List[ConversionResult]:
        """
        将PDF拆分为奇数页和偶数页

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录

        Returns:
            转换结果列表
        """
        results = []

        try:
            reader = PdfReader(str(input_file))
            total_pages = len(reader.pages)

            # 奇数页
            odd_writer = PdfWriter()
            # 偶数页
            even_writer = PdfWriter()

            for page_num in range(total_pages):
                if (page_num + 1) % 2 == 1:  # 奇数页
                    odd_writer.add_page(reader.pages[page_num])
                else:  # 偶数页
                    even_writer.add_page(reader.pages[page_num])

            # 保存奇数页
            if len(odd_writer.pages) > 0:
                odd_path = output_dir / f"{input_file.stem}_odd.pdf"
                with open(odd_path, 'wb') as f:
                    odd_writer.write(f)
                results.append(ConversionResult(
                    input_file=input_file,
                    output_file=odd_path,
                    status=ConversionStatus.COMPLETED,
                    message=f"奇数页 ({len(odd_writer.pages)} 页)"
                ))

            # 保存偶数页
            if len(even_writer.pages) > 0:
                even_path = output_dir / f"{input_file.stem}_even.pdf"
                with open(even_path, 'wb') as f:
                    even_writer.write(f)
                results.append(ConversionResult(
                    input_file=input_file,
                    output_file=even_path,
                    status=ConversionStatus.COMPLETED,
                    message=f"偶数页 ({len(even_writer.pages)} 页)"
                ))

            logger.info(f"PDF拆分成功(奇偶): {input_file.name} -> 2 个文件")

        except Exception as e:
            result = ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )
            results.append(result)
            logger.error(f"PDF拆分失败: {input_file.name} - {e}")

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