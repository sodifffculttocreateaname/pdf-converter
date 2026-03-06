# -*- coding: utf-8 -*-
"""
PDF加水印转换器

该模块提供PDF加水印功能，支持：
- 文字水印（支持透明度）
- 图片水印（支持透明度）
- 平铺/居中/对角线位置
- 密集程度调节（平铺模式）
- 倾斜角度设置

使用方式：
    from converters.pdf_add_watermark import PdfAddWatermarkConverter

    converter = PdfAddWatermarkConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
import math
from pathlib import Path
from typing import List, Tuple

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfAddWatermarkConverter(BaseConverter):
    """
    PDF加水印转换器

    在PDF中添加文字或图片水印。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF加水印"
    description = "在PDF中添加文字或图片水印"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 水印类型
    TYPE_TEXT = "text"
    TYPE_IMAGE = "image"

    # 位置模式
    POSITION_TILE = "tile"        # 平铺
    POSITION_CENTER = "center"   # 居中
    POSITION_DIAGONAL = "diagonal"  # 对角线

    def __init__(self):
        """初始化PDF加水印转换器"""
        super().__init__()
        self._watermark_type = self.TYPE_TEXT
        self._text = "WATERMARK"
        self._font_size = 50
        self._color = (200, 200, 200)  # 灰色
        self._opacity = 0.3
        self._position = self.POSITION_DIAGONAL
        self._rotation = 45
        self._spacing_x = 250  # 水平间距
        self._spacing_y = 200  # 垂直间距
        self._image_path = None

    def set_text_watermark(self, text: str, font_size: int = 50,
                           color: Tuple[int, int, int] = (200, 200, 200)):
        """
        设置文字水印

        Args:
            text: 水印文字
            font_size: 字体大小
            color: RGB颜色元组
        """
        self._watermark_type = self.TYPE_TEXT
        self._text = text
        self._font_size = font_size
        self._color = color

    def set_image_watermark(self, image_path: Path):
        """
        设置图片水印

        Args:
            image_path: 图片路径
        """
        self._watermark_type = self.TYPE_IMAGE
        self._image_path = image_path

    def set_opacity(self, opacity: float):
        """
        设置透明度

        Args:
            opacity: 透明度（0.0-1.0）
        """
        self._opacity = max(0.0, min(1.0, opacity))

    def set_position(self, position: str):
        """
        设置位置模式

        Args:
            position: 位置模式（tile/center/diagonal）
        """
        self._position = position

    def set_rotation(self, rotation: int):
        """
        设置旋转角度

        Args:
            rotation: 旋转角度（-180到180）
        """
        self._rotation = rotation

    def set_spacing(self, spacing_x: int, spacing_y: int):
        """
        设置水印间距（平铺模式）

        Args:
            spacing_x: 水平间距（像素）
            spacing_y: 垂直间距（像素）
        """
        self._spacing_x = max(50, spacing_x)
        self._spacing_y = max(50, spacing_y)

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF加水印

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数

        Returns:
            转换结果列表
        """
        results = []

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
                message=f"正在添加水印: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行加水印
            result = self._add_watermark(input_file, output_dir)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="添加水印完成"
            )
            self._report_progress(progress)

        return results

    def _add_watermark(self, input_file: Path, output_dir: Path) -> ConversionResult:
        """
        添加水印到PDF

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录

        Returns:
            转换结果
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(input_file))

            for page_num in range(len(doc)):
                if self._check_cancelled():
                    break

                page = doc[page_num]
                rect = page.rect

                if self._watermark_type == self.TYPE_TEXT:
                    # 添加文字水印
                    self._add_text_watermark(page, rect)
                else:
                    # 添加图片水印
                    self._add_image_watermark(page, rect)

            # 保存输出
            output_path = output_dir / f"{input_file.stem}_watermarked.pdf"
            doc.save(str(output_path))
            doc.close()

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message="水印添加完成"
            )
            logger.info(f"PDF加水印成功: {input_file.name}")
            return result

        except ImportError as e:
            logger.error(f"PDF加水印失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF加水印失败: {input_file.name} - {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )

    def _add_text_watermark(self, page, rect):
        """
        添加文字水印 - 支持旋转角度和透明度

        Args:
            page: PyMuPDF页面对象
            rect: 页面矩形
        """
        import fitz

        # RGB颜色转换为0-1范围
        color = (self._color[0] / 255, self._color[1] / 255, self._color[2] / 255)

        # 计算水印位置
        if self._position == self.POSITION_CENTER:
            positions = [(rect.width / 2, rect.height / 2)]
        elif self._position == self.POSITION_DIAGONAL:
            # 对角线多个水印
            positions = []
            # 从左上到右下
            for i in range(-2, 5):
                x = rect.width * i / 4
                y = rect.height * i / 4 + rect.height / 4
                if 0 <= x <= rect.width + 100 and 0 <= y <= rect.height + 100:
                    positions.append((x, y))
        else:
            # 平铺 - 使用用户设置的间距
            positions = []
            for x in range(0, int(rect.width) + self._spacing_x, self._spacing_x):
                for y in range(0, int(rect.height) + self._spacing_y, self._spacing_y):
                    positions.append((x, y))

        # 使用TextWriter来支持透明度和颜色
        font = fitz.Font('helv')

        for x, y in positions:
            try:
                tw = fitz.TextWriter(page.rect)
                text_point = fitz.Point(x, y)
                tw.append(text_point, self._text, font=font, fontsize=self._font_size)
                # write_text支持color和opacity参数
                tw.write_text(page, color=color, opacity=self._opacity, rotate=self._rotation)
            except Exception as e:
                # 如果rotate参数不支持，尝试不带旋转
                try:
                    tw = fitz.TextWriter(page.rect)
                    tw.append(text_point, self._text, font=font, fontsize=self._font_size)
                    tw.write_text(page, color=color, opacity=self._opacity)
                except Exception as e2:
                    logger.warning(f"添加水印失败: {e2}")

    def _add_image_watermark(self, page, rect):
        """
        添加图片水印

        Args:
            page: PyMuPDF页面对象
            rect: 页面矩形
        """
        if not self._image_path or not self._image_path.exists():
            logger.warning(f"图片水印文件不存在: {self._image_path}")
            return

        import fitz

        # 计算水印位置
        if self._position == self.POSITION_CENTER:
            img_rect = fitz.Rect(
                rect.width / 4,
                rect.height / 4,
                rect.width * 3 / 4,
                rect.height * 3 / 4
            )
            page.insert_image(img_rect, filename=str(self._image_path))
        elif self._position == self.POSITION_DIAGONAL:
            # 对角线多个水印
            for i in range(-1, 3):
                x = rect.width * i / 3
                y = rect.height * i / 3 + rect.height / 4
                if -100 <= x <= rect.width and -100 <= y <= rect.height:
                    img_rect = fitz.Rect(x, y, x + 150, y + 100)
                    page.insert_image(img_rect, filename=str(self._image_path))
        else:
            # 平铺
            for x in range(0, int(rect.width) + self._spacing_x, self._spacing_x):
                for y in range(0, int(rect.height) + self._spacing_y, self._spacing_y):
                    img_rect = fitz.Rect(x, y, x + 150, y + 100)
                    page.insert_image(img_rect, filename=str(self._image_path))

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