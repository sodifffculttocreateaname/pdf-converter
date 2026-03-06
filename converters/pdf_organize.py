# -*- coding: utf-8 -*-
"""
PDF编排转换器

该模块提供PDF页面编排功能，支持：
- 调整页面顺序
- 复制页面
- 删除页面

使用方式：
    from converters.pdf_organize import PdfOrganizeConverter

    converter = PdfOrganizeConverter()
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


class PdfOrganizeConverter(BaseConverter):
    """
    PDF编排转换器

    调整PDF页面的顺序，支持复制和删除。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF编排页面"
    description = "调整PDF页面顺序、复制、删除"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        """初始化PDF编排转换器"""
        super().__init__()
        self._page_order = []

    def set_page_order(self, order: List[int]):
        """
        设置页面顺序

        Args:
            order: 页面顺序列表（1-based），如 [3, 1, 2, 5, 4]
                   支持重复页码表示复制，如 [1, 1, 2, 3] 表示复制第1页
        """
        self._page_order = order

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF编排

        Args:
            input_files: 输入PDF文件列表（仅处理第一个文件）
            output_dir: 输出目录
            **kwargs: 额外参数
                - page_order: 页面顺序列表

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        page_order = kwargs.get('page_order', self._page_order)

        # PDF编排通常只处理单个文件
        if not input_files:
            return results

        input_file = input_files[0]

        if self._check_cancelled():
            return results

        # 报告进度
        progress = ConversionProgress(
            current=1,
            total=1,
            current_file=input_file.name,
            message=f"正在编排: {input_file.name}"
        )
        self._report_progress(progress)

        # 确保输出目录存在
        ensure_dir(output_dir)

        # 执行编排
        result = self._organize_pdf(input_file, output_dir, page_order)
        results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=1,
                total=1,
                message="编排完成"
            )
            self._report_progress(progress)

        return results

    def _organize_pdf(self, input_file: Path, output_dir: Path,
                      page_order: List[int]) -> ConversionResult:
        """
        编排PDF页面

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            page_order: 页面顺序列表（1-based）

        Returns:
            转换结果
        """
        try:
            reader = PdfReader(str(input_file))
            writer = PdfWriter()
            total_pages = len(reader.pages)

            if not page_order:
                # 如果没有指定顺序，按原样输出
                for page in reader.pages:
                    writer.add_page(page)
            else:
                # 按指定顺序添加页面
                for page_num in page_order:
                    if 1 <= page_num <= total_pages:
                        writer.add_page(reader.pages[page_num - 1])

            output_path = output_dir / f"{input_file.stem}_organized.pdf"
            with open(output_path, 'wb') as f:
                writer.write(f)

            new_page_count = len(writer.pages)
            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"编排完成，共 {new_page_count} 页"
            )
            logger.info(f"PDF编排成功: {input_file.name} -> {new_page_count} 页")
            return result

        except Exception as e:
            logger.error(f"PDF编排失败: {input_file.name} - {e}")
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