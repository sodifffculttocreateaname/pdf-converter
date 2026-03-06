# -*- coding: utf-8 -*-
"""
发票合并转换器

该模块提供发票PDF合并功能，支持：
- 合并多个发票PDF文件
- 按添加顺序排列

使用方式：
    from converters.invoice_merge import InvoiceMergeConverter

    converter = InvoiceMergeConverter()
    results = converter.convert([Path("invoice1.pdf"), Path("invoice2.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class InvoiceMergeConverter(BaseConverter):
    """
    发票合并转换器

    合并多个发票PDF文件。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "发票合并"
    description = "合并多个发票PDF文件"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        """初始化发票合并转换器"""
        super().__init__()
        self._output_filename = "merged_invoices.pdf"

    def set_output_filename(self, filename: str):
        """
        设置输出文件名

        Args:
            filename: 输出文件名（不含路径）
        """
        self._output_filename = filename

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行发票合并

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - output_filename: 输出文件名

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        output_filename = kwargs.get('output_filename', self._output_filename)

        if not input_files:
            return results

        if self._check_cancelled():
            return results

        # 确保输出目录存在
        ensure_dir(output_dir)

        # 报告进度
        progress = ConversionProgress(
            current=0,
            total=len(input_files),
            message="正在合并发票..."
        )
        self._report_progress(progress)

        # 执行合并
        result = self._merge_invoices(input_files, output_dir, output_filename)
        results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=len(input_files),
                total=len(input_files),
                message="合并完成"
            )
            self._report_progress(progress)

        return results

    def _merge_invoices(self, input_files: List[Path], output_dir: Path,
                        output_filename: str) -> ConversionResult:
        """
        合并发票PDF

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            output_filename: 输出文件名

        Returns:
            转换结果
        """
        try:
            writer = PdfWriter()
            merged_count = 0

            for i, input_file in enumerate(input_files):
                if self._check_cancelled():
                    break

                try:
                    reader = PdfReader(str(input_file))

                    # 添加所有页面
                    for page in reader.pages:
                        writer.add_page(page)

                    merged_count += 1

                    # 报告进度
                    progress = ConversionProgress(
                        current=i + 1,
                        total=len(input_files),
                        current_file=input_file.name,
                        message=f"正在合并: {input_file.name}"
                    )
                    self._report_progress(progress)

                except Exception as e:
                    logger.warning(f"合并文件失败，跳过: {input_file.name} - {e}")
                    continue

            # 保存合并后的PDF
            if merged_count > 0:
                output_path = output_dir / output_filename
                with open(output_path, 'wb') as f:
                    writer.write(f)

                result = ConversionResult(
                    input_file=input_files[0],  # 使用第一个文件作为代表
                    output_file=output_path,
                    status=ConversionStatus.COMPLETED,
                    message=f"成功合并 {merged_count} 个发票文件"
                )
                logger.info(f"发票合并成功: 合并 {merged_count} 个文件 -> {output_path.name}")
                return result
            else:
                return ConversionResult(
                    input_file=input_files[0] if input_files else Path(""),
                    status=ConversionStatus.FAILED,
                    error="没有可合并的文件"
                )

        except Exception as e:
            logger.error(f"发票合并失败: {e}")
            return ConversionResult(
                input_file=input_files[0] if input_files else Path(""),
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