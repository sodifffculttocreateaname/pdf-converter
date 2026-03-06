# -*- coding: utf-8 -*-
"""
主窗口模块

该模块是PDF工具箱的主界面，提供：
- 左侧功能导航列表
- 右侧功能页面区域（使用堆栈窗口切换）
- 各功能模块的独立页面

布局结构:
┌─────────────────────────────────────────────────────────┐
│  PDF工具箱                                              │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  功能列表    │         功能页面区域                     │
│              │      (根据选择切换不同页面)              │
│  ...         │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
"""
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget
)

from config.constants import MODULE_NAMES
from config.settings import Settings
from gui.styles import get_stylesheet
from gui.pages import (
    ImageToPdfPage, PdfToImagePage, PdfToExcelPage, PdfToWordPage, PdfMergePage,
    PdfSplitPage, PdfCompressPage, DocToPdfPage, WordToPdfPage, TxtToPdfPage,
    ExcelToPdfPage, PptToPdfPage,
    PdfExtractImagesPage, PdfAddRemovePagesPage, PdfRotatePage, PdfOrganizePage,
    PdfToLongImagePage, PdfToGrayscalePage, PdfAddPageNumbersPage, PdfCropSplitPage,
    PdfPageMergePage, PdfRemoveWatermarkPage, PdfAddWatermarkPage, PdfEncryptPage,
    InvoiceMergePage
)
from utils.logger import get_logger


logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    主窗口类

    提供PDF工具箱的主界面，包含左侧功能导航和右侧功能页面区域。

    Attributes:
        _function_list: 功能列表控件
        _page_stack: 页面堆栈控件
        _pages: 功能页面字典
        _status_bar: 状态栏
    """

    # 转换开始信号
    conversion_started = Signal()
    # 转换完成信号
    conversion_finished = Signal()

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 功能页面字典
        self._pages: Dict[str, QWidget] = {}

        # 初始化UI
        self._init_ui()

        logger.info("主窗口初始化完成")

    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle(Settings.APP_NAME)
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        # 设置样式
        self.setStyleSheet(get_stylesheet())

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建左侧面板 - 功能列表
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # 创建右侧面板 - 页面堆栈
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("请从左侧选择功能")

    def _create_left_panel(self) -> QWidget:
        """
        创建左侧功能导航面板

        Returns:
            QWidget: 左侧面板
        """
        panel = QWidget()
        panel.setMinimumWidth(150)
        panel.setMaximumWidth(250)
        panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QLabel("功能列表")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            color: #333;
        """)
        layout.addWidget(title)

        # 功能列表
        self._function_list = QListWidget()
        self._function_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-radius: 6px;
                margin: 2px 0;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #e9ecef;
            }
        """)

        # 添加功能项
        for module_key, module_name in MODULE_NAMES.items():
            item = QListWidgetItem(module_name)
            item.setData(Qt.ItemDataRole.UserRole, module_key)
            self._function_list.addItem(item)

        # 连接选择信号
        self._function_list.currentRowChanged.connect(self._on_function_changed)

        layout.addWidget(self._function_list)

        return panel

    def _create_right_panel(self) -> QWidget:
        """
        创建右侧页面堆栈面板

        Returns:
            QWidget: 右侧面板
        """
        panel = QWidget()
        panel.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建页面堆栈
        self._page_stack = QStackedWidget()

        # 创建欢迎页面
        welcome_page = self._create_welcome_page()
        self._page_stack.addWidget(welcome_page)

        # 创建图片转PDF页面
        image_to_pdf_page = ImageToPdfPage()
        self._pages['image_to_pdf'] = image_to_pdf_page
        self._page_stack.addWidget(image_to_pdf_page)

        # 创建PDF转图片页面
        pdf_to_image_page = PdfToImagePage()
        self._pages['pdf_to_image'] = pdf_to_image_page
        self._page_stack.addWidget(pdf_to_image_page)

        # 创建PDF转Excel页面
        pdf_to_excel_page = PdfToExcelPage()
        self._pages['pdf_to_excel'] = pdf_to_excel_page
        self._page_stack.addWidget(pdf_to_excel_page)

        # 创建PDF转Word页面
        pdf_to_word_page = PdfToWordPage()
        self._pages['pdf_to_word'] = pdf_to_word_page
        self._page_stack.addWidget(pdf_to_word_page)

        # 创建PDF合并页面
        pdf_merge_page = PdfMergePage()
        self._pages['pdf_merge'] = pdf_merge_page
        self._page_stack.addWidget(pdf_merge_page)

        # 创建Word转PDF页面
        word_to_pdf_page = WordToPdfPage()
        self._pages['word_to_pdf'] = word_to_pdf_page
        self._page_stack.addWidget(word_to_pdf_page)

        # 创建TXT转PDF页面
        txt_to_pdf_page = TxtToPdfPage()
        self._pages['txt_to_pdf'] = txt_to_pdf_page
        self._page_stack.addWidget(txt_to_pdf_page)

        # 创建PDF压缩页面
        pdf_compress_page = PdfCompressPage()
        self._pages['pdf_compress'] = pdf_compress_page
        self._page_stack.addWidget(pdf_compress_page)

        # 创建PDF拆分页面
        pdf_split_page = PdfSplitPage()
        self._pages['pdf_split'] = pdf_split_page
        self._page_stack.addWidget(pdf_split_page)

        # 创建Excel转PDF页面
        excel_to_pdf_page = ExcelToPdfPage()
        self._pages['excel_to_pdf'] = excel_to_pdf_page
        self._page_stack.addWidget(excel_to_pdf_page)

        # 创建PPT转PDF页面
        ppt_to_pdf_page = PptToPdfPage()
        self._pages['ppt_to_pdf'] = ppt_to_pdf_page
        self._page_stack.addWidget(ppt_to_pdf_page)

        # 创建通用文档转PDF页面
        doc_to_pdf_page = DocToPdfPage()
        self._pages['doc_to_pdf'] = doc_to_pdf_page
        self._page_stack.addWidget(doc_to_pdf_page)

        # ==================== 新增PDF处理页面 ====================

        # 创建PDF提取图片页面
        pdf_extract_images_page = PdfExtractImagesPage()
        self._pages['pdf_extract_images'] = pdf_extract_images_page
        self._page_stack.addWidget(pdf_extract_images_page)

        # 创建PDF增删页页面
        pdf_add_remove_pages_page = PdfAddRemovePagesPage()
        self._pages['pdf_add_remove_pages'] = pdf_add_remove_pages_page
        self._page_stack.addWidget(pdf_add_remove_pages_page)

        # 创建PDF旋转页面
        pdf_rotate_page = PdfRotatePage()
        self._pages['pdf_rotate'] = pdf_rotate_page
        self._page_stack.addWidget(pdf_rotate_page)

        # 创建PDF编排页面
        pdf_organize_page = PdfOrganizePage()
        self._pages['pdf_organize'] = pdf_organize_page
        self._page_stack.addWidget(pdf_organize_page)

        # 创建PDF转长图页面
        pdf_to_long_image_page = PdfToLongImagePage()
        self._pages['pdf_to_long_image'] = pdf_to_long_image_page
        self._page_stack.addWidget(pdf_to_long_image_page)

        # 创建PDF转黑白页面
        pdf_to_grayscale_page = PdfToGrayscalePage()
        self._pages['pdf_to_grayscale'] = pdf_to_grayscale_page
        self._page_stack.addWidget(pdf_to_grayscale_page)

        # 创建PDF添加页码页面
        pdf_add_page_numbers_page = PdfAddPageNumbersPage()
        self._pages['pdf_add_page_numbers'] = pdf_add_page_numbers_page
        self._page_stack.addWidget(pdf_add_page_numbers_page)

        # 创建PDF分割裁剪页面
        pdf_crop_split_page = PdfCropSplitPage()
        self._pages['pdf_crop_split'] = pdf_crop_split_page
        self._page_stack.addWidget(pdf_crop_split_page)

        # 创建PDF页面合并页面
        pdf_page_merge_page = PdfPageMergePage()
        self._pages['pdf_page_merge'] = pdf_page_merge_page
        self._page_stack.addWidget(pdf_page_merge_page)

        # 创建PDF去水印页面
        pdf_remove_watermark_page = PdfRemoveWatermarkPage()
        self._pages['pdf_remove_watermark'] = pdf_remove_watermark_page
        self._page_stack.addWidget(pdf_remove_watermark_page)

        # 创建PDF加水印页面
        pdf_add_watermark_page = PdfAddWatermarkPage()
        self._pages['pdf_add_watermark'] = pdf_add_watermark_page
        self._page_stack.addWidget(pdf_add_watermark_page)

        # 创建PDF加密页面
        pdf_encrypt_page = PdfEncryptPage()
        self._pages['pdf_encrypt'] = pdf_encrypt_page
        self._page_stack.addWidget(pdf_encrypt_page)

        # 创建发票合并页面
        invoice_merge_page = InvoiceMergePage()
        self._pages['invoice_merge'] = invoice_merge_page
        self._page_stack.addWidget(invoice_merge_page)

        # 已实现的页面列表（不创建占位页面）
        implemented_pages = [
            'image_to_pdf', 'pdf_to_image', 'pdf_to_excel', 'pdf_to_word', 'pdf_merge',
            'word_to_pdf', 'txt_to_pdf', 'pdf_compress', 'pdf_split',
            'excel_to_pdf', 'ppt_to_pdf', 'doc_to_pdf',
            'pdf_extract_images', 'pdf_add_remove_pages', 'pdf_rotate', 'pdf_organize',
            'pdf_to_long_image', 'pdf_to_grayscale', 'pdf_add_page_numbers', 'pdf_crop_split',
            'pdf_page_merge', 'pdf_remove_watermark', 'pdf_add_watermark', 'pdf_encrypt',
            'invoice_merge'
        ]

        # 创建其他功能的占位页面
        for module_key in MODULE_NAMES.keys():
            if module_key not in implemented_pages:
                placeholder = self._create_placeholder_page(module_key)
                self._pages[module_key] = placeholder
                self._page_stack.addWidget(placeholder)

        layout.addWidget(self._page_stack)

        return panel

    def _create_welcome_page(self) -> QWidget:
        """
        创建欢迎页面

        Returns:
            QWidget: 欢迎页面
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_label = QLabel("欢迎使用 PDF 工具箱")
        welcome_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        hint_label = QLabel("请从左侧选择要使用的功能")
        hint_label.setStyleSheet("""
            font-size: 16px;
            color: #666;
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        return page

    def _create_placeholder_page(self, module_key: str) -> QWidget:
        """
        创建占位页面（用于尚未开发的功能）

        Args:
            module_key: 模块标识符

        Returns:
            QWidget: 占位页面
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        module_name = MODULE_NAMES.get(module_key, module_key)

        title_label = QLabel(module_name)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        hint_label = QLabel("该功能页面正在开发中...")
        hint_label.setStyleSheet("""
            font-size: 16px;
            color: #999;
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        return page

    def _on_function_changed(self, row: int):
        """
        功能选择变化处理

        Args:
            row: 选中的行号
        """
        item = self._function_list.item(row)
        if not item:
            return

        module_key = item.data(Qt.ItemDataRole.UserRole)
        module_name = MODULE_NAMES.get(module_key, module_key)

        # 切换到对应页面
        if module_key in self._pages:
            self._page_stack.setCurrentWidget(self._pages[module_key])

        # 更新状态栏
        self._status_bar.showMessage(f"已选择: {module_name}")

        logger.debug(f"切换到功能: {module_key}")

    def closeEvent(self, event):
        """
        窗口关闭事件

        检查是否有正在进行的任务，提示用户确认。

        Args:
            event: 关闭事件
        """
        # 检查图片转PDF页面是否正在转换
        if 'image_to_pdf' in self._pages:
            page = self._pages['image_to_pdf']
            if hasattr(page, '_worker') and page._worker and page._worker.isRunning():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                page._worker.cancel()
                page._worker.wait()

        # 检查PDF转图片页面是否正在转换
        if 'pdf_to_image' in self._pages:
            page = self._pages['pdf_to_image']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查PDF转Excel页面是否正在转换
        if 'pdf_to_excel' in self._pages:
            page = self._pages['pdf_to_excel']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查PDF转Word页面是否正在转换
        if 'pdf_to_word' in self._pages:
            page = self._pages['pdf_to_word']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查PDF合并页面是否正在进行合并
        if 'pdf_merge' in self._pages:
            page = self._pages['pdf_merge']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查TXT转PDF页面是否正在转换
        if 'txt_to_pdf' in self._pages:
            page = self._pages['txt_to_pdf']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

                # 检查Word转PDF页面是否正在转换
        if 'word_to_pdf' in self._pages:
            page = self._pages['word_to_pdf' ]
            if hasattr(page, 'is_converting' ) and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查PDF压缩页面是否正在进行压缩
        if 'pdf_compress' in self._pages:
            page = self._pages['pdf_compress']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查PDF拆分页面是否正在进行拆分
        if 'pdf_split' in self._pages:
            page = self._pages['pdf_split']
            if hasattr(page, 'is_splitting') and page.is_splitting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查Excel转PDF页面是否正在转换
        if 'excel_to_pdf' in self._pages:
            page = self._pages['excel_to_pdf']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查PPT转PDF页面是否正在转换
        if 'ppt_to_pdf' in self._pages:
            page = self._pages['ppt_to_pdf']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # 检查通用文档转PDF页面是否正在转换
        if 'doc_to_pdf' in self._pages:
            page = self._pages['doc_to_pdf']
            if hasattr(page, 'is_converting') and page.is_converting():
                reply = QMessageBox.question(
                    self,
                    "确认退出",
                    "正在处理任务，确定要退出吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return

                # 取消正在进行的任务
                if page._worker:
                    page._worker.cancel()
                    page._worker.wait()

        # ==================== 检查新增PDF处理页面 ====================

        # 定义需要检查的新页面列表
        new_pages_to_check = [
            'pdf_extract_images', 'pdf_add_remove_pages', 'pdf_rotate', 'pdf_organize',
            'pdf_to_long_image', 'pdf_to_grayscale', 'pdf_add_page_numbers', 'pdf_crop_split',
            'pdf_page_merge', 'pdf_remove_watermark', 'pdf_add_watermark', 'pdf_encrypt',
            'invoice_merge'
        ]

        for page_key in new_pages_to_check:
            if page_key in self._pages:
                page = self._pages[page_key]
                if hasattr(page, 'is_converting') and page.is_converting():
                    reply = QMessageBox.question(
                        self,
                        "确认退出",
                        "正在处理任务，确定要退出吗？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.No:
                        event.ignore()
                        return

                    # 取消正在进行的任务
                    if hasattr(page, '_worker') and page._worker:
                        page._worker.cancel()
                        page._worker.wait()

        event.accept()