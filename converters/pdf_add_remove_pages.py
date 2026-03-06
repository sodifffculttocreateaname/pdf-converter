# -*- coding: utf-8 -*-
"""
PDF增删页转换器

该模块提供PDF页面增删功能，支持：
- 删除指定页面
- 插入空白页面
- 页码范围选择

使用方式：
    from converters.pdf_add_remove_pages import PdfAddRemovePagesConverter

    converter = PdfAddRemovePagesConverter()
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


class PdfAddRemovePagesConverter(BaseConverter):
    """
    PDF增删页转换器

    在PDF中添加或删除页面。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF增删页"
    description = "在PDF中添加或删除页面"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 操作模式
    MODE_DELETE = "delete"
    MODE_INSERT = "insert"

    def __init__(self):
        """初始化PDF增删页转换器"""
        super().__init__()
        self._operation = self.MODE_DELETE
        self._pages = ""

    def set_operation(self, operation: str):
        """
        设置操作模式

        Args:
            operation: 操作模式（delete/insert）
        """
        self._operation = operation

    def set_pages(self, pages: str):
        """
        设置页码列表

        Args:
            pages: 页码列表字符串（如 "1,3,5-10"）
        """
        self._pages = pages

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF增删页操作

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - operation: 操作模式（delete/insert）
                - pages: 页码列表字符串

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        operation = kwargs.get('operation', self._operation)
        pages = kwargs.get('pages', self._pages)

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
                message=f"正在处理: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行操作
            if operation == self.MODE_DELETE:
                result = self._delete_pages(input_file, output_dir, pages)
            else:
                result = self._insert_pages(input_file, output_dir, pages)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="处理完成"
            )
            self._report_progress(progress)

        return results

    def _parse_pages(self, pages_str: str, total_pages: int) -> List[int]:
        """
        解析页码字符串

        Args:
            pages_str: 页码字符串（如 "1,3,5-10"）
            total_pages: 总页数

        Returns:
            页码列表（0-based索引）
        """
        pages = []
        if not pages_str.strip():
            return pages

        parts = pages_str.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if '-' in part:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                for p in range(start, min(end + 1, total_pages + 1)):
                    pages.append(p - 1)  # 转为0-based索引
            else:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.append(p - 1)  # 转为0-based索引

        return sorted(set(pages))

    def _delete_pages(self, input_file: Path, output_dir: Path, pages_str: str) -> ConversionResult:
        """
        删除指定页面

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            pages_str: 页码字符串

        Returns:
            转换结果
        """
        try:
            reader = PdfReader(str(input_file))
            total_pages = len(reader.pages)

            pages_to_delete = self._parse_pages(pages_str, total_pages)

            if not pages_to_delete:
                return ConversionResult(
                    input_file=input_file,
                    status=ConversionStatus.FAILED,
                    error="未指定有效的页码"
                )

            writer = PdfWriter()

            for i, page in enumerate(reader.pages):
                if i not in pages_to_delete:
                    writer.add_page(page)

            output_path = output_dir / f"{input_file.stem}_modified.pdf"
            with open(output_path, 'wb') as f:
                writer.write(f)

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"删除了 {len(pages_to_delete)} 页"
            )
            logger.info(f"PDF删除页面成功: {input_file.name} -> 删除 {len(pages_to_delete)} 页")
            return result

        except Exception as e:
            logger.error(f"PDF删除页面失败: {input_file.name} - {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )

    def _insert_pages(self, input_file: Path, output_dir: Path, pages_str: str) -> ConversionResult:
        """
        在指定位置插入空白页

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            pages_str: 页码字符串（指定插入位置）

        Returns:
            转换结果
        """
        try:
            reader = PdfReader(str(input_file))
            writer = PdfWriter()

            total_pages = len(reader.pages)
            insert_positions = self._parse_pages(pages_str, total_pages + 1)  # 允许在末尾插入

            insert_count = 0
            for i, page in enumerate(reader.pages):
                # 在当前页之前插入空白页
                if i in insert_positions:
                    writer.add_blank_page(width=page.mediabox.width, height=page.mediabox.height)
                    insert_count += 1
                writer.add_page(page)

            # 在最后一页之后插入
            if total_pages in insert_positions:
                last_page = reader.pages[-1]
                writer.add_blank_page(width=last_page.mediabox.width, height=last_page.mediabox.height)
                insert_count += 1

            output_path = output_dir / f"{input_file.stem}_modified.pdf"
            with open(output_path, 'wb') as f:
                writer.write(f)

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"插入了 {insert_count} 页空白页"
            )
            logger.info(f"PDF插入页面成功: {input_file.name} -> 插入 {insert_count} 页")
            return result

        except Exception as e:
            logger.error(f"PDF插入页面失败: {input_file.name} - {e}")
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