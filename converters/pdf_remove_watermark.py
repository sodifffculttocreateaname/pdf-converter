# -*- coding: utf-8 -*-
"""
PDF去水印转换器

该模块提供PDF去水印功能，支持：
- 基于颜色的水印检测和移除
- 基于位置的水印检测（页眉页脚常见位置）
- 支持文字水印和图片水印
- 可配置的阈值和选项

使用方式：
    from converters.pdf_remove_watermark import PdfRemoveWatermarkConverter

    converter = PdfRemoveWatermarkConverter()
    # 设置水印颜色（RGB）
    converter.set_watermark_color((128, 128, 128))  # 灰色
    # 设置颜色容差
    converter.set_color_tolerance(30)
    # 执行去水印
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List, Tuple, Optional

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfRemoveWatermarkConverter(BaseConverter):
    """
    PDF去水印转换器

    移除PDF中的水印，支持基于颜色、位置或透明度的水印检测。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF去水印"
    description = "移除PDF中的水印"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 检测模式
    MODE_COLOR = "color"           # 基于颜色检测
    MODE_POSITION = "position"     # 基于位置检测
    MODE_TRANSPARENCY = "transparency"  # 基于透明度检测
    MODE_MIXED = "mixed"           # 混合模式

    def __init__(self):
        """初始化PDF去水印转换器"""
        super().__init__()
        self._mode = self.MODE_MIXED
        self._watermark_color: Optional[Tuple[int, int, int]] = None
        self._color_tolerance = 30
        self._transparency_threshold = 0.5
        self._remove_header = False
        self._remove_footer = False
        self._header_height = 50  # 页眉高度（点）
        self._footer_height = 50  # 页脚高度（点）

    def set_mode(self, mode: str):
        """
        设置去水印模式

        Args:
            mode: 检测模式（color/position/transparency/mixed）
        """
        self._mode = mode

    def set_watermark_color(self, color: Tuple[int, int, int]):
        """
        设置水印颜色（用于颜色检测模式）

        Args:
            color: RGB颜色元组，如 (128, 128, 128) 表示灰色
        """
        self._watermark_color = color

    def set_color_tolerance(self, tolerance: int):
        """
        设置颜色容差

        Args:
            tolerance: 颜色容差值（0-255），越大匹配范围越广
        """
        self._color_tolerance = max(0, min(255, tolerance))

    def set_transparency_threshold(self, threshold: float):
        """
        设置透明度阈值

        Args:
            threshold: 透明度阈值（0.0-1.0）
        """
        self._transparency_threshold = max(0.0, min(1.0, threshold))

    def set_remove_header_footer(self, remove_header: bool, remove_footer: bool):
        """
        设置是否移除页眉页脚区域的内容

        Args:
            remove_header: 是否移除页眉
            remove_footer: 是否移除页脚
        """
        self._remove_header = remove_header
        self._remove_footer = remove_footer

    def set_header_footer_height(self, header_height: int, footer_height: int):
        """
        设置页眉页脚高度

        Args:
            header_height: 页眉高度（点）
            footer_height: 页脚高度（点）
        """
        self._header_height = header_height
        self._footer_height = footer_height

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF去水印

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - mode: 检测模式
                - watermark_color: 水印颜色(RGB)
                - color_tolerance: 颜色容差
                - transparency_threshold: 透明度阈值
                - remove_header: 是否移除页眉
                - remove_footer: 是否移除页脚

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        mode = kwargs.get('mode', self._mode)
        watermark_color = kwargs.get('watermark_color', self._watermark_color)
        color_tolerance = kwargs.get('color_tolerance', self._color_tolerance)
        transparency_threshold = kwargs.get('transparency_threshold', self._transparency_threshold)
        remove_header = kwargs.get('remove_header', self._remove_header)
        remove_footer = kwargs.get('remove_footer', self._remove_footer)

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
                message=f"正在去除水印: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行去水印
            result = self._remove_watermark(
                input_file, output_dir, mode,
                watermark_color, color_tolerance,
                transparency_threshold, remove_header, remove_footer
            )
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="去水印完成"
            )
            self._report_progress(progress)

        return results

    def _remove_watermark(self, input_file: Path, output_dir: Path,
                          mode: str, watermark_color: Optional[Tuple[int, int, int]],
                          color_tolerance: int, transparency_threshold: float,
                          remove_header: bool, remove_footer: bool) -> ConversionResult:
        """
        移除PDF水印

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            mode: 检测模式
            watermark_color: 水印颜色
            color_tolerance: 颜色容差
            transparency_threshold: 透明度阈值
            remove_header: 是否移除页眉
            remove_footer: 是否移除页脚

        Returns:
            转换结果
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_file))
            removed_text_count = 0
            removed_image_count = 0
            removed_annotation_count = 0

            for page_num in range(len(doc)):
                if self._check_cancelled():
                    break

                page = doc[page_num]
                page_rect = page.rect

                # 1. 移除页眉页脚区域的内容
                if remove_header or remove_footer:
                    header_footer_removed = self._remove_header_footer(
                        page, page_rect, remove_header, remove_footer
                    )
                    removed_annotation_count += header_footer_removed

                # 2. 基于颜色移除文字水印
                if mode in [self.MODE_COLOR, self.MODE_MIXED] and watermark_color:
                    color_removed = self._remove_by_color(
                        page, watermark_color, color_tolerance
                    )
                    removed_text_count += color_removed

                # 3. 基于透明度检测（适用于部分PDF）
                if mode in [self.MODE_TRANSPARENCY, self.MODE_MIXED]:
                    transparency_removed = self._remove_by_transparency(
                        page, transparency_threshold
                    )
                    removed_text_count += transparency_removed

                # 4. 移除常见的图形水印（如对角线文字）
                if mode == self.MODE_MIXED:
                    shape_removed = self._remove_shape_watermarks(page)
                    removed_annotation_count += shape_removed

                # 5. 尝试覆盖常见的水印图案
                self._cover_common_watermarks(page, page_rect)

            # 保存输出
            output_path = output_dir / f"{input_file.stem}_cleaned.pdf"
            doc.save(str(output_path), garbage=4, deflate=True)
            doc.close()

            total_removed = removed_text_count + removed_image_count + removed_annotation_count
            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"已移除 {total_removed} 个水印元素（文字:{removed_text_count}, 图形:{removed_annotation_count}）"
            )
            logger.info(f"PDF去水印成功: {input_file.name}, 移除 {total_removed} 个元素")
            return result

        except ImportError as e:
            logger.error(f"PDF去水印失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF去水印失败: {input_file.name} - {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )

    def _remove_header_footer(self, page, page_rect, remove_header: bool,
                              remove_footer: bool) -> int:
        """
        移除页眉页脚区域的内容

        Args:
            page: PyMuPDF页面对象
            page_rect: 页面矩形
            remove_header: 是否移除页眉
            remove_footer: 是否移除页脚

        Returns:
            移除的元素数量
        """
        removed_count = 0

        try:
            # 创建页眉区域矩形
            if remove_header:
                header_rect = fitz.Rect(
                    page_rect.x0,
                    page_rect.y0,
                    page_rect.x1,
                    page_rect.y0 + self._header_height
                )
                # 添加白色矩形覆盖页眉
                shape = page.new_shape()
                shape.draw_rect(header_rect)
                shape.finish(color=(1, 1, 1), fill=(1, 1, 1))
                shape.commit()
                removed_count += 1

            # 创建页脚区域矩形
            if remove_footer:
                footer_rect = fitz.Rect(
                    page_rect.x0,
                    page_rect.y1 - self._footer_height,
                    page_rect.x1,
                    page_rect.y1
                )
                # 添加白色矩形覆盖页脚
                shape = page.new_shape()
                shape.draw_rect(footer_rect)
                shape.finish(color=(1, 1, 1), fill=(1, 1, 1))
                shape.commit()
                removed_count += 1

        except Exception as e:
            logger.debug(f"移除页眉页脚时出错: {e}")

        return removed_count

    def _remove_by_color(self, page, watermark_color: Tuple[int, int, int],
                         tolerance: int) -> int:
        """
        基于颜色移除文字水印

        Args:
            page: PyMuPDF页面对象
            watermark_color: 水印颜色(RGB)
            tolerance: 颜色容差

        Returns:
            移除的文字元素数量
        """
        removed_count = 0

        try:
            # 将RGB颜色归一化到0-1范围
            target_r = watermark_color[0] / 255.0
            target_g = watermark_color[1] / 255.0
            target_b = watermark_color[2] / 255.0
            tolerance_norm = tolerance / 255.0

            # 获取页面上的所有文字块
            blocks = page.get_text("blocks")

            for block in blocks:
                # block格式: (x0, y0, x1, y1, text, block_no, block_type)
                if len(block) >= 5:
                    rect = fitz.Rect(block[0], block[1], block[2], block[3])
                    text = block[4]

                    # 检查文字颜色（使用span级别的颜色信息）
                    text_dict = page.get_text("dict", clip=rect)
                    for text_block in text_dict.get("blocks", []):
                        if "lines" in text_block:
                            for line in text_block["lines"]:
                                for span in line.get("spans", []):
                                    color = span.get("color")
                                    if color is not None:
                                        # 将整数颜色转换为RGB
                                        r = ((color >> 16) & 0xFF) / 255.0
                                        g = ((color >> 8) & 0xFF) / 255.0
                                        b = (color & 0xFF) / 255.0

                                        # 检查颜色是否匹配
                                        if (abs(r - target_r) <= tolerance_norm and
                                            abs(g - target_g) <= tolerance_norm and
                                            abs(b - target_b) <= tolerance_norm):
                                            # 添加白色覆盖层
                                            page.add_redact_annot(rect, fill=(1, 1, 1))
                                            removed_count += 1
                                            break

            # 应用所有修订
            page.apply_redactions()

        except Exception as e:
            logger.debug(f"基于颜色移除时出错: {e}")

        return removed_count

    def _remove_by_transparency(self, page, threshold: float) -> int:
        """
        基于透明度检测移除水印

        Args:
            page: PyMuPDF页面对象
            threshold: 透明度阈值

        Returns:
            移除的元素数量
        """
        removed_count = 0

        try:
            # 获取页面上的注释（annotations）
            annots = list(page.annots())

            for annot in annots:
                try:
                    # 检查注释类型，某些水印可能作为注释添加
                    if annot.type[0] in [2, 25]:  # FreeText 或 Stamp
                        rect = annot.rect
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        removed_count += 1
                except Exception:
                    continue

            # 应用修订
            page.apply_redactions()

            # 尝试检测半透明的XObject（如水印层）
            xobjects = page.get_xobjects()
            for xobj in xobjects:
                try:
                    # 检查XObject的名称，常见的水印名称包含"Watermark"等
                    name = xobj.get("name", "").lower()
                    if any(keyword in name for keyword in ["watermark", "draft", "confidential", "sample"]):
                        rect = xobj.get("rect", page.rect)
                        if rect:
                            page.add_redact_annot(rect, fill=(1, 1, 1))
                            removed_count += 1
                except Exception:
                    continue

            page.apply_redactions()

        except Exception as e:
            logger.debug(f"基于透明度移除时出错: {e}")

        return removed_count

    def _remove_shape_watermarks(self, page) -> int:
        """
        移除图形水印（如对角线文字）

        Args:
            page: PyMuPDF页面对象

        Returns:
            移除的图形数量
        """
        removed_count = 0

        try:
            # 获取页面上的绘图对象
            drawings = page.get_drawings()

            for drawing in drawings:
                try:
                    rect = drawing.get("rect")
                    if rect:
                        # 检查是否是覆盖整个页面的半透明层
                        page_area = page.rect.width * page.rect.height
                        drawing_area = rect.width * rect.height

                        # 如果绘图覆盖页面的大部分区域，可能是水印背景
                        if drawing_area > page_area * 0.5:
                            page.add_redact_annot(rect, fill=(1, 1, 1))
                            removed_count += 1
                except Exception:
                    continue

            page.apply_redactions()

        except Exception as e:
            logger.debug(f"移除图形水印时出错: {e}")

        return removed_count

    def _cover_common_watermarks(self, page, page_rect):
        """
        覆盖常见的水印图案（如"SAMPLE", "DRAFT", "CONFIDENTIAL"等）

        Args:
            page: PyMuPDF页面对象
            page_rect: 页面矩形
        """
        try:
            # 常见的半透明水印关键词
            watermark_keywords = [
                "sample", "draft", "confidential", "copy", "watermark",
                "内部资料", "机密", "草稿", "样品", "样张"
            ]

            # 获取所有文字
            text_blocks = page.get_text("blocks")

            for block in text_blocks:
                if len(block) >= 5:
                    text = block[4].lower()
                    rect = fitz.Rect(block[0], block[1], block[2], block[3])

                    # 检查是否包含水印关键词
                    if any(keyword in text for keyword in watermark_keywords):
                        # 扩展矩形以确保完全覆盖
                        extended_rect = rect + (-5, -5, 5, 5)
                        page.add_redact_annot(extended_rect, fill=(1, 1, 1))

            page.apply_redactions()

        except Exception as e:
            logger.debug(f"覆盖常见水印时出错: {e}")

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
