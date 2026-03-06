# -*- coding: utf-8 -*-
"""
PDF分割裁剪转换器

该模块提供PDF分割裁剪功能，支持：
- 裁剪页面边距
- 水平分割
- 垂直分割

使用方式：
    from converters.pdf_crop_split import PdfCropSplitConverter

    converter = PdfCropSplitConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List, Tuple

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfCropSplitConverter(BaseConverter):
    """
    PDF分割裁剪转换器

    裁剪PDF页面或分割页面。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF分割裁剪"
    description = "裁剪PDF页面或分割页面"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 操作模式
    MODE_CROP = "crop"
    MODE_SPLIT = "split"

    # 分割类型
    SPLIT_HORIZONTAL = "horizontal"
    SPLIT_VERTICAL = "vertical"

    def __init__(self):
        """初始化PDF分割裁剪转换器"""
        super().__init__()
        self._mode = self.MODE_CROP
        self._margins = (0, 0, 0, 0)  # left, top, right, bottom
        self._split_type = self.SPLIT_HORIZONTAL

    def set_mode(self, mode: str):
        """
        设置操作模式

        Args:
            mode: 操作模式（crop/split）
        """
        self._mode = mode

    def set_margins(self, left: int, top: int, right: int, bottom: int):
        """
        设置裁剪边距

        Args:
            left: 左边距（点）
            top: 上边距（点）
            right: 右边距（点）
            bottom: 下边距（点）
        """
        self._margins = (left, top, right, bottom)

    def set_split_type(self, split_type: str):
        """
        设置分割类型

        Args:
            split_type: 分割类型（horizontal/vertical）
        """
        self._split_type = split_type

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF分割裁剪

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - mode: 操作模式
                - margins: 裁剪边距元组
                - split_type: 分割类型

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        mode = kwargs.get('mode', self._mode)
        margins = kwargs.get('margins', self._margins)
        split_type = kwargs.get('split_type', self._split_type)

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
            if mode == self.MODE_CROP:
                result = self._crop_pdf(input_file, output_dir, margins)
            else:
                result = self._split_pdf(input_file, output_dir, split_type)
            results.extend(result if isinstance(result, list) else [result])

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="处理完成"
            )
            self._report_progress(progress)

        return results

    def _crop_pdf(self, input_file: Path, output_dir: Path,
                  margins: Tuple[int, int, int, int]) -> ConversionResult:
        """
        裁剪PDF页面

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            margins: 裁剪边距（左、上、右、下）

        Returns:
            转换结果
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_file))
            left, top, right, bottom = margins

            for page in doc:
                if self._check_cancelled():
                    break

                rect = page.rect
                # 计算新的页面框
                new_rect = fitz.Rect(
                    rect.x0 + left,
                    rect.y0 + top,
                    rect.x1 - right,
                    rect.y1 - bottom
                )
                page.set_cropbox(new_rect)

            # 保存输出
            output_path = output_dir / f"{input_file.stem}_cropped.pdf"
            doc.save(str(output_path))
            doc.close()

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message="裁剪完成"
            )
            logger.info(f"PDF裁剪成功: {input_file.name}")
            return result

        except ImportError as e:
            logger.error(f"PDF裁剪失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF裁剪失败: {input_file.name} - {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )

    def _split_pdf(self, input_file: Path, output_dir: Path,
                   split_type: str) -> List[ConversionResult]:
        """
        分割PDF页面

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            split_type: 分割类型

        Returns:
            转换结果列表
        """
        results = []

        try:
            import fitz  # PyMuPDF
            from pypdf import PdfReader, PdfWriter

            doc = fitz.open(str(input_file))
            split_count = 0

            for page_num in range(len(doc)):
                if self._check_cancelled():
                    break

                page = doc[page_num]
                rect = page.rect

                if split_type == self.SPLIT_HORIZONTAL:
                    # 水平分割（上下分割）
                    top_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1 / 2)
                    bottom_rect = fitz.Rect(rect.x0, rect.y1 / 2, rect.x1, rect.y1)

                    # 创建新PDF
                    for i, crop_rect in enumerate([top_rect, bottom_rect]):
                        new_doc = fitz.open()
                        new_page = new_doc.new_page(width=rect.width, height=rect.height / 2)
                        new_page.show_pdf_page(crop_rect, doc, page_num)
                        output_path = output_dir / f"{input_file.stem}_p{page_num + 1}_{i + 1}.pdf"
                        new_doc.save(str(output_path))
                        new_doc.close()

                        results.append(ConversionResult(
                            input_file=input_file,
                            output_file=output_path,
                            status=ConversionStatus.COMPLETED,
                            message=f"第{page_num + 1}页 - {'上' if i == 0 else '下'}半部分"
                        ))
                        split_count += 1

                else:  # vertical
                    # 垂直分割（左右分割）
                    left_rect = fitz.Rect(rect.x0, rect.y0, rect.x1 / 2, rect.y1)
                    right_rect = fitz.Rect(rect.x1 / 2, rect.y0, rect.x1, rect.y1)

                    for i, crop_rect in enumerate([left_rect, right_rect]):
                        new_doc = fitz.open()
                        new_page = new_doc.new_page(width=rect.width / 2, height=rect.height)
                        new_page.show_pdf_page(crop_rect, doc, page_num)
                        output_path = output_dir / f"{input_file.stem}_p{page_num + 1}_{i + 1}.pdf"
                        new_doc.save(str(output_path))
                        new_doc.close()

                        results.append(ConversionResult(
                            input_file=input_file,
                            output_file=output_path,
                            status=ConversionStatus.COMPLETED,
                            message=f"第{page_num + 1}页 - {'左' if i == 0 else '右'}半部分"
                        ))
                        split_count += 1

            doc.close()
            logger.info(f"PDF分割成功: {input_file.name} -> {split_count} 个文件")

        except ImportError as e:
            logger.error(f"PDF分割失败: {input_file.name} - 缺少依赖: {e}")
            results.append(ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            ))
        except Exception as e:
            logger.error(f"PDF分割失败: {input_file.name} - {e}")
            results.append(ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            ))

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