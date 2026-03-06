# -*- coding: utf-8 -*-
"""
Converters模块初始化

该模块提供所有文件格式转换器，包括：

核心转换器（无额外依赖）：
- ImageToPdfConverter: 图片转PDF
- PdfToImageConverter: PDF转图片（需要poppler）
- PdfMergeConverter: PDF合并
- PdfSplitConverter: PDF拆分
- PdfCompressConverter: PDF压缩

文档转换器（需要相应依赖）：
- TxtToPdfConverter: TXT转PDF
- WordToPdfConverter: Word转PDF
- PptToPdfConverter: PPT转PDF
- ExcelToPdfConverter: Excel转PDF
- PdfToWordConverter: PDF转Word
- PdfToExcelConverter: PDF转Excel

其他转换器：
- DocToPdfConverter: 通用文档转PDF

新增PDF处理转换器：
- PdfExtractImagesConverter: PDF提取图片
- PdfAddRemovePagesConverter: PDF增删页
- PdfRotateConverter: PDF旋转页面
- PdfOrganizeConverter: PDF编排页面
- PdfToLongImageConverter: PDF转长图
- PdfToGrayscaleConverter: PDF转黑白
- PdfAddPageNumbersConverter: PDF添加页码
- PdfCropSplitConverter: PDF分割裁剪
- PdfPageMergeConverter: PDF页面合并
- PdfRemoveWatermarkConverter: PDF去水印
- PdfAddWatermarkConverter: PDF加水印
- PdfEncryptConverter: PDF加密
- InvoiceMergeConverter: 发票合并

使用方式：
    from converters import register_all_converters, ImageToPdfConverter

    # 注册所有转换器
    from core.dispatcher import TaskDispatcher
    dispatcher = TaskDispatcher()
    register_all_converters(dispatcher)

    # 直接使用转换器
    converter = ImageToPdfConverter()
    results = converter.convert([Path("image.jpg")], Path("output"))
"""
from typing import TYPE_CHECKING

# 导入核心转换器（无额外依赖）
from converters.image_to_pdf import ImageToPdfConverter
from converters.pdf_to_image import PdfToImageConverter
from converters.pdf_merge import PdfMergeConverter
from converters.pdf_split import PdfSplitConverter
from converters.pdf_compress import PdfCompressConverter

# 导入新增PDF处理转换器
from converters.pdf_extract_images import PdfExtractImagesConverter
from converters.pdf_add_remove_pages import PdfAddRemovePagesConverter
from converters.pdf_rotate import PdfRotateConverter
from converters.pdf_organize import PdfOrganizeConverter
from converters.pdf_to_long_image import PdfToLongImageConverter
from converters.pdf_to_grayscale import PdfToGrayscaleConverter
from converters.pdf_add_page_numbers import PdfAddPageNumbersConverter
from converters.pdf_crop_split import PdfCropSplitConverter
from converters.pdf_page_merge import PdfPageMergeConverter
from converters.pdf_remove_watermark import PdfRemoveWatermarkConverter
from converters.pdf_add_watermark import PdfAddWatermarkConverter
from converters.pdf_encrypt import PdfEncryptConverter
from converters.invoice_merge import InvoiceMergeConverter

if TYPE_CHECKING:
    from core.dispatcher import TaskDispatcher


def register_all_converters(dispatcher: 'TaskDispatcher') -> None:
    """
    注册所有转换器到调度器

    该函数将所有可用的转换器注册到任务调度器。
    某些转换器可能因为依赖缺失而无法导入，
    这些转换器会被跳过并记录警告日志。

    Args:
        dispatcher: 任务调度器实例

    Example:
        >>> from core.dispatcher import TaskDispatcher
        >>> dispatcher = TaskDispatcher()
        >>> register_all_converters(dispatcher)
    """
    from utils.logger import get_logger
    logger = get_logger(__name__)

    logger.info("开始注册转换器...")

    # ==================== 核心转换器 ====================
    # 这些转换器依赖已验证，总是可用

    # 图片转PDF
    try:
        dispatcher.register_converter(ImageToPdfConverter())
        logger.debug("注册转换器: 图片转PDF")
    except Exception as e:
        logger.error(f"注册转换器失败 [图片转PDF]: {e}")

    # PDF转图片
    try:
        dispatcher.register_converter(PdfToImageConverter())
        logger.debug("注册转换器: PDF转图片")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF转图片]: {e}")

    # PDF合并
    try:
        dispatcher.register_converter(PdfMergeConverter())
        logger.debug("注册转换器: PDF合并")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF合并]: {e}")

    # PDF拆分
    try:
        dispatcher.register_converter(PdfSplitConverter())
        logger.debug("注册转换器: PDF拆分")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF拆分]: {e}")

    # PDF压缩
    try:
        dispatcher.register_converter(PdfCompressConverter())
        logger.debug("注册转换器: PDF压缩")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF压缩]: {e}")

    # ==================== 文档转换器 ====================
    # 这些转换器可能因为依赖缺失而不可用

    # TXT转PDF
    try:
        from converters.txt_to_pdf import TxtToPdfConverter
        dispatcher.register_converter(TxtToPdfConverter())
        logger.debug("注册转换器: TXT转PDF")
    except ImportError as e:
        logger.warning(f"跳过转换器 [TXT转PDF]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [TXT转PDF]: {e}")

    # Word转PDF
    try:
        from converters.word_to_pdf import WordToPdfConverter
        dispatcher.register_converter(WordToPdfConverter())
        logger.debug("注册转换器: Word转PDF")
    except ImportError as e:
        logger.warning(f"跳过转换器 [Word转PDF]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [Word转PDF]: {e}")

    # PPT转PDF
    try:
        from converters.ppt_to_pdf import PptToPdfConverter
        dispatcher.register_converter(PptToPdfConverter())
        logger.debug("注册转换器: PPT转PDF")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PPT转PDF]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PPT转PDF]: {e}")

    # Excel转PDF
    try:
        from converters.excel_to_pdf import ExcelToPdfConverter
        dispatcher.register_converter(ExcelToPdfConverter())
        logger.debug("注册转换器: Excel转PDF")
    except ImportError as e:
        logger.warning(f"跳过转换器 [Excel转PDF]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [Excel转PDF]: {e}")

    # PDF转Word
    try:
        from converters.pdf_to_word import PdfToWordConverter
        dispatcher.register_converter(PdfToWordConverter())
        logger.debug("注册转换器: PDF转Word")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF转Word]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF转Word]: {e}")

    # PDF转Excel
    try:
        from converters.pdf_to_excel import PdfToExcelConverter
        dispatcher.register_converter(PdfToExcelConverter())
        logger.debug("注册转换器: PDF转Excel")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF转Excel]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF转Excel]: {e}")

    # ==================== 其他转换器 ====================

    # 通用文档转PDF
    try:
        from converters.doc_to_pdf import DocToPdfConverter
        dispatcher.register_converter(DocToPdfConverter())
        logger.debug("注册转换器: 文档转PDF")
    except ImportError as e:
        logger.warning(f"跳过转换器 [文档转PDF]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [文档转PDF]: {e}")

    # ==================== 新增PDF处理转换器 ====================

    # PDF提取图片
    try:
        from converters.pdf_extract_images import PdfExtractImagesConverter
        dispatcher.register_converter(PdfExtractImagesConverter())
        logger.debug("注册转换器: PDF提取图片")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF提取图片]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF提取图片]: {e}")

    # PDF增删页
    try:
        from converters.pdf_add_remove_pages import PdfAddRemovePagesConverter
        dispatcher.register_converter(PdfAddRemovePagesConverter())
        logger.debug("注册转换器: PDF增删页")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF增删页]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF增删页]: {e}")

    # PDF旋转页面
    try:
        from converters.pdf_rotate import PdfRotateConverter
        dispatcher.register_converter(PdfRotateConverter())
        logger.debug("注册转换器: PDF旋转页面")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF旋转页面]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF旋转页面]: {e}")

    # PDF编排页面
    try:
        from converters.pdf_organize import PdfOrganizeConverter
        dispatcher.register_converter(PdfOrganizeConverter())
        logger.debug("注册转换器: PDF编排页面")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF编排页面]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF编排页面]: {e}")

    # PDF转长图
    try:
        from converters.pdf_to_long_image import PdfToLongImageConverter
        dispatcher.register_converter(PdfToLongImageConverter())
        logger.debug("注册转换器: PDF转长图")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF转长图]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF转长图]: {e}")

    # PDF转黑白
    try:
        from converters.pdf_to_grayscale import PdfToGrayscaleConverter
        dispatcher.register_converter(PdfToGrayscaleConverter())
        logger.debug("注册转换器: PDF转黑白")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF转黑白]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF转黑白]: {e}")

    # PDF添加页码
    try:
        from converters.pdf_add_page_numbers import PdfAddPageNumbersConverter
        dispatcher.register_converter(PdfAddPageNumbersConverter())
        logger.debug("注册转换器: PDF添加页码")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF添加页码]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF添加页码]: {e}")

    # PDF分割裁剪
    try:
        from converters.pdf_crop_split import PdfCropSplitConverter
        dispatcher.register_converter(PdfCropSplitConverter())
        logger.debug("注册转换器: PDF分割裁剪")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF分割裁剪]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF分割裁剪]: {e}")

    # PDF页面合并
    try:
        from converters.pdf_page_merge import PdfPageMergeConverter
        dispatcher.register_converter(PdfPageMergeConverter())
        logger.debug("注册转换器: PDF页面合并")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF页面合并]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF页面合并]: {e}")

    # PDF去水印
    try:
        from converters.pdf_remove_watermark import PdfRemoveWatermarkConverter
        dispatcher.register_converter(PdfRemoveWatermarkConverter())
        logger.debug("注册转换器: PDF去水印")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF去水印]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF去水印]: {e}")

    # PDF加水印
    try:
        from converters.pdf_add_watermark import PdfAddWatermarkConverter
        dispatcher.register_converter(PdfAddWatermarkConverter())
        logger.debug("注册转换器: PDF加水印")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF加水印]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF加水印]: {e}")

    # PDF加密
    try:
        from converters.pdf_encrypt import PdfEncryptConverter
        dispatcher.register_converter(PdfEncryptConverter())
        logger.debug("注册转换器: PDF加密")
    except ImportError as e:
        logger.warning(f"跳过转换器 [PDF加密]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [PDF加密]: {e}")

    # 发票合并
    try:
        from converters.invoice_merge import InvoiceMergeConverter
        dispatcher.register_converter(InvoiceMergeConverter())
        logger.debug("注册转换器: 发票合并")
    except ImportError as e:
        logger.warning(f"跳过转换器 [发票合并]: 依赖缺失 - {e}")
    except Exception as e:
        logger.error(f"注册转换器失败 [发票合并]: {e}")

    # 统计已注册的转换器
    converters = dispatcher.get_all_converters()
    logger.info(f"转换器注册完成，共注册 {len(converters)} 个转换器")


# ==================== 导出 ====================
__all__ = [
    # 核心转换器（直接导入）
    'ImageToPdfConverter',
    'PdfToImageConverter',
    'PdfMergeConverter',
    'PdfSplitConverter',
    'PdfCompressConverter',

    # 新增PDF处理转换器（直接导入）
    'PdfExtractImagesConverter',
    'PdfAddRemovePagesConverter',
    'PdfRotateConverter',
    'PdfOrganizeConverter',
    'PdfToLongImageConverter',
    'PdfToGrayscaleConverter',
    'PdfAddPageNumbersConverter',
    'PdfCropSplitConverter',
    'PdfPageMergeConverter',
    'PdfRemoveWatermarkConverter',
    'PdfAddWatermarkConverter',
    'PdfEncryptConverter',
    'InvoiceMergeConverter',

    # 工具函数
    'register_all_converters',
]