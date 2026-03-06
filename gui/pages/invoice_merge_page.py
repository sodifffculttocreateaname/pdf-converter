# -*- coding: utf-8 -*-
"""
发票合并功能页面
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QVBoxLayout, QWidget, QFrame
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.invoice_merge import InvoiceMergeConverter
from core.base_converter import ConversionProgress, ConversionResult
from utils.file_utils import get_file_size, ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class FileItem:
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
            ConversionStatus.PENDING: "待处理", ConversionStatus.PROCESSING: "处理中",
            ConversionStatus.COMPLETED: "已完成", ConversionStatus.FAILED: "失败",
            ConversionStatus.CANCELLED: "已取消"
        }
        return status_map.get(self.status, "未知")


class ConversionWorker(QThread):
    progress = Signal(object)
    finished = Signal(list)

    def __init__(self, converter: InvoiceMergeConverter, files: List[Path],
                 output_dir: Path, output_filename: str, parent=None):
        super().__init__(parent)
        self._converter = converter
        self._files = files
        self._output_dir = output_dir
        self._output_filename = output_filename
        self._cancelled = False

    def run(self):
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)
        self._converter.set_progress_callback(on_progress)
        self._converter.set_output_filename(self._output_filename)
        results = self._converter.convert(self._files, self._output_dir)
        self.finished.emit(results)

    def cancel(self):
        self._cancelled = True
        self._converter.cancel()


class InvoiceDropArea(QWidget):
    files_dropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self._label = QLabel("拖拽发票PDF文件到此处上传\n支持 PDF 格式\n或点击选择文件")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._label)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setStyleSheet("InvoiceDropArea { background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 8px; } InvoiceDropArea:hover { background-color: #fff3e0; border-color: #FF9800; } QLabel { color: #666; }")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("InvoiceDropArea { background-color: #fff3e0; border: 2px dashed #FF9800; border-radius: 8px; } QLabel { color: #FF9800; font-weight: bold; }")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("InvoiceDropArea { background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 8px; } InvoiceDropArea:hover { background-color: #fff3e0; border-color: #FF9800; } QLabel { color: #666; }")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("InvoiceDropArea { background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 8px; } InvoiceDropArea:hover { background-color: #fff3e0; border-color: #FF9800; } QLabel { color: #666; }")
        files: List[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() == '.pdf':
                files.append(path)
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(self, "选择发票PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)")
            if files:
                self.files_dropped.emit([Path(f) for f in files])


class InvoiceMergePage(QWidget):
    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._files: List[FileItem] = []
        self._converter = InvoiceMergeConverter()
        self._worker: Optional[ConversionWorker] = None
        self._init_ui()
        logger.info("发票合并页面初始化完成")

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ==================== 左侧：文件管理区域 ====================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 标题
        self._title_label = QLabel("发票合并")
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_layout.addWidget(self._title_label)

        # 说明
        desc_label = QLabel("合并多张发票PDF文件为一个PDF，按添加顺序排列")
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        left_layout.addWidget(desc_label)

        # 文件管理区
        file_manage_widget = QWidget()
        file_manage_widget.setStyleSheet("background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px;")
        file_manage_layout = QHBoxLayout(file_manage_widget)
        file_manage_layout.setContentsMargins(10, 10, 10, 10)
        file_manage_layout.setSpacing(10)

        # 拖拽区域
        self._drop_area = InvoiceDropArea()
        self._drop_area.files_dropped.connect(self._on_files_dropped)
        file_manage_layout.addWidget(self._drop_area, 1)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        file_manage_layout.addWidget(separator)

        # 文件列表区域
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(8)

        self._count_label = QLabel("待合并文件 (0)")
        self._count_label.setStyleSheet("font-size: 12px; color: #666;")
        list_layout.addWidget(self._count_label)

        self._file_list = QWidget()
        self._file_list_layout = QVBoxLayout(self._file_list)
        self._file_list_layout.setContentsMargins(0, 0, 0, 0)
        self._file_list_layout.setSpacing(5)
        self._file_list_layout.addStretch()
        list_layout.addWidget(self._file_list, 1)

        # 排序按钮
        sort_btn_layout = QHBoxLayout()
        sort_btn_layout.setSpacing(5)
        self._up_btn = QPushButton("↑ 上移")
        self._up_btn.setFixedHeight(26)
        self._up_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 12px; } QPushButton:hover { background-color: #1976D2; }")
        self._up_btn.clicked.connect(self._move_up)
        sort_btn_layout.addWidget(self._up_btn)
        self._down_btn = QPushButton("↓ 下移")
        self._down_btn.setFixedHeight(26)
        self._down_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 12px; } QPushButton:hover { background-color: #1976D2; }")
        self._down_btn.clicked.connect(self._move_down)
        sort_btn_layout.addWidget(self._down_btn)
        sort_btn_layout.addStretch()
        list_layout.addLayout(sort_btn_layout)

        # 操作按钮
        file_btn_layout = QHBoxLayout()
        file_btn_layout.setSpacing(5)
        self._add_btn = QPushButton("添加")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 12px; } QPushButton:hover { background-color: #388E3C; }")
        self._add_btn.clicked.connect(self._on_add_files)
        file_btn_layout.addWidget(self._add_btn)
        self._clear_btn = QPushButton("清空")
        self._clear_btn.setFixedHeight(26)
        self._clear_btn.setStyleSheet("QPushButton { background-color: #9E9E9E; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 12px; } QPushButton:hover { background-color: #757575; }")
        self._clear_btn.clicked.connect(self._clear_files)
        file_btn_layout.addWidget(self._clear_btn)
        file_btn_layout.addStretch()
        list_layout.addLayout(file_btn_layout)

        file_manage_layout.addWidget(list_widget, 1)
        left_layout.addWidget(file_manage_widget, 1)

        # 进度显示组
        progress_group = QGroupBox("合并进度")
        progress_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(5)
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setMinimumHeight(20)
        self._progress_bar.setStyleSheet("QProgressBar { border: 1px solid #e0e0e0; border-radius: 4px; text-align: center; background-color: #f5f5f5; } QProgressBar::chunk { background-color: #FF9800; border-radius: 3px; }")
        progress_layout.addWidget(self._progress_bar)
        self._status_label = QLabel("就绪")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
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

        self._start_btn = QPushButton("开始合并")
        self._start_btn.setFixedWidth(100)
        self._start_btn.setFixedHeight(32)
        self._start_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 4px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #F57C00; } QPushButton:disabled { background-color: #ccc; color: #666; }")
        self._start_btn.clicked.connect(self._start_merge)
        action_layout.addWidget(self._start_btn)

        left_layout.addLayout(action_layout)

        main_layout.addWidget(left_widget, 2)

        # ==================== 右侧：设置面板 ====================
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll.setStyleSheet("QScrollArea { background-color: transparent; }")

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        output_layout = QGridLayout(output_group)
        output_layout.setSpacing(10)
        output_layout.setVerticalSpacing(8)

        output_layout.addWidget(QLabel("输出目录:"), 0, 0)
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setText(str(Settings.DEFAULT_OUTPUT_DIR))
        self._output_dir_edit.setReadOnly(True)
        output_layout.addWidget(self._output_dir_edit, 0, 1)
        self._browse_btn = QPushButton("浏览")
        self._browse_btn.setFixedWidth(50)
        self._browse_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; padding: 5px 8px; font-size: 12px; } QPushButton:hover { background-color: #1976D2; }")
        self._browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self._browse_btn, 0, 2)
        self._open_folder_btn = QPushButton("打开")
        self._open_folder_btn.setFixedWidth(50)
        self._open_folder_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 4px; padding: 5px 8px; font-size: 12px; } QPushButton:hover { background-color: #F57C00; }")
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        output_layout.addWidget(self._open_folder_btn, 0, 3)

        output_layout.addWidget(QLabel("输出文件名:"), 1, 0)
        self._filename_edit = QLineEdit()
        self._filename_edit.setText("merged_invoices.pdf")
        self._filename_edit.setPlaceholderText("输入输出文件名")
        output_layout.addWidget(self._filename_edit, 1, 1, 1, 2)

        output_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(output_group)

        # 使用说明组
        hint_group = QGroupBox("使用说明")
        hint_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        hint_layout = QVBoxLayout(hint_group)
        hint_text = QLabel("1. 拖拽或点击添加发票PDF文件\n2. 使用上移/下移调整合并顺序\n3. 设置输出文件名\n4. 点击开始合并")
        hint_text.setStyleSheet("color: #666; font-size: 12px; line-height: 1.5;")
        hint_layout.addWidget(hint_text)
        settings_layout.addWidget(hint_group)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)

        main_layout.addWidget(settings_scroll, 1)

    def _on_files_dropped(self, files: List[Path]):
        self._add_files(files)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择发票PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)")
        if files:
            self._add_files([Path(f) for f in files])

    def _move_up(self):
        if self._selected_index() > 0:
            idx = self._selected_index()
            self._files[idx], self._files[idx - 1] = self._files[idx - 1], self._files[idx]
            self._refresh_file_list()
            self._select_file(idx - 1)

    def _move_down(self):
        if 0 <= self._selected_index() < len(self._files) - 1:
            idx = self._selected_index()
            self._files[idx], self._files[idx + 1] = self._files[idx + 1], self._files[idx]
            self._refresh_file_list()
            self._select_file(idx + 1)

    def _selected_index(self) -> int:
        return getattr(self, '_selected_file_index', -1)

    def _select_file(self, index: int):
        self._selected_file_index = index

    def _remove_file(self, file_item: FileItem):
        if file_item in self._files:
            self._files.remove(file_item)
            self._refresh_file_list()

    def _clear_files(self):
        self._files.clear()
        self._refresh_file_list()

    def _add_files(self, files: List[Path]):
        for file_path in files:
            if not file_path.is_file() or file_path.suffix.lower() != '.pdf':
                continue
            if any(f.file_path == file_path for f in self._files):
                continue
            self._files.append(FileItem(file_path))
        self._refresh_file_list()

    def _refresh_file_list(self):
        # 清空现有列表
        while self._file_list_layout.count() > 1:
            item = self._file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加文件项
        for idx, file_item in enumerate(self._files):
            item_widget = self._create_file_item_widget(file_item, idx)
            self._file_list_layout.insertWidget(self._file_list_layout.count() - 1, item_widget)

        self._count_label.setText(f"待合并文件 ({len(self._files)})")

    def _create_file_item_widget(self, file_item: FileItem, index: int) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: white; border: 1px solid #e0e0e0; border-radius: 4px; padding: 5px; } QWidget:hover { background-color: #f5f5f5; }")
        widget.mousePressEvent = lambda e: self._select_file(index)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 序号标签
        num_label = QLabel(f"{index + 1}")
        num_label.setStyleSheet("background-color: #FF9800; color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px; font-weight: bold;")
        num_label.setFixedWidth(20)
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(num_label)

        # PDF标签
        pdf_label = QLabel("PDF")
        pdf_label.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px; font-weight: bold;")
        layout.addWidget(pdf_label)

        # 文件名
        name_label = QLabel(file_item.name)
        name_label.setStyleSheet("font-size: 12px; color: #333;")
        layout.addWidget(name_label, 1)

        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet("QPushButton { background-color: transparent; color: #999; border: none; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #ffebee; color: #f44336; }")
        delete_btn.clicked.connect(lambda: self._remove_file(file_item))
        layout.addWidget(delete_btn)

        return widget

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

    def _start_merge(self):
        if len(self._files) < 2:
            QMessageBox.warning(self, "提示", "请至少添加2个发票文件进行合并")
            return

        filename = self._filename_edit.text().strip()
        if not filename:
            QMessageBox.warning(self, "提示", "请输入输出文件名")
            return

        if not filename.endswith('.pdf'):
            filename += '.pdf'

        output_dir = Path(self._output_dir_edit.text())
        ensure_dir(output_dir)

        self._start_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在合并...")

        files = [f.file_path for f in self._files]

        self._worker = ConversionWorker(self._converter, files, output_dir, filename)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_merge_finished)
        self._worker.start()

    def _cancel_merge(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_label.setText("正在取消...")

    @Slot(object)
    def _on_progress(self, progress: ConversionProgress):
        self._progress_bar.setValue(int(progress.percentage))
        self._status_label.setText(progress.message)

    @Slot(list)
    def _on_merge_finished(self, results: List[ConversionResult]):
        if results and results[0].success():
            self._status_label.setText("合并完成")
            QMessageBox.information(self, "合并完成", f"已保存到: {results[0].output_file}")
        else:
            error = results[0].error if results else "未知错误"
            self._status_label.setText("合并失败")
            QMessageBox.warning(self, "合并失败", error)

        self._start_btn.setEnabled(True)
        self._progress_bar.setValue(100)
        self._worker = None

    def is_converting(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

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
            self._cancel_merge()

        # 清空文件列表
        self._files.clear()
        self._refresh_file_list()

        # 重置进度条和状态
        self._progress_bar.setValue(0)
        self._status_label.setText("就绪 - 请添加文件开始转换")

        # 重置按钮状态
        self._start_btn.setEnabled(True)

        logger.info("开始新转换 - 已重置所有状态")