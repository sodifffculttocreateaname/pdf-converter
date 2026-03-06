# -*- coding: utf-8 -*-
"""
PDF添加页码转换器

该模块提供PDF添加页码功能，支持：
- 页码位置选择：底部居中/左下/右下
- 页码格式：简单数字/第N页/第N页共M页
- 起始页码设置
- 字体大小设置

使用方式：
    from converters.pdf_add_page_numbers import PdfAddPageNumbersConverter

    converter = PdfAddPageNumbersConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfAddPageNumbersConverter(BaseConverter):
    """
    PDF添加页码转换器

    在PDF页面底部添加页码。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF添加页码"
    description = "在PDF页面底部添加页码"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 页码位置
    POSITION_CENTER = "center"
    POSITION_LEFT = "left"
    POSITION_RIGHT = "right"

    # 页码格式
    FORMAT_SIMPLE = "simple"        # 1, 2, 3
    FORMAT_PAGE = "page"            # 第1页
    FORMAT_PAGE_TOTAL = "page_total"  # 第1页/共N页

    def __init__(self):
        """初始化PDF添加页码转换器"""
        super().__init__()
        self._position = self.POSITION_CENTER
        self._format_type = self.FORMAT_SIMPLE
        self._start_page = 1
        self._font_size = 10

    def set_position(self, position: str):
        """
        设置页码位置

        Args:
            position: 页码位置（center/left/right）
        """
        self._position = position

    def set_format(self, format_type: str):
        """
        设置页码格式

        Args:
            format_type: 页码格式（simple/page/page_total）
        """
        self._format_type = format_type

    def set_start_page(self, start: int):
        """
        设置起始页码

        Args:
            start: 起始页码
        """
        self._start_page = start

    def set_font_size(self, size: int):
        """
        设置字体大小

        Args:
            size: 字体大小（pt）
        """
        self._font_size = size

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF添加页码

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - position: 页码位置
                - format_type: 页码格式
                - start_page: 起始页码
                - font_size: 字体大小

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        position = kwargs.get('position', self._position)
        format_type = kwargs.get('format_type', self._format_type)
        start_page = kwargs.get('start_page', self._start_page)
        font_size = kwargs.get('font_size', self._font_size)

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
                message=f"正在添加页码: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行添加页码
            result = self._add_page_numbers(input_file, output_dir, position, format_type, start_page, font_size)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="添加页码完成"
            )
            self._report_progress(progress)

        return results

    def _format_page_number(self, page_num: int, total: int, format_type: str) -> str:
        """
        格式化页码文本

        Args:
            page_num: 当前页码
            total: 总页数
            format_type: 格式类型

        Returns:
            格式化的页码文本
        """
        if format_type == self.FORMAT_PAGE:
            return f"第{page_num}页"
        elif format_type == self.FORMAT_PAGE_TOTAL:
            return f"第{page_num}页/共{total}页"
        else:
            return str(page_num)

    def _add_page_numbers(self, input_file: Path, output_dir: Path,
                          position: str, format_type: str,
                          start_page: int, font_size: int) -> ConversionResult:
        """
        添加页码到PDF

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            position: 页码位置
            format_type: 页码格式
            start_page: 起始页码
            font_size: 字体大小

        Returns:
            转换结果
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_file))
            total_pages = len(doc)

            for page_num in range(total_pages):
                if self._check_cancelled():
                    break

                page = doc[page_num]
                rect = page.rect

                # 计算页码文本
                display_num = page_num + start_page
                text = self._format_page_number(display_num, total_pages + start_page - 1, format_type)

                # 计算位置
                text_width = len(text) * font_size * 0.5  # 估算文本宽度
                margin = 30

                if position == self.POSITION_LEFT:
                    x = margin
                elif position == self.POSITION_RIGHT:
                    x = rect.width - text_width - margin
                else:  # center
                    x = (rect.width - text_width) / 2

                y = rect.height - margin

                # 添加文本
                point = fitz.Point(x, y)
                page.insert_text(
                    point,
                    text,
                    fontsize=font_size,
                    color=(0, 0, 0)  # 黑色
                )

            # 保存输出
            output_path = output_dir / f"{input_file.stem}_numbered.pdf"
            doc.save(str(output_path))
            doc.close()

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"已添加页码（共{total_pages}页）"
            )
            logger.info(f"PDF添加页码成功: {input_file.name}")
            return result

        except ImportError as e:
            logger.error(f"PDF添加页码失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF添加页码失败: {input_file.name} - {e}")
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