# -*- coding: utf-8 -*-
"""
PDF页面合并功能页面

该模块提供PDF页面合并功能的完整界面，包括：
- PDF文件拖拽上传区域
- 文件列表管理
- 布局选择（2合1、4合1、6合1）
- 页面间距和边框设置
- 进度显示和取消功能

使用方式：
    from gui.pages import PdfPageMergePage

    # 创建页面
    page = PdfPageMergePage()

    # 添加到布局或堆栈窗口
    stack.addWidget(page)
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QSpinBox,
    QVBoxLayout, QWidget, QCheckBox, QScrollArea, QGridLayout
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.pdf_page_merge import PdfPageMergeConverter
from core.base_converter import ConversionProgress, ConversionResult
from utils.file_utils import get_file_size, ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class FileItem:
    """
    文件项数据类

    存储单个文件的元数据和状态信息。

    Attributes:
        file_path: 文件路径
        status: 转换状态
        message: 状态消息
    """

    def __init__(self, file_path: Path):
        """
        初始化文件项

        Args:
            file_path: 文件路径
        """
        self.file_path: Path = file_path
        self.status: ConversionStatus = ConversionStatus.PENDING
        self.message: str = ""

    @property
    def name(self) -> str:
        """文件名（含扩展名，不含路径）"""
        return self.file_path.name

    @property
    def size(self) -> int:
        """文件大小（字节）"""
        return get_file_size(self.file_path)

    @property
    def size_formatted(self) -> str:
        """格式化的文件大小字符串"""
        return format_file_size(self.size)

    @property
    def status_text(self) -> str:
        """状态文本（中文）"""
        status_map = {
            ConversionStatus.PENDING: "待处理",
            ConversionStatus.PROCESSING: "处理中",
            ConversionStatus.COMPLETED: "已完成",
            ConversionStatus.FAILED: "失败",
            ConversionStatus.CANCELLED: "已取消"
        }
        return status_map.get(self.status, "未知")


class ConversionWorker(QThread):
    """
    转换工作线程

    在后台执行PDF页面合并任务，避免阻塞UI。

    Signals:
        progress: 进度信号，参数为ConversionProgress对象
        finished: 完成信号，参数为结果列表
    """

    progress = Signal(object)  # ConversionProgress
    finished = Signal(list)    # List[ConversionResult]

    def __init__(self, converter: PdfPageMergeConverter, files: List[Path],
                 output_dir: Path, layout: int, spacing: int, show_border: bool, parent=None):
        """
        初始化工作线程

        Args:
            converter: PDF页面合并转换器实例
            files: 要处理的文件列表
            output_dir: 输出目录
            layout: 布局模式（2/4/6）
            spacing: 页面间距
            show_border: 是否显示边框
            parent: 父对象
        """
        super().__init__(parent)
        self._converter = converter
        self._files = files
        self._output_dir = output_dir
        self._layout = layout
        self._spacing = spacing
        self._show_border = show_border
        self._cancelled = False

    def run(self):
        """执行合并任务"""
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)
        self._converter.set_progress_callback(on_progress)
        results = self._converter.convert(
            self._files, self._output_dir,
            layout=self._layout, spacing=self._spacing, show_border=self._show_border
        )
        self.finished.emit(results)

    def cancel(self):
        """取消合并"""
        self._cancelled = True
        self._converter.cancel()


class PdfDropArea(QWidget):
    """
    PDF拖拽上传区域

    专门用于PDF文件的拖拽上传组件（紧凑版本，用于左右分栏布局）。

    Signals:
        files_dropped(list): 文件拖放信号，参数为Path列表
    """

    files_dropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化拖拽区域

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 提示标签
        self._label = QLabel(
            "拖拽PDF文件到此处\n"
            "或点击选择文件"
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        # 启用拖拽
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 设置最小高度和样式
        self.setMinimumHeight(80)
        self._set_normal_style()

    def _set_normal_style(self):
        """设置正常样式"""
        self.setStyleSheet("""
            PdfDropArea {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
            PdfDropArea:hover {
                background-color: #fff3e0;
                border-color: #FF9800;
            }
            QLabel {
                color: #666;
                font-size: 13px;
            }
        """)

    def _set_drag_style(self):
        """设置拖拽悬停样式"""
        self.setStyleSheet("""
            PdfDropArea {
                background-color: #fff3e0;
                border: 2px dashed #FF9800;
                border-radius: 8px;
            }
            QLabel {
                color: #FF9800;
                font-size: 14px;
                font-weight: bold;
            }
        """)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self._set_normal_style()

    def dropEvent(self, event):
        """拖拽放下事件"""
        self._set_normal_style()

        files: List[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() == '.pdf':
                files.append(path)

        if files:
            self.files_dropped.emit(files)

        event.acceptProposedAction()

    def mousePressEvent(self, event):
        """鼠标点击事件 - 打开文件选择对话框"""
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)"
            )
            if files:
                self.files_dropped.emit([Path(f) for f in files])


class PdfPageMergePage(QWidget):
    """
    PDF页面合并功能页面

    提供完整的PDF页面合并功能界面，包括：
    - PDF文件拖拽/选择上传
    - 文件列表管理
    - 布局选择（2合1、4合1、6合1）
    - 页面间距和边框设置
    - 合并进度显示
    - 开始/取消按钮

    Signals:
        back_requested: 请求返回主页面信号
    """

    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化PDF页面合并页面

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 文件列表
        self._files: List[FileItem] = []

        # 转换器
        self._converter = PdfPageMergeConverter()

        # 工作线程
        self._worker: Optional[ConversionWorker] = None

        # 初始化UI
        self._init_ui()

        logger.info("PDF页面合并页面初始化完成")

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
        self._title_label = QLabel("PDF页面合并")
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_layout.addWidget(self._title_label)

        # 功能说明
        desc_label = QLabel("将PDF多页合并为单页（如2合1、4合1打印布局）")
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

        # 文件列表
        self._file_list = QWidget()
        self._file_list_layout = QVBoxLayout(self._file_list)
        self._file_list_layout.setContentsMargins(0, 0, 0, 0)
        self._file_list_layout.setSpacing(4)
        self._file_list_layout.addStretch()
        list_layout.addWidget(self._file_list, 1)

        # 文件操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self._add_btn = QPushButton("添加")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #F57C00; }
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
        progress_group = QGroupBox("合并进度")
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
        self._start_btn = QPushButton("开始合并")
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
        self._start_btn.clicked.connect(self._start_merge)
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

        # 合并设置组
        merge_group = QGroupBox("合并设置")
        merge_group.setStyleSheet("""
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
        merge_layout = QGridLayout(merge_group)
        merge_layout.setSpacing(10)
        merge_layout.setContentsMargins(10, 15, 10, 10)

        # 布局选择
        merge_layout.addWidget(QLabel("布局:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        self._layout_combo = QComboBox()
        self._layout_combo.addItems(["2合1", "4合1", "6合1"])
        self._layout_combo.setCurrentIndex(1)  # 默认4合1
        self._layout_combo.setMinimumWidth(100)
        merge_layout.addWidget(self._layout_combo, 0, 1, Qt.AlignmentFlag.AlignLeft)

        # 页面间距
        merge_layout.addWidget(QLabel("页面间距:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        spacing_widget = QWidget()
        spacing_hlayout = QHBoxLayout(spacing_widget)
        spacing_hlayout.setContentsMargins(0, 0, 0, 0)
        spacing_hlayout.setSpacing(5)
        self._spacing_spin = QSpinBox()
        self._spacing_spin.setRange(0, 100)
        self._spacing_spin.setValue(5)
        self._spacing_spin.setSuffix(" px")
        self._spacing_spin.setMinimumWidth(80)
        spacing_hlayout.addWidget(self._spacing_spin)
        spacing_hlayout.addStretch()
        merge_layout.addWidget(spacing_widget, 1, 1)

        merge_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(merge_group)

        # 边框设置组
        border_group = QGroupBox("边框设置")
        border_group.setStyleSheet("""
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
        border_layout = QVBoxLayout(border_group)
        border_layout.setSpacing(8)
        border_layout.setContentsMargins(10, 15, 10, 10)

        self._border_check = QCheckBox("显示边框")
        border_layout.addWidget(self._border_check)

        settings_layout.addWidget(border_group)

        # 添加弹性空间
        settings_layout.addStretch()

        settings_scroll.setWidget(settings_widget)
        main_layout.addWidget(settings_scroll, 1)

    # ==================== 事件处理 ====================
    def _on_files_dropped(self, files: List[Path]):
        """
        文件拖放处理

        Args:
            files: 拖放的文件路径列表
        """
        self._add_files(files)

    def _on_add_files(self):
        """添加文件按钮点击处理"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if files:
            self._add_files([Path(f) for f in files])

    def _browse_output_dir(self):
        """浏览输出目录"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self._output_dir_edit.text()
        )
        if folder:
            self._output_dir_edit.setText(folder)
            logger.info(f"输出目录已更改: {folder}")

    def _open_output_folder(self):
        """打开输出目录"""
        import subprocess
        import sys

        output_dir = self._output_dir_edit.text()
        if output_dir:
            path = Path(output_dir)
            # 如果目录不存在，先创建
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

            # 根据系统选择打开方式
            if sys.platform == 'win32':
                subprocess.run(['explorer', str(path)])
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(path)])
            else:
                subprocess.run(['xdg-open', str(path)])

            logger.info(f"打开输出目录: {output_dir}")

    # ==================== 文件管理 ====================
    def _add_files(self, files: List[Path]):
        """
        添加文件到列表

        Args:
            files: 文件路径列表
        """
        added_count = 0

        for file_path in files:
            if not file_path.is_file():
                continue

            # 检查格式
            if file_path.suffix.lower() != '.pdf':
                logger.debug(f"忽略非PDF文件: {file_path.name}")
                continue

            # 检查重复
            if any(f.file_path == file_path for f in self._files):
                logger.debug(f"文件已存在，跳过: {file_path.name}")
                continue

            self._files.append(FileItem(file_path))
            added_count += 1

        self._refresh_file_list()
        logger.info(f"添加文件: {added_count} 个，总计: {len(self._files)} 个")

    def _clear_files(self):
        """清空文件列表"""
        count = len(self._files)
        self._files.clear()
        self._refresh_file_list()
        logger.info(f"清空文件列表: 移除 {count} 个文件")

    def _remove_file(self, row: int):
        """移除指定行的文件"""
        if 0 <= row < len(self._files):
            removed_file = self._files[row]
            del self._files[row]
            self._refresh_file_list()
            logger.debug(f"移除文件: {removed_file.name}")

    def _refresh_file_list(self):
        """刷新文件列表显示"""
        # 清空现有列表
        while self._file_list_layout.count() > 1:
            item = self._file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加文件项
        for i, file_item in enumerate(self._files):
            item_widget = self._create_file_item_widget(file_item, i)
            self._file_list_layout.insertWidget(i, item_widget)

        # 更新计数
        self._count_label.setText(f"待处理文件 ({len(self._files)})")

    def _create_file_item_widget(self, file_item: FileItem, index: int) -> QWidget:
        """
        创建文件项控件

        Args:
            file_item: 文件项数据
            index: 文件索引

        Returns:
            文件项控件
        """
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #f5f5f5;
                border-color: #bdbdbd;
            }
        """)
        widget.setFixedHeight(32)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 文件图标
        ext_label = QLabel("PDF")
        ext_label.setStyleSheet("""
            QLabel {
                background-color: #fff3e0;
                color: #FF9800;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        ext_label.setFixedWidth(36)
        ext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ext_label)

        # 文件名（支持省略）
        name_label = QLabel()
        name_label.setStyleSheet("font-size: 12px; color: #333;")
        name_label.setToolTip(str(file_item.file_path))
        layout.addWidget(name_label, 1)

        # 文件大小
        size_label = QLabel(file_item.size_formatted)
        size_label.setStyleSheet("font-size: 11px; color: #999;")
        layout.addWidget(size_label)

        # 删除按钮
        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #999;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffebee;
                color: #f44336;
                border-radius: 10px;
            }
        """)
        remove_btn.clicked.connect(lambda: self._remove_file(index))
        layout.addWidget(remove_btn)

        # 延迟设置文件名，以便正确获取控件宽度
        def update_elided_text():
            try:
                available_width = name_label.width()
                if available_width > 20:
                    font_metrics = QFontMetrics(name_label.font())
                    elided_text = font_metrics.elidedText(
                        file_item.name,
                        Qt.TextElideMode.ElideMiddle,
                        available_width
                    )
                    name_label.setText(elided_text)
                else:
                    name_label.setText(file_item.name)
            except Exception:
                name_label.setText(file_item.name)

        # 使用单次定时器确保布局完成后更新
        QTimer.singleShot(10, update_elided_text)

        return widget

    # ==================== 合并操作 ====================
    def _start_merge(self):
        """开始合并"""
        # 检查文件列表
        if not self._files:
            QMessageBox.warning(self, "提示", "请先添加要合并的PDF文件")
            return

        # 获取设置
        output_dir = Path(self._output_dir_edit.text())
        layout_map = {0: 2, 1: 4, 2: 6}
        layout = layout_map[self._layout_combo.currentIndex()]
        spacing = self._spacing_spin.value()
        show_border = self._border_check.isChecked()

        # 确保输出目录存在
        ensure_dir(output_dir)

        # 重置文件状态
        for file_item in self._files:
            file_item.status = ConversionStatus.PENDING
            file_item.message = ""
        self._refresh_file_list()

        # 更新UI状态
        self._start_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在合并...")

        # 创建工作线程
        files = [f.file_path for f in self._files]
        self._worker = ConversionWorker(
            self._converter, files, output_dir,
            layout, spacing, show_border
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_merge_finished)

        # 启动合并
        self._worker.start()
        logger.info(f"开始PDF页面合并: {len(files)} 个文件")

    def _cancel_merge(self):
        """取消合并"""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_label.setText("正在取消...")

    @Slot(object)
    def _on_progress(self, progress: ConversionProgress):
        """进度更新处理"""
        percentage = progress.percentage
        self._progress_bar.setValue(int(percentage))
        self._status_label.setText(progress.message)

        # 更新文件状态
        if progress.current_file:
            for file_item in self._files:
                if file_item.name == progress.current_file:
                    file_item.status = ConversionStatus.PROCESSING
                    break
            self._refresh_file_list()

    @Slot(list)
    def _on_merge_finished(self, results: List[ConversionResult]):
        """合并完成处理"""
        # 更新文件状态
        for result in results:
            for file_item in self._files:
                if file_item.file_path == result.input_file:
                    file_item.status = result.status
                    file_item.message = result.message or result.error or ""
                    break

        self._refresh_file_list()

        # 统计结果
        success_count = sum(1 for r in results if r.success())
        fail_count = len(results) - success_count

        # 更新UI状态
        self._start_btn.setEnabled(True)
        self._progress_bar.setValue(100)

        message = f"合并完成: 成功 {success_count} 个"
        if fail_count > 0:
            message += f", 失败 {fail_count} 个"
            self._status_label.setText(message)

            # 显示失败详情
            failed_results = [r for r in results if not r.success()]
            error_messages = "\n".join([
                f"{r.input_file.name}: {r.error}" for r in failed_results[:5]
            ])
            if len(failed_results) > 5:
                error_messages += f"\n... 还有 {len(failed_results) - 5} 个失败"

            QMessageBox.warning(self, "合并完成", f"{message}\n\n失败详情:\n{error_messages}")
        else:
            self._status_label.setText(message)
            QMessageBox.information(self, "合并完成", message)

        logger.info(f"PDF页面合并完成: 成功 {success_count}, 失败 {fail_count}")

        # 清理工作线程
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

    def is_converting(self) -> bool:
        """是否正在转换"""
        return self._worker is not None and self._worker.isRunning()