# -*- coding: utf-8 -*-
"""
PDF转图片转换器
"""
import os
from pathlib import Path
from typing import List

from pdf2image import convert_from_path

from config.constants import ConversionStatus
from config.settings import Settings
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfToImageConverter(BaseConverter):
    """PDF转图片转换器"""

    name = "PDF转图片"
    description = "将PDF文档转换为图片"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["png", "jpg", "jpeg", "bmp", "tiff"]

    def __init__(self):
        super().__init__()
        self._dpi = 150
        self._output_format = "png"
        self._quality = 85

    def set_dpi(self, dpi: int):
        """设置DPI"""
        self._dpi = dpi

    def set_output_format(self, format_name: str):
        """设置输出格式"""
        self._output_format = format_name.lower()

    def set_quality(self, quality: int):
        """设置压缩质量"""
        self._quality = quality

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF转图片转换

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数 (dpi, format, quality)

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        dpi = kwargs.get('dpi', self._dpi)
        output_format = kwargs.get('format', self._output_format).lower()
        quality = kwargs.get('quality', self._quality)

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

            result = self._convert_pdf(input_file, output_dir, dpi, output_format, quality)
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

    def _convert_pdf(self, input_file: Path, output_dir: Path,
                     dpi: int, output_format: str, quality: int) -> ConversionResult:
        """
        转换单个PDF

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            dpi: DPI设置
            output_format: 输出格式
            quality: 压缩质量

        Returns:
            转换结果
        """
        result = ConversionResult(input_file=input_file)

        try:
            # 创建输出子目录
            pdf_output_dir = output_dir / input_file.stem
            ensure_dir(pdf_output_dir)

            # 获取poppler路径（Windows需要）
            poppler_path = self._get_poppler_path()

            # 转换PDF为图片（不指定output_folder，只在内存中转换）
            if poppler_path:
                images = convert_from_path(
                    str(input_file),
                    dpi=dpi,
                    fmt=output_format,
                    poppler_path=poppler_path
                )
            else:
                images = convert_from_path(
                    str(input_file),
                    dpi=dpi,
                    fmt=output_format
                )

            # 保存图片
            saved_files = []
            for page_num, image in enumerate(images, 1):
                if self._check_cancelled():
                    break

                output_filename = f"{input_file.stem}_page_{page_num:03d}.{output_format}"
                output_path = pdf_output_dir / output_filename

                # 如果是JPEG，设置质量
                if output_format in ['jpg', 'jpeg']:
                    image.save(output_path, quality=quality)
                else:
                    image.save(output_path)

                saved_files.append(output_path)

            if self._check_cancelled():
                result.status = ConversionStatus.CANCELLED
                # 清理已创建的文件
                for f in saved_files:
                    if f.exists():
                        f.unlink()
            else:
                result.output_file = pdf_output_dir
                result.status = ConversionStatus.COMPLETED
                result.message = f"成功转换 {len(saved_files)} 页"

                logger.info(f"PDF转图片成功: {input_file.name} -> {len(saved_files)} 张图片")

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"PDF转图片失败: {input_file.name} - {e}")

        return result

    def _get_poppler_path(self) -> str:
        """
        获取poppler路径（Windows需要）

        Returns:
            poppler路径，非Windows返回None
        """
        if os.name != 'nt':
            return None

        # 尝试从环境变量获取
        poppler_path = os.environ.get('POPPLER_PATH')
        if poppler_path and os.path.exists(poppler_path):
            return poppler_path

        # 获取项目根目录（当前文件所在目录的父目录）
        project_root = Path(__file__).parent.parent

        # 尝试项目目录下的tools/poppler路径
        project_poppler_paths = [
            project_root / "tools" / "poppler" / "Library" / "bin",
            project_root / "tools" / "poppler-25.12.0" / "Library" / "bin",
        ]

        for path in project_poppler_paths:
            if path.exists():
                return str(path)

        # 尝试常见系统路径
        common_paths = [
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Program Files (x86)\poppler\Library\bin",
            r"C:\poppler\Library\bin",
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'poppler', 'Library', 'bin'),
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

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