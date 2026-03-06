# -*- coding: utf-8 -*-
"""
PDF转Word转换器
"""
from pathlib import Path
from typing import List

from pdf2docx import Converter

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfToWordConverter(BaseConverter):
    """PDF转Word转换器"""

    name = "PDF转Word"
    description = "将PDF文档转换为Word文档"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["docx"]

    def __init__(self):
        super().__init__()
        self._start_page = 0    # 起始页（0表示全部）
        self._end_page = 0      # 结束页（0表示全部）

    def set_page_range(self, start: int, end: int):
        """
        设置转换的页码范围

        Args:
            start: 起始页（从1开始）
            end: 结束页
        """
        self._start_page = start
        self._end_page = end

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF转Word转换

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数 (start_page, end_page)

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        start_page = kwargs.get('start_page', self._start_page)
        end_page = kwargs.get('end_page', self._end_page)

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

            result = self._convert_pdf_to_word(input_file, output_dir, start_page, end_page)
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

    def _convert_pdf_to_word(self, input_file: Path, output_dir: Path,
                              start_page: int, end_page: int) -> ConversionResult:
        """
        转换单个PDF为Word

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            start_page: 起始页
            end_page: 结束页

        Returns:
            转换结果
        """
        result = ConversionResult(input_file=input_file)

        try:
            # 生成输出文件名
            output_filename = self.get_output_filename(input_file, 'docx')
            output_path = output_dir / output_filename

            # 创建转换器
            cv = Converter(str(input_file))

            # 设置进度回调
            def progress_callback(current, total):
                if self._check_cancelled():
                    cv.close()
                    return
                progress = ConversionProgress(
                    current=current,
                    total=total,
                    current_file=input_file.name,
                    message=f"正在转换第 {current}/{total} 页"
                )
                self._report_progress(progress)

            # 转换
            # pages参数: None表示全部, (start, end)表示范围
            pages = None
            if start_page > 0 and end_page > 0:
                pages = (start_page - 1, end_page - 1)  # pdf2docx使用0-based索引
            elif start_page > 0:
                pages = (start_page - 1, None)

            cv.convert(
                str(output_path),
                start=0 if pages is None else pages[0],
                end=None if pages is None else pages[1],
                progress_callback=progress_callback
            )

            cv.close()

            if self._check_cancelled():
                result.status = ConversionStatus.CANCELLED
                if output_path.exists():
                    output_path.unlink()
            else:
                result.output_file = output_path
                result.status = ConversionStatus.COMPLETED
                result.message = "转换成功"

                logger.info(f"PDF转Word成功: {input_file.name}")

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"PDF转Word失败: {input_file.name} - {e}")

        return result

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