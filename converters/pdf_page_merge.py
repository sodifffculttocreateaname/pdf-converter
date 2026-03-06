# -*- coding: utf-8 -*-
"""
PDF页面合并转换器

该模块提供PDF页面合并功能，支持：
- 2合1布局
- 4合1布局
- 6合1布局
- 边框显示设置

使用方式：
    from converters.pdf_page_merge import PdfPageMergeConverter

    converter = PdfPageMergeConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfPageMergeConverter(BaseConverter):
    """
    PDF页面合并转换器

    将PDF多页合并为单页打印布局。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF页面合并"
    description = "将PDF多页合并为单页（如2合1、4合1）"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        """初始化PDF页面合并转换器"""
        super().__init__()
        self._layout = 4  # 2、4、6
        self._spacing = 5
        self._show_border = False

    def set_layout(self, layout: int):
        """
        设置布局

        Args:
            layout: 合并数量（2/4/6）
        """
        if layout in [2, 4, 6]:
            self._layout = layout
        else:
            raise ValueError("布局必须是 2、4 或 6")

    def set_spacing(self, spacing: int):
        """
        设置页面间距

        Args:
            spacing: 间距（点）
        """
        self._spacing = spacing

    def set_show_border(self, show: bool):
        """
        设置是否显示边框

        Args:
            show: 是否显示边框
        """
        self._show_border = show

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF页面合并

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - layout: 布局（2/4/6）
                - spacing: 页面间距
                - show_border: 是否显示边框

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        layout = kwargs.get('layout', self._layout)
        spacing = kwargs.get('spacing', self._spacing)
        show_border = kwargs.get('show_border', self._show_border)

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
                message=f"正在合并: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行合并
            result = self._merge_pages(input_file, output_dir, layout, spacing, show_border)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="合并完成"
            )
            self._report_progress(progress)

        return results

    def _merge_pages(self, input_file: Path, output_dir: Path,
                     layout: int, spacing: int, show_border: bool) -> ConversionResult:
        """
        合并PDF页面

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            layout: 布局
            spacing: 间距
            show_border: 是否显示边框

        Returns:
            转换结果
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_file))
            total_pages = len(doc)

            if total_pages == 0:
                doc.close()
                return ConversionResult(
                    input_file=input_file,
                    status=ConversionStatus.FAILED,
                    error="PDF没有页面"
                )

            # 计算布局
            if layout == 2:
                cols, rows = 2, 1
            elif layout == 4:
                cols, rows = 2, 2
            else:  # 6
                cols, rows = 3, 2

            # 获取第一页尺寸作为参考
            first_page = doc[0]
            src_width = first_page.rect.width
            src_height = first_page.rect.height

            # 计算新页面尺寸
            new_width = cols * src_width + (cols + 1) * spacing
            new_height = rows * src_height + (rows + 1) * spacing

            # 创建新文档
            new_doc = fitz.open()
            output_page_count = 0

            # 按布局合并页面
            page_index = 0
            while page_index < total_pages:
                if self._check_cancelled():
                    break

                # 创建新页面
                new_page = new_doc.new_page(width=new_width, height=new_height)

                # 填充布局
                for row in range(rows):
                    for col in range(cols):
                        if page_index >= total_pages:
                            break

                        # 计算位置
                        x = spacing + col * (src_width + spacing)
                        y = spacing + row * (src_height + spacing)
                        dest_rect = fitz.Rect(x, y, x + src_width, y + src_height)

                        # 插入源页面
                        new_page.show_pdf_page(dest_rect, doc, page_index)

                        # 绘制边框
                        if show_border:
                            shape = new_page.new_shape()
                            shape.draw_rect(dest_rect)
                            shape.finish(color=(0.5, 0.5, 0.5), width=0.5)
                            shape.commit()

                        page_index += 1

                output_page_count += 1

            # 保存输出
            output_path = output_dir / f"{input_file.stem}_merged.pdf"
            new_doc.save(str(output_path))
            new_doc.close()
            doc.close()

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"{layout}合1，共{output_page_count}页"
            )
            logger.info(f"PDF页面合并成功: {input_file.name} -> {layout}合1")
            return result

        except ImportError as e:
            logger.error(f"PDF页面合并失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF页面合并失败: {input_file.name} - {e}")
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