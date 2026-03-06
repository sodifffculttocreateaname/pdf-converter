# -*- coding: utf-8 -*-
"""
常量定义模块

该模块定义了应用程序中使用的所有常量和枚举类型，包括：
- 转换状态枚举
- 文件格式枚举
- 图片格式列表
- 文档格式映射
- 功能模块名称映射
- 文件大小格式化工具函数

使用方式：
    from config.constants import ConversionStatus, MODULE_NAMES, format_file_size

    # 使用转换状态
    status = ConversionStatus.COMPLETED

    # 获取模块名称
    name = MODULE_NAMES.get('image_to_pdf')

    # 格式化文件大小
    size_str = format_file_size(1024 * 1024)  # 返回 "1.00 MB"
"""
from enum import Enum, auto
from typing import Dict, List


class ConversionStatus(Enum):
    """
    转换状态枚举

    定义文件转换过程中的所有可能状态。

    Attributes:
        PENDING: 待处理状态 - 文件已添加到队列，等待处理
        PROCESSING: 处理中状态 - 文件正在被转换
        COMPLETED: 已完成状态 - 文件转换成功
        FAILED: 失败状态 - 文件转换失败
        CANCELLED: 已取消状态 - 用户取消了转换操作

    Example:
        >>> status = ConversionStatus.COMPLETED
        >>> if status == ConversionStatus.COMPLETED:
        ...     print("转换成功")
        转换成功
    """
    PENDING = auto()      # 待处理：文件已添加，等待开始处理
    PROCESSING = auto()   # 处理中：文件正在被转换
    COMPLETED = auto()    # 已完成：转换成功完成
    FAILED = auto()       # 失败：转换过程中出现错误
    CANCELLED = auto()    # 已取消：用户主动取消转换


class FileFormat(Enum):
    """
    文件格式枚举

    定义应用程序支持的所有文件格式。

    Attributes:
        图片格式: JPG, JPEG, PNG, BMP, TIFF, GIF, WEBP
        文档格式: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, HTML, HTM
        其他格式: CSV, RTF

    Example:
        >>> format_type = FileFormat.PDF
        >>> print(format_type.value)
        'pdf'
    """
    # ==================== 图片格式 ====================
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    GIF = "gif"
    WEBP = "webp"

    # ==================== 文档格式 ====================
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"
    PPT = "ppt"
    PPTX = "pptx"
    TXT = "txt"
    HTML = "html"
    HTM = "htm"

    # ==================== 其他格式 ====================
    CSV = "csv"
    RTF = "rtf"


# ==================== 图片格式列表 ====================
# 包含所有支持的图片格式，用于图片转PDF等功能
IMAGE_FORMATS: List[FileFormat] = [
    FileFormat.JPG,
    FileFormat.JPEG,
    FileFormat.PNG,
    FileFormat.BMP,
    FileFormat.TIFF,
    FileFormat.GIF,
    FileFormat.WEBP,
]

# 图片扩展名列表（字符串形式）
# 用于文件类型检测和过滤
IMAGE_EXTENSIONS: List[str] = [fmt.value for fmt in IMAGE_FORMATS]

# ==================== Excel格式列表 ====================
# Excel扩展名列表（字符串形式）
# 用于文件类型检测和过滤
EXCEL_EXTENSIONS: List[str] = ['xls', 'xlsx']


# ==================== 文档格式映射 ====================
# 将文档类型映射到对应的文件格式列表
# 用于根据文档类型获取支持的文件扩展名
DOCUMENT_FORMATS: Dict[str, List[FileFormat]] = {
    'word': [FileFormat.DOC, FileFormat.DOCX],           # Word文档
    'excel': [FileFormat.XLS, FileFormat.XLSX],          # Excel表格
    'powerpoint': [FileFormat.PPT, FileFormat.PPTX],     # PowerPoint演示文稿
    'text': [FileFormat.TXT],                             # 纯文本文件
}


# ==================== 功能模块名称映射 ====================
# 将模块标识符映射到用户友好的中文名称
# 用于在GUI中显示功能列表
MODULE_NAMES: Dict[str, str] = {
    # 文档转换类
    'image_to_pdf': '图片转PDF',      # 将图片文件转换为PDF文档
    'pdf_to_image': 'PDF转图片',      # 将PDF文档转换为图片
    'pdf_to_excel': 'PDF转Excel',     # 从PDF中提取表格到Excel
    'pdf_to_word': 'PDF转Word',       # 将PDF转换为Word文档
    'word_to_pdf': 'Word转PDF',       # 将Word文档转换为PDF
    'ppt_to_pdf': 'PPT转PDF',         # 将PowerPoint转换为PDF
    'excel_to_pdf': 'Excel转PDF',    # 将Excel表格转换为PDF
    'txt_to_pdf': 'TXT转PDF',         # 将文本文件转换为PDF
    'doc_to_pdf': '文档转PDF',        # 通用文档转PDF（自动识别类型）

    # PDF处理类
    'pdf_merge': 'PDF合并',           # 合并多个PDF文件
    'pdf_split': 'PDF拆分',           # 拆分PDF文件
    'pdf_compress': 'PDF压缩',        # 压缩PDF文件大小

    # PDF高级处理类（新增）
    'pdf_extract_images': 'PDF提取图片',    # 从PDF中提取图片
    'pdf_add_remove_pages': 'PDF增删页',    # PDF页面增删
    'pdf_rotate': 'PDF旋转页面',            # 旋转PDF页面
    'pdf_organize': 'PDF编排页面',          # PDF页面编排
    'pdf_to_long_image': 'PDF转长图',       # PDF转长图
    'pdf_to_grayscale': 'PDF转黑白',         # PDF转黑白
    'pdf_add_page_numbers': 'PDF添加页码',   # PDF添加页码
    'pdf_crop_split': 'PDF分割裁剪',         # PDF分割裁剪
    'pdf_page_merge': 'PDF页面合并',         # PDF页面合并
    'pdf_remove_watermark': 'PDF去水印',     # PDF去水印
    'pdf_add_watermark': 'PDF加水印',         # PDF加水印
    'pdf_encrypt': 'PDF加密',               # PDF加密
    'invoice_merge': '发票合并',            # 发票合并
}


# ==================== 文件大小单位 ====================
# 用于文件大小格式化显示
SIZE_UNITS: List[str] = ['B', 'KB', 'MB', 'GB', 'TB']


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示

    将字节数转换为人类可读的文件大小字符串。

    Args:
        size_bytes: 文件大小（字节），必须为非负整数

    Returns:
        str: 格式化后的文件大小字符串，保留两位小数
            例如: "0 B", "1.00 KB", "1.50 MB", "2.00 GB"

    Example:
        >>> format_file_size(0)
        '0 B'
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1536)
        '1.50 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
        >>> format_file_size(1073741824)
        '1.00 GB'
    """
    # 处理零值情况
    if size_bytes == 0:
        return "0 B"

    # 初始化单位和大小
    unit_index = 0
    size = float(size_bytes)

    # 不断除以1024直到找到合适的单位
    # 或者到达最大单位(TB)
    while size >= 1024 and unit_index < len(SIZE_UNITS) - 1:
        size /= 1024
        unit_index += 1

    # 返回格式化后的字符串，保留两位小数
    return f"{size:.2f} {SIZE_UNITS[unit_index]}"


def get_file_format(extension: str) -> FileFormat:
    """
    根据文件扩展名获取文件格式枚举

    Args:
        extension: 文件扩展名（不含点号），如 "pdf", "jpg"

    Returns:
        FileFormat: 对应的文件格式枚举值

    Raises:
        ValueError: 如果扩展名不被支持

    Example:
        >>> get_file_format("pdf")
        <FileFormat.PDF: 'pdf'>
        >>> get_file_format("jpg")
        <FileFormat.JPG: 'jpg'>
    """
    extension = extension.lower()

    for file_format in FileFormat:
        if file_format.value == extension:
            return file_format

    raise ValueError(f"不支持的文件格式: {extension}")


def is_image_extension(extension: str) -> bool:
    """
    检查扩展名是否为图片格式

    Args:
        extension: 文件扩展名（不含点号），如 "jpg", "png"

    Returns:
        bool: 如果是图片格式返回True，否则返回False

    Example:
        >>> is_image_extension("jpg")
        True
        >>> is_image_extension("pdf")
        False
    """
    return extension.lower() in IMAGE_EXTENSIONS


def is_document_extension(extension: str) -> bool:
    """
    检查扩展名是否为文档格式

    Args:
        extension: 文件扩展名（不含点号），如 "pdf", "docx"

    Returns:
        bool: 如果是文档格式返回True，否则返回False

    Example:
        >>> is_document_extension("pdf")
        True
        >>> is_document_extension("jpg")
        False
    """
    extension = extension.lower()
    doc_extensions = []

    # 收集所有文档格式的扩展名
    for formats in DOCUMENT_FORMATS.values():
        doc_extensions.extend([f.value for f in formats])

    # 添加PDF格式
    doc_extensions.append(FileFormat.PDF.value)

    return extension in doc_extensions