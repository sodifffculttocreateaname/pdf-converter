# -*- coding: utf-8 -*-
"""
功能模块页面包

该包包含各个功能模块的独立页面组件。
每个功能模块都有自己独立的页面，代码完全分离。

可用的页面模块：
- image_to_pdf_page: 图片转PDF页面
- pdf_to_image_page: PDF转图片页面
- pdf_to_excel_page: PDF转Excel页面
- pdf_to_word_page: PDF转Word页面
- pdf_merge_page: PDF合并页面
- pdf_split_page: PDF拆分页面
- excel_to_pdf_page: Excel转PDF页面
- word_to_pdf_page: Word转PDF页面
- pdf_compress_page: PDF压缩页面
- doc_to_pdf_page: 通用文档转PDF页面
- txt_to_pdf_page: TXT转PDF页面
- ppt_to_pdf_page: PPT转PDF页面
- pdf_extract_images_page: PDF提取图片页面
- pdf_add_remove_pages_page: PDF增删页页面
- pdf_rotate_page: PDF旋转页面页面
- pdf_organize_page: PDF编排页面页面
- pdf_to_long_image_page: PDF转长图页面
- pdf_to_grayscale_page: PDF转黑白页面
- pdf_add_page_numbers_page: PDF添加页码页面
- pdf_crop_split_page: PDF分割裁剪页面
- pdf_page_merge_page: PDF页面合并页面
- pdf_remove_watermark_page: PDF去水印页面
- pdf_add_watermark_page: PDF加水印页面
- pdf_encrypt_page: PDF加密页面
- invoice_merge_page: 发票合并页面
"""

from gui.pages.image_to_pdf_page import ImageToPdfPage
from gui.pages.pdf_to_image_page import PdfToImagePage
from gui.pages.pdf_to_excel_page import PdfToExcelPage
from gui.pages.pdf_to_word_page import PdfToWordPage
from gui.pages.pdf_merge_page import PdfMergePage
from gui.pages.pdf_split_page import PdfSplitPage
from gui.pages.excel_to_pdf_page import ExcelToPdfPage
from gui.pages.word_to_pdf_page import WordToPdfPage
from gui.pages.pdf_compress_page import PdfCompressPage
from gui.pages.doc_to_pdf_page import DocToPdfPage
from gui.pages.txt_to_pdf_page import TxtToPdfPage
from gui.pages.ppt_to_pdf_page import PptToPdfPage
from gui.pages.pdf_extract_images_page import PdfExtractImagesPage
from gui.pages.pdf_add_remove_pages_page import PdfAddRemovePagesPage
from gui.pages.pdf_rotate_page import PdfRotatePage
from gui.pages.pdf_organize_page import PdfOrganizePage
from gui.pages.pdf_to_long_image_page import PdfToLongImagePage
from gui.pages.pdf_to_grayscale_page import PdfToGrayscalePage
from gui.pages.pdf_add_page_numbers_page import PdfAddPageNumbersPage
from gui.pages.pdf_crop_split_page import PdfCropSplitPage
from gui.pages.pdf_page_merge_page import PdfPageMergePage
from gui.pages.pdf_remove_watermark_page import PdfRemoveWatermarkPage
from gui.pages.pdf_add_watermark_page import PdfAddWatermarkPage
from gui.pages.pdf_encrypt_page import PdfEncryptPage
from gui.pages.invoice_merge_page import InvoiceMergePage

__all__ = [
    'ImageToPdfPage',
    'PdfToImagePage',
    'PdfToExcelPage',
    'PdfToWordPage',
    'PdfMergePage',
    'PdfSplitPage',
    'ExcelToPdfPage',
    'WordToPdfPage',
    'PdfCompressPage',
    'DocToPdfPage',
    'TxtToPdfPage',
    'PptToPdfPage',
    'PdfExtractImagesPage',
    'PdfAddRemovePagesPage',
    'PdfRotatePage',
    'PdfOrganizePage',
    'PdfToLongImagePage',
    'PdfToGrayscalePage',
    'PdfAddPageNumbersPage',
    'PdfCropSplitPage',
    'PdfPageMergePage',
    'PdfRemoveWatermarkPage',
    'PdfAddWatermarkPage',
    'PdfEncryptPage',
    'InvoiceMergePage',
]
