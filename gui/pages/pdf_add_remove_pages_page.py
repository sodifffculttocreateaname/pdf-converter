# -*- coding: utf-8 -*-
"""
PDF增删页功能页面

该模块提供PDF增删页功能的完整界面，包括：
- PDF文件拖拽上传区域
- 操作模式选择（删除/插入）
- 页码列表设置
- 进度显示和取消功能
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QVBoxLayout,
    QWidget,
    QButtonGroup,
    QFrame
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.pdf_add_remove_pages import PdfAddRemovePagesConverter
from core.base_converter import ConversionProgress, ConversionResult
from utils.file_utils import get_file_size, ensure_dir
from utils.logger import get_logger


logger = get_logger(__name__)


class FileItem:
    """文件项数据类"""

    def __init__(self, file_path: Path):
        self.file_path: Path = file_path
        self.status: ConversionStatus = ConversionStatus.PENDING
        self.message: str = ""

    @property
    def name(self) -> str:
        return self.file_path.name

    @property
    def size(self) -> int:
        return get_file_size(self.file_path)

    @property
    def size_formatted(self) -> str:
        return format_file_size(self.size)

    @property
    def status_text(self) -> str:
        status_map = {
            ConversionStatus.PENDING: "待处理",
            ConversionStatus.PROCESSING: "处理中",
            ConversionStatus.COMPLETED: "已完成",
            ConversionStatus.FAILED: "失败",
            ConversionStatus.CANCELLED: "已取消"
        }
        return status_map.get(self.status, "未知")


class ConversionWorker(QThread):
    """转换工作线程"""

    progress = Signal(object)
    finished = Signal(list)

    def __init__(
        self,
        converter: PdfAddRemovePagesConverter,
        files: List[Path],
        output_dir: Path,
        operation: str = "delete",
        pages: str = "",
        parent=None
    ):
        super().__init__(parent)
        self._converter = converter
        self._files = files
        self._output_dir = output_dir
        self._operation = operation
        self._pages = pages
        self._cancelled = False

    def run(self):
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)

        self._converter.set_progress_callback(on_progress)
        results = self._converter.convert(
            self._files,
            self._output_dir,
            operation=self._operation,
            pages=self._pages
        )
        self.finished.emit(results)

    def cancel(self):
        self._cancelled = True
        self._converter.cancel()


class PdfDropArea(QWidget):
    """PDF文件拖拽上传区域"""

    files_dropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self._label = QLabel(
            "拖拽PDF文件到此处\n"
            "或点击选择文件"
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self._set_normal_style()

    def _set_normal_style(self):
        self.setStyleSheet("""
            PdfDropArea {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
            PdfDropArea:hover {
                background-color: #e3f2fd;
                border-color: #2196F3;
            }
            QLabel { color: #666; font-size: 13px; }
        """)

    def _set_drag_style(self):
        self.setStyleSheet("""
            PdfDropArea {
                background-color: #e3f2fd;
                border: 2px dashed #2196F3;
                border-radius: 8px;
            }
            QLabel { color: #2196F3; font-size: 14px; font-weight: bold; }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_normal_style()

    def dropEvent(self, event: QDropEvent):
        self._set_normal_style()
        files: List[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() == '.pdf':
                files.append(path)
            elif path.is_dir():
                for item in path.iterdir():
                    if item.is_file() and item.suffix.lower() == '.pdf':
                        files.append(item)
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)"
            )
            if files:
                self.files_dropped.emit([Path(f) for f in files])


class PdfAddRemovePagesPage(QWidget):
    """PDF增删页功能页面"""

    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._files: List[FileItem] = []
        self._converter = PdfAddRemovePagesConverter()
        self._worker: Optional[ConversionWorker] = None
        self._init_ui()
        logger.info("PDF增删页页面初始化完成")

    def _init_ui(self):
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
        self._title_label = QLabel("PDF增删页")
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_layout.addWidget(self._title_label)

        # 功能说明
        desc_label = QLabel("在PDF中删除指定页面或插入空白页")
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        left_layout.addWidget(desc_label)

        # 文件管理区 - 上传区域和文件列表左右对半分
        file_manage_widget = QWidget()
        file_manage_widget.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        file_manage_layout = QHBoxLayout(file_manage_widget)
        file_manage_layout.setContentsMargins(0, 0, 0, 0)
        file_manage_layout.setSpacing(0)

        # 左侧：拖拽上传区域
        self._drop_area = PdfDropArea()
        self._drop_area.files_dropped.connect(self._on_files_dropped)
        file_manage_layout.addWidget(self._drop_area, 1)

        # 分隔线
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setStyleSheet("background-color: #e0e0e0;")
        file_manage_layout.addWidget(separator)

        # 右侧：文件列表区域
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(8, 8, 8, 8)
        list_layout.setSpacing(6)

        # 文件计数标签
        self._count_label = QLabel("待处理文件 (0)")
        self._count_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #555;")
        list_layout.addWidget(self._count_label)

        # 文件列表表格
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["文件名", "大小", "状态"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        list_layout.addWidget(self._table, 1)

        # 文件操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self._add_btn = QPushButton("添加")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self._add_btn.clicked.connect(self._on_add_files)
        btn_layout.addWidget(self._add_btn)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setFixedHeight(26)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #757575; }
        """)
        self._clear_btn.clicked.connect(self._clear_files)
        btn_layout.addWidget(self._clear_btn)

        list_layout.addLayout(btn_layout)
        file_manage_layout.addWidget(list_widget, 1)

        left_layout.addWidget(file_manage_widget, 1)

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
                background-color: #FF9800;
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
        self._start_btn = QPushButton("开始处理")
        self._start_btn.setMinimumWidth(100)
        self._start_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self._start_btn.clicked.connect(self._start_operation)
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

        # 操作设置组
        operation_group = QGroupBox("操作设置")
        operation_group.setStyleSheet("""
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
        operation_layout = QVBoxLayout(operation_group)
        operation_layout.setSpacing(8)
        operation_layout.setContentsMargins(10, 15, 10, 10)

        # 操作模式
        mode_label = QLabel("操作模式:")
        mode_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        operation_layout.addWidget(mode_label)

        self._mode_group = QButtonGroup(self)
        self._delete_radio = QRadioButton("删除页面 - 删除指定的页码")
        self._delete_radio.setChecked(True)
        self._mode_group.addButton(self._delete_radio, 0)
        operation_layout.addWidget(self._delete_radio)

        self._insert_radio = QRadioButton("插入空白页 - 在指定位置插入空白页")
        self._mode_group.addButton(self._insert_radio, 1)
        operation_layout.addWidget(self._insert_radio)

        # 页码输入
        pages_label = QLabel("页码列表:")
        pages_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 8px;")
        operation_layout.addWidget(pages_label)

        self._pages_edit = QLineEdit()
        self._pages_edit.setPlaceholderText("例如: 1,3,5-10,15")
        self._pages_edit.setMinimumWidth(150)
        self._pages_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #FF9800;
            }
        """)
        operation_layout.addWidget(self._pages_edit)

        # 提示标签
        hint_label = QLabel("提示: 页码格式支持单个页码(5)、范围(1-3)、多个(1,3,5-10)，用逗号分隔")
        hint_label.setStyleSheet("color: #888; font-size: 11px;")
        hint_label.setWordWrap(True)
        operation_layout.addWidget(hint_label)

        settings_layout.addWidget(operation_group)

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

        # 添加弹性空间
        settings_layout.addStretch()

        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 1)

    def _on_files_dropped(self, files: List[Path]):
        self._add_files(files)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)")
        if files:
            self._add_files([Path(f) for f in files])

    def _show_context_menu(self, pos):
        item = self._table.itemAt(pos)
        if not item:
            return
        row = item.row()
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        remove_action = menu.addAction("移除")
        remove_action.triggered.connect(lambda: self._remove_file(row))
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _remove_file(self, row: int):
        if 0 <= row < len(self._files):
            del self._files[row]
            self._refresh_table()

    def _clear_files(self):
        self._files.clear()
        self._refresh_table()

    def _add_files(self, files: List[Path]):
        for file_path in files:
            if not file_path.is_file() or file_path.suffix.lower() != '.pdf':
                continue
            if any(f.file_path == file_path for f in self._files):
                continue
            self._files.append(FileItem(file_path))
        self._refresh_table()

    def _refresh_table(self):
        self._table.setUpdatesEnabled(False)
        try:
            self._table.setRowCount(len(self._files))
            for row, file_item in enumerate(self._files):
                name_item = QTableWidgetItem(file_item.name)
                name_item.setToolTip(str(file_item.file_path))
                self._table.setItem(row, 0, name_item)
                size_item = QTableWidgetItem(file_item.size_formatted)
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, 1, size_item)
                status_item = QTableWidgetItem(file_item.status_text)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if file_item.status == ConversionStatus.COMPLETED:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif file_item.status == ConversionStatus.FAILED:
                    status_item.setForeground(Qt.GlobalColor.red)
                self._table.setItem(row, 2, status_item)
        finally:
            self._table.setUpdatesEnabled(True)
        self._count_label.setText(f"待处理文件 ({len(self._files)})")

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

    def _start_operation(self):
        if not self._files:
            QMessageBox.warning(self, "提示", "请先添加PDF文件")
            return

        pages = self._pages_edit.text().strip()
        if not pages:
            QMessageBox.warning(self, "提示", "请输入页码列表")
            return

        output_dir = Path(self._output_dir_edit.text())
        ensure_dir(output_dir)

        operation = "delete" if self._delete_radio.isChecked() else "insert"

        for file_item in self._files:
            file_item.status = ConversionStatus.PENDING
        self._refresh_table()

        self._start_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在处理...")

        files = [f.file_path for f in self._files]
        self._worker = ConversionWorker(self._converter, files, output_dir, operation, pages)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_operation_finished)
        self._worker.start()

    def _cancel_operation(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_label.setText("正在取消...")

    @Slot(object)
    def _on_progress(self, progress: ConversionProgress):
        self._progress_bar.setValue(int(progress.percentage))
        self._status_label.setText(progress.message)

    @Slot(list)
    def _on_operation_finished(self, results: List[ConversionResult]):
        success_count = sum(1 for r in results if r.success())
        fail_count = len(results) - success_count

        for result in results:
            for file_item in self._files:
                if file_item.file_path == result.input_file:
                    file_item.status = result.status
                    file_item.message = result.message or result.error or ""
                    break
        self._refresh_table()

        self._start_btn.setEnabled(True)
        self._progress_bar.setValue(100)

        message = f"处理完成: 成功 {success_count} 个"
        if fail_count > 0:
            message += f"，失败 {fail_count} 个"
        self._status_label.setText(message)

        if fail_count > 0:
            QMessageBox.warning(self, "处理完成", message)
        else:
            QMessageBox.information(self, "处理完成", message)

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
            self._cancel_operation()

        # 清空文件列表
        self._files.clear()
        self._refresh_table()

        # 重置进度条和状态
        self._progress_bar.setValue(0)
        self._status_label.setText("就绪 - 请添加文件开始转换")

        # 重置按钮状态
        self._start_btn.setEnabled(True)

        logger.info("开始新转换 - 已重置所有状态")

    def is_converting(self) -> bool:
        return self._worker is not None and self._worker.isRunning()