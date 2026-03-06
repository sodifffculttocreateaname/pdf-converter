# -*- coding: utf-8 -*-
"""
PDF合并转换器
"""
from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir, get_unique_filename
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfMergeConverter(BaseConverter):
    """PDF合并转换器"""

    name = "PDF合并"
    description = "将多个PDF文件合并为一个PDF"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        super().__init__()

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF合并

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数 (output_filename)

        Returns:
            转换结果列表
        """
        results = []

        # 确保输出目录存在
        ensure_dir(output_dir)

        if len(input_files) < 2:
            result = ConversionResult(
                input_file=input_files[0] if input_files else Path(""),
                status=ConversionStatus.FAILED,
                error="合并至少需要2个PDF文件"
            )
            results.append(result)
            return results

        # 报告开始进度
        progress = ConversionProgress(
            current=0,
            total=len(input_files),
            message="正在合并PDF文件..."
        )
        self._report_progress(progress)

        result = ConversionResult(input_file=input_files[0])

        try:
            writer = PdfWriter()
            total_pages = 0

            for i, input_file in enumerate(input_files):
                if self._check_cancelled():
                    break

                # 报告进度
                progress = ConversionProgress(
                    current=i + 1,
                    total=len(input_files),
                    current_file=input_file.name,
                    message=f"正在添加: {input_file.name}"
                )
                self._report_progress(progress)

                # 读取PDF
                reader = PdfReader(str(input_file))
                pages_count = len(reader.pages)
                total_pages += pages_count

                # 添加所有页面
                for page in reader.pages:
                    writer.add_page(page)

                logger.debug(f"添加PDF: {input_file.name}, 页数: {pages_count}")

            if self._check_cancelled():
                result.status = ConversionStatus.CANCELLED
                return [result]

            # 生成输出文件名
            output_filename = kwargs.get('output_filename', 'merged.pdf')
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'

            # 确保文件名唯一
            if (output_dir / output_filename).exists():
                output_filename = get_unique_filename(output_dir, output_filename)

            output_path = output_dir / output_filename

            # 写入合并后的PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            result.output_file = output_path
            result.status = ConversionStatus.COMPLETED
            result.message = f"成功合并 {len(input_files)} 个PDF, 共 {total_pages} 页"

            # 报告完成进度
            progress = ConversionProgress(
                current=len(input_files),
                total=len(input_files),
                message="合并完成"
            )
            self._report_progress(progress)

            logger.info(f"PDF合并成功: {len(input_files)} 个文件 -> {output_filename}")

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"PDF合并失败: {e}")

        results.append(result)
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