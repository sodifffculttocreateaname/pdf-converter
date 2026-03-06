# -*- coding: utf-8 -*-
"""
PDF转黑白转换器

该模块提供PDF转黑白功能，支持：
- 灰度转换
- 阈值二值化

使用方式：
    from converters.pdf_to_grayscale import PdfToGrayscaleConverter

    converter = PdfToGrayscaleConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfToGrayscaleConverter(BaseConverter):
    """
    PDF转黑白转换器

    将PDF页面转换为灰度或黑白图像。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF转黑白"
    description = "将PDF转换为黑白/灰度"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 转换模式
    MODE_GRAYSCALE = "grayscale"
    MODE_THRESHOLD = "threshold"

    def __init__(self):
        """初始化PDF转黑白转换器"""
        super().__init__()
        self._mode = self.MODE_GRAYSCALE
        self._threshold = 128

    def set_mode(self, mode: str):
        """
        设置转换模式

        Args:
            mode: 转换模式（grayscale/threshold）
        """
        self._mode = mode

    def set_threshold(self, threshold: int):
        """
        设置二值化阈值

        Args:
            threshold: 阈值（0-255）
        """
        self._threshold = max(0, min(255, threshold))

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF转黑白

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - mode: 转换模式（grayscale/threshold）
                - threshold: 二值化阈值

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        mode = kwargs.get('mode', self._mode)
        threshold = kwargs.get('threshold', self._threshold)

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

            # 执行转换
            result = self._convert_to_grayscale(input_file, output_dir, mode, threshold)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="转换完成"
            )
            self._report_progress(progress)

        return results

    def _convert_to_grayscale(self, input_file: Path, output_dir: Path,
                               mode: str, threshold: int) -> ConversionResult:
        """
        将PDF转换为灰度/黑白

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            mode: 转换模式
            threshold: 二值化阈值

        Returns:
            转换结果
        """
        try:
            import fitz  # PyMuPDF
            from PIL import Image

            doc = fitz.open(str(input_file))

            # 创建新的PDF
            output_doc = fitz.open()

            for page_num in range(len(doc)):
                if self._check_cancelled():
                    break

                page = doc[page_num]

                # 渲染页面为图像
                mat = fitz.Matrix(2.0, 2.0)  # 2x缩放
                pix = page.get_pixmap(matrix=mat)

                # 转换为PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # 转换为灰度
                img = img.convert('L')

                if mode == self.MODE_THRESHOLD:
                    # 二值化
                    img = img.point(lambda x: 255 if x > threshold else 0, '1')

                # 转回RGB以便创建PDF
                img = img.convert('RGB')

                # 创建新页面
                img_bytes = img.tobytes()
                new_page = output_doc.new_page(width=pix.width, height=pix.height)
                rect = fitz.Rect(0, 0, pix.width, pix.height)
                new_page.insert_image(rect, stream=img_bytes)

            doc.close()

            # 保存输出
            output_path = output_dir / f"{input_file.stem}_grayscale.pdf"
            output_doc.save(str(output_path))
            output_doc.close()

            result = ConversionResult(
                input_file=input_file,
                output_file=output_path,
                status=ConversionStatus.COMPLETED,
                message=f"已转换为{'黑白' if mode == self.MODE_THRESHOLD else '灰度'}"
            )
            logger.info(f"PDF转黑白成功: {input_file.name}")
            return result

        except ImportError as e:
            logger.error(f"PDF转黑白失败: {input_file.name} - 缺少依赖: {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=f"缺少依赖库: {e}"
            )
        except Exception as e:
            logger.error(f"PDF转黑白失败: {input_file.name} - {e}")
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