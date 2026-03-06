# -*- coding: utf-8 -*-
"""
通用文档转PDF转换器
自动识别文档类型并调用相应的转换器
"""
import platform
from pathlib import Path
from typing import List, Optional, Type

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import get_file_extension
from utils.logger import get_logger

logger = get_logger(__name__)


class DocToPdfConverter(BaseConverter):
    """通用文档转PDF转换器"""

    name = "文档转PDF"
    description = "自动识别文档类型并转换为PDF"
    supported_input_formats = [
        # 文本格式
        "txt",
        # Word格式
        "doc", "docx",
        # Excel格式
        "xls", "xlsx",
        # PowerPoint格式
        "ppt", "pptx",
        # 图片格式
        "jpg", "jpeg", "png", "bmp", "tiff", "gif", "webp",
        # PDF
        "pdf",
    ]
    supported_output_formats = ["pdf"]

    def __init__(self):
        super().__init__()
        self._converters = {}  # 缓存转换器实例
        self._use_com = self._check_com_available()

    def _check_com_available(self) -> bool:
        """检查COM是否可用（仅Windows）"""
        if platform.system() != 'Windows':
            return False

        try:
            import win32com.client
            return True
        except ImportError:
            return False

    def _get_converter(self, extension: str) -> Optional[BaseConverter]:
        """
        根据文件扩展名获取对应的转换器

        Args:
            extension: 文件扩展名

        Returns:
            转换器实例，如果没有对应的转换器返回None
        """
        extension = extension.lower()

        # 检查缓存
        if extension in self._converters:
            return self._converters[extension]

        converter = None

        # 文本文件
        if extension == 'txt':
            try:
                from converters.txt_to_pdf import TxtToPdfConverter
                converter = TxtToPdfConverter()
            except ImportError:
                pass

        # Word文档
        elif extension in ['doc', 'docx']:
            try:
                from converters.word_to_pdf import WordToPdfConverter
                converter = WordToPdfConverter()
            except ImportError:
                pass

        # Excel文档
        elif extension in ['xls', 'xlsx']:
            try:
                from converters.excel_to_pdf import ExcelToPdfConverter
                converter = ExcelToPdfConverter()
            except ImportError:
                pass

        # PowerPoint文档
        elif extension in ['ppt', 'pptx']:
            try:
                from converters.ppt_to_pdf import PptToPdfConverter
                converter = PptToPdfConverter()
            except ImportError:
                pass

        # 图片
        elif extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'webp']:
            try:
                from converters.image_to_pdf import ImageToPdfConverter
                converter = ImageToPdfConverter()
            except ImportError:
                pass

        # PDF - 不需要转换
        elif extension == 'pdf':
            converter = None  # PDF不需要转换

        # 缓存转换器
        if converter:
            self._converters[extension] = converter

        return converter

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行文档转PDF转换

        Args:
            input_files: 输入文件列表
            output_dir: 输出目录
            **kwargs: 额外参数

        Returns:
            转换结果列表
        """
        results = []

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

            result = self._convert_single(input_file, output_dir, **kwargs)
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

    def _convert_single(self, input_file: Path, output_dir: Path, **kwargs) -> ConversionResult:
        """
        转换单个文件

        Args:
            input_file: 输入文件
            output_dir: 输出目录
            **kwargs: 额外参数

        Returns:
            转换结果
        """
        result = ConversionResult(input_file=input_file)

        extension = get_file_extension(input_file)

        # PDF文件不需要转换
        if extension == 'pdf':
            result.status = ConversionStatus.COMPLETED
            result.message = "PDF文件无需转换"
            result.output_file = input_file
            return result

        # 获取对应的转换器
        converter = self._get_converter(extension)

        if not converter:
            result.status = ConversionStatus.FAILED
            result.error = f"不支持的文件格式: {extension}"
            return result

        try:
            # 设置进度回调
            if self._progress_callback:
                converter.set_progress_callback(self._progress_callback)

            # 执行转换
            single_results = converter.convert([input_file], output_dir, **kwargs)

            if single_results:
                return single_results[0]
            else:
                result.status = ConversionStatus.FAILED
                result.error = "转换器未返回结果"
                return result

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"文档转换失败: {input_file.name} - {e}")
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

        extension = get_file_extension(file_path)
        return extension.lower() in [fmt.lower() for fmt in self.supported_input_formats]

    def get_supported_types(self) -> dict:
        """
        获取支持的文档类型

        Returns:
            文档类型字典 {类型名: [扩展名列表]}
        """
        return {
            '文本文件': ['txt'],
            'Word文档': ['doc', 'docx'],
            'Excel表格': ['xls', 'xlsx'],
            'PowerPoint演示': ['ppt', 'pptx'],
            '网页': ['html', 'htm'],
            '图片': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'webp'],
            'PDF文档': ['pdf'],
        }