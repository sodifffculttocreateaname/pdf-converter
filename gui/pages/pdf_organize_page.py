# -*- coding: utf-8 -*-
"""
PDF编排页面功能页面

该模块提供PDF页面编排功能的完整界面，包括：
- PDF文件拖拽上传区域
- 页面缩略图预览
- 页面拖拽排序
- 复制/删除操作
- 进度显示和取消功能
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QVBoxLayout,
    QWidget
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.pdf_organize import PdfOrganizeConverter
from core.base_converter import ConversionProgress, ConversionResult
from utils.file_utils import get_file_size, ensure_dir
from utils.logger import get_logger


logger = get_logger(__name__)


class ConversionWorker(QThread):
    """转换工作线程"""
    progress = Signal(object)
    finished = Signal(list)

    def __init__(self, converter: PdfOrganizeConverter, file: Path,
                 output_dir: Path, page_order: List[int], parent=None):
        super().__init__(parent)
        self._converter = converter
        self._file = file
        self._output_dir = output_dir
        self._page_order = page_order
        self._cancelled = False

    def run(self):
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)
        self._converter.set_progress_callback(on_progress)
        self._converter.set_page_order(self._page_order)
        results = self._converter.convert([self._file], self._output_dir)
        self.finished.emit(results)

    def cancel(self):
        self._cancelled = True
        self._converter.cancel()


class PdfOrganizePage(QWidget):
    """PDF编排页面功能页面"""
    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._file: Optional[Path] = None
        self._page_count = 0
        self._page_order: List[int] = []
        self._converter = PdfOrganizeConverter()
        self._worker: Optional[ConversionWorker] = None
        self._init_ui()
        logger.info("PDF编排页面初始化完成")

    def _init_ui(self):
        """初始化UI"""
        # 主布局 - 水平分栏：左侧文件区域 | 右侧设置区域
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ==================== 左侧：文件管理区域 ====================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 标题
        self._title_label = QLabel("PDF编排")
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_layout.addWidget(self._title_label)

        # 说明
        desc_label = QLabel("调整PDF页面顺序，支持拖拽排序、复制和删除页面")
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        left_layout.addWidget(desc_label)

        # 文件选择组
        file_group = QGroupBox("选择PDF文件")
        file_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        file_layout = QGridLayout(file_group)
        file_layout.setSpacing(10)
        file_layout.setContentsMargins(10, 15, 10, 10)

        self._file_label = QLabel("未选择文件")
        self._file_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self._file_label, 0, 0, Qt.AlignmentFlag.AlignLeft)

        self._select_btn = QPushButton("选择文件")
        self._select_btn.setFixedWidth(80)
        self._select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self._select_btn.clicked.connect(self._select_file)
        file_layout.addWidget(self._select_btn, 0, 1)

        file_layout.setColumnStretch(0, 1)
        left_layout.addWidget(file_group)

        # 页面列表组
        pages_group = QGroupBox("页面顺序（拖拽调整）")
        pages_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        pages_layout = QVBoxLayout(pages_group)
        pages_layout.setSpacing(10)
        pages_layout.setContentsMargins(10, 15, 10, 10)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["原始页码", "当前顺序", "操作"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setDragEnabled(True)
        self._table.setAcceptDrops(True)
        self._table.setDropIndicatorShown(True)
        self._table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._table.setMinimumHeight(200)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        pages_layout.addWidget(self._table)
        left_layout.addWidget(pages_group, 1)

        # 进度显示
        progress_group = QGroupBox("处理进度")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(6)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setMinimumHeight(20)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("就绪")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 12px; color: #666;")
        progress_layout.addWidget(self._status_label)

        left_layout.addWidget(progress_group)

        # 操作按钮
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self._new_conversion_btn = QPushButton("新转换")
        self._new_conversion_btn.setMinimumWidth(100)
        self._new_conversion_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:pressed { background-color: #E65100; }
        """)
        self._new_conversion_btn.clicked.connect(self._start_new_conversion)
        action_layout.addWidget(self._new_conversion_btn)
        self._start_btn = QPushButton("开始编排")
        self._start_btn.setMinimumWidth(100)
        self._start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self._start_btn.clicked.connect(self._start_organize)
        action_layout.addWidget(self._start_btn)




        left_layout.addLayout(action_layout)

        # 设置左侧区域比例
        main_layout.addWidget(left_widget, 2)

        # ==================== 右侧：设置面板 ====================
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        settings_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        settings_scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: transparent;")
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        output_layout = QGridLayout(output_group)
        output_layout.setSpacing(10)
        output_layout.setContentsMargins(10, 15, 10, 10)

        # 输出目录
        output_layout.addWidget(QLabel("输出目录:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setText(str(Settings.DEFAULT_OUTPUT_DIR))
        self._output_dir_edit.setReadOnly(True)
        self._output_dir_edit.setMinimumWidth(150)
        output_layout.addWidget(self._output_dir_edit, 0, 1)

        self._browse_btn = QPushButton("浏览")
        self._browse_btn.setFixedWidth(60)
        self._browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self._browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self._browse_btn, 0, 2)

        self._open_folder_btn = QPushButton("打开")
        self._open_folder_btn.setFixedWidth(60)
        self._open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        output_layout.addWidget(self._open_folder_btn, 0, 3)

        output_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(output_group)

        # 页面操作按钮组
        page_ops_group = QGroupBox("页面操作")
        page_ops_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        page_ops_layout = QVBoxLayout(page_ops_group)
        page_ops_layout.setSpacing(8)
        page_ops_layout.setContentsMargins(10, 15, 10, 10)

        self._up_btn = QPushButton("上移选中页")
        self._up_btn.setMinimumWidth(100)
        self._up_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self._up_btn.clicked.connect(self._move_up)
        page_ops_layout.addWidget(self._up_btn)

        self._down_btn = QPushButton("下移选中页")
        self._down_btn.setMinimumWidth(100)
        self._down_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self._down_btn.clicked.connect(self._move_down)
        page_ops_layout.addWidget(self._down_btn)

        self._copy_btn = QPushButton("复制选中页")
        self._copy_btn.setMinimumWidth(100)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self._copy_btn.clicked.connect(self._copy_page)
        page_ops_layout.addWidget(self._copy_btn)

        self._delete_btn = QPushButton("删除选中页")
        self._delete_btn.setMinimumWidth(100)
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        self._delete_btn.clicked.connect(self._delete_page)
        page_ops_layout.addWidget(self._delete_btn)

        settings_layout.addWidget(page_ops_group)

        # 使用说明
        tips_group = QGroupBox("使用说明")
        tips_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        tips_layout = QVBoxLayout(tips_group)
        tips_layout.setContentsMargins(10, 15, 10, 10)

        tips_label = QLabel("1. 选择一个PDF文件\n2. 通过拖拽或按钮调整页面顺序\n3. 可复制或删除页面\n4. 点击开始编排保存结果")
        tips_label.setStyleSheet("color: #666; font-size: 12px;")
        tips_label.setWordWrap(True)
        tips_layout.addWidget(tips_label)

        settings_layout.addWidget(tips_group)

        # 添加弹性空间
        settings_layout.addStretch()

        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 1)

    def _select_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)")
        if files:
            self._file = Path(files[0])
            self._file_label.setText(self._file.name)
            self._load_pages()

    def _load_pages(self):
        """加载PDF页面信息"""
        if not self._file:
            return
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(self._file))
            self._page_count = len(reader.pages)
            self._page_order = list(range(1, self._page_count + 1))
            self._refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取PDF文件: {e}")

    def _refresh_table(self):
        self._table.setUpdatesEnabled(False)
        try:
            self._table.setRowCount(len(self._page_order))
            for row, page_num in enumerate(self._page_order):
                # 原始页码
                orig_item = QTableWidgetItem(f"第 {page_num} 页")
                orig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, 0, orig_item)
                # 当前顺序
                order_item = QTableWidgetItem(f"位置 {row + 1}")
                order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, 1, order_item)
                # 操作（占位）
                op_item = QTableWidgetItem("")
                self._table.setItem(row, 2, op_item)
        finally:
            self._table.setUpdatesEnabled(True)

    def _move_up(self):
        row = self._table.currentRow()
        if row > 0:
            self._page_order[row], self._page_order[row - 1] = self._page_order[row - 1], self._page_order[row]
            self._refresh_table()
            self._table.selectRow(row - 1)

    def _move_down(self):
        row = self._table.currentRow()
        if row < len(self._page_order) - 1:
            self._page_order[row], self._page_order[row + 1] = self._page_order[row + 1], self._page_order[row]
            self._refresh_table()
            self._table.selectRow(row + 1)

    def _copy_page(self):
        row = self._table.currentRow()
        if row >= 0:
            self._page_order.insert(row + 1, self._page_order[row])
            self._refresh_table()

    def _delete_page(self):
        row = self._table.currentRow()
        if row >= 0 and len(self._page_order) > 1:
            del self._page_order[row]
            self._refresh_table()

    def _browse_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录", self._output_dir_edit.text())
        if folder:
            self._output_dir_edit.setText(folder)

    def _open_output_folder(self):
        """打开输出目录"""
        import subprocess
        import sys

        output_dir = self._output_dir_edit.text()
        if output_dir:
            path = Path(output_dir)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

            if sys.platform == 'win32':
                subprocess.run(['explorer', str(path)])
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(path)])
            else:
                subprocess.run(['xdg-open', str(path)])

            logger.info(f"打开输出目录: {output_dir}")

    def _start_organize(self):
        if not self._file:
            QMessageBox.warning(self, "提示", "请先选择PDF文件")
            return

        output_dir = Path(self._output_dir_edit.text())
        ensure_dir(output_dir)

        self._start_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在编排...")

        self._worker = ConversionWorker(self._converter, self._file, output_dir, self._page_order)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_organize_finished)
        self._worker.start()

    def _cancel_organize(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_label.setText("正在取消...")

    @Slot(object)
    def _on_progress(self, progress: ConversionProgress):
        self._progress_bar.setValue(int(progress.percentage))
        self._status_label.setText(progress.message)

    @Slot(list)
    def _on_organize_finished(self, results: List[ConversionResult]):
        self._start_btn.setEnabled(True)
        self._progress_bar.setValue(100)

        if results and results[0].success():
            self._status_label.setText("编排完成")
            QMessageBox.information(self, "编排完成", f"已保存到: {results[0].output_file}")
        else:
            self._status_label.setText("编排失败")
            error = results[0].error if results else "未知错误"
            QMessageBox.warning(self, "编排失败", error)

        self._worker = None

    def _start_new_conversion(self):
        """开始新转换 - 清空所有状态以准备新的转换任务"""
        # 检查是否有正在进行的转换
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self,
                "确认",
                "当前有正在进行的转换任务，确定要取消并开始新转换吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            self._cancel_organize()

        # 清空文件选择
        self._file = None
        self._page_count = 0
        self._page_order = []
        self._file_label.setText("未选择文件")
        self._table.setRowCount(0)

        # 重置进度条和状态
        self._progress_bar.setValue(0)
        self._status_label.setText("就绪 - 请选择PDF文件")

        # 重置按钮状态
        self._start_btn.setEnabled(True)

        logger.info("开始新转换 - 已重置所有状态")

    def is_converting(self) -> bool:
        return self._worker is not None and self._worker.isRunning()