# -*- coding: utf-8 -*-
"""
PDF合并功能页面

该模块提供PDF合并功能的完整界面，包括：
- PDF拖拽上传区域
- 文件列表管理（支持排序调整）
- 输出文件名设置
- 进度显示和取消功能
- 后台线程合并

使用方式：
    from gui.pages import PdfMergePage

    # 创建页面
    page = PdfMergePage()

    # 添加到布局或堆栈窗口
    stack.addWidget(page)
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
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QVBoxLayout,
    QWidget
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.pdf_merge import PdfMergeConverter
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
        page_count: PDF页数
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
        self.page_count: int = 0
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
    def extension(self) -> str:
        """文件扩展名（大写，不含点号）"""
        return self.file_path.suffix.upper().lstrip('.')

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


class MergeWorker(QThread):
    """
    合并工作线程

    在后台执行PDF合并任务，避免阻塞UI。

    Signals:
        progress: 进度信号，参数为ConversionProgress对象
        finished: 完成信号，参数为结果列表
    """

    progress = Signal(object)  # ConversionProgress
    finished = Signal(list)    # List[ConversionResult]

    def __init__(
        self,
        converter: PdfMergeConverter,
        files: List[Path],
        output_dir: Path,
        output_filename: str,
        parent=None
    ):
        """
        初始化工作线程

        Args:
            converter: PDF合并转换器实例
            files: 要合并的文件列表
            output_dir: 输出目录
            output_filename: 输出文件名
            parent: 父对象
        """
        super().__init__(parent)
        self._converter = converter
        self._files = files
        self._output_dir = output_dir
        self._output_filename = output_filename
        self._cancelled = False

    def run(self):
        """执行合并任务"""
        # 设置进度回调
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)

        self._converter.set_progress_callback(on_progress)

        # 执行合并
        results = self._converter.convert(
            self._files,
            self._output_dir,
            output_filename=self._output_filename
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
                background-color: #e8f4e8;
                border-color: #4CAF50;
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
                background-color: #e8f4e8;
                border: 2px dashed #4CAF50;
                border-radius: 8px;
            }
            QLabel {
                color: #4CAF50;
                font-size: 14px;
                font-weight: bold;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self._set_normal_style()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        self._set_normal_style()

        files: List[Path] = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                # 检查是否为PDF格式
                ext = path.suffix.lower().lstrip('.')
                if ext == 'pdf':
                    files.append(path)
            elif path.is_dir():
                # 获取文件夹中的PDF文件
                for item in path.iterdir():
                    if item.is_file():
                        ext = item.suffix.lower().lstrip('.')
                        if ext == 'pdf':
                            files.append(item)

        if files:
            self.files_dropped.emit(files)

        event.acceptProposedAction()

    def mousePressEvent(self, event):
        """鼠标点击事件 - 打开文件选择对话框"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()

    def _open_file_dialog(self):
        """打开文件选择对话框"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )

        if files:
            paths = [Path(f) for f in files]
            self.files_dropped.emit(paths)


class PdfMergePage(QWidget):
    """
    PDF合并功能页面

    提供完整的PDF合并功能界面，包括：
    - PDF拖拽/选择上传
    - 文件列表管理（支持排序调整）
    - 输出文件名设置
    - 转换进度显示
    - 开始/取消合并按钮

    Signals:
        back_requested: 请求返回主页面信号
    """

    # 请求返回主页面信号
    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化PDF合并页面

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 文件列表
        self._files: List[FileItem] = []

        # 转换器
        self._converter = PdfMergeConverter()

        # 工作线程
        self._worker: Optional[MergeWorker] = None

        # 初始化UI
        self._init_ui()

        logger.info("PDF合并页面初始化完成")

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
        self._title_label = QLabel("PDF合并")
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_layout.addWidget(self._title_label)

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
        self._count_label = QLabel("待合并文件 (0)")
        self._count_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #555;")
        list_layout.addWidget(self._count_label)

        # 文件表格
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["文件名", "大小", "状态"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)

        # 设置列宽
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # 启用右键菜单
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # 设置表格样式
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 4px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        list_layout.addWidget(self._table, 1)

        # 文件操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        # 排序按钮
        self._up_btn = QPushButton("上移")
        self._up_btn.setFixedHeight(26)
        self._up_btn.setStyleSheet("""
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
        self._up_btn.clicked.connect(self._move_file_up)
        btn_layout.addWidget(self._up_btn)

        self._down_btn = QPushButton("下移")
        self._down_btn.setFixedHeight(26)
        self._down_btn.setStyleSheet("""
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
        self._down_btn.clicked.connect(self._move_file_down)
        btn_layout.addWidget(self._down_btn)

        btn_layout.addStretch()

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

        self._add_folder_btn = QPushButton("文件夹")
        self._add_folder_btn.setFixedHeight(26)
        self._add_folder_btn.setStyleSheet("""
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
        self._add_folder_btn.clicked.connect(self._on_add_folder)
        btn_layout.addWidget(self._add_folder_btn)

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
        self._start_btn = QPushButton("开始合并")
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

        # 输出目录
        merge_layout.addWidget(QLabel("输出目录:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setText(str(Settings.DEFAULT_OUTPUT_DIR))
        self._output_dir_edit.setReadOnly(True)
        self._output_dir_edit.setMinimumWidth(150)
        merge_layout.addWidget(self._output_dir_edit, 0, 1)

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
        merge_layout.addWidget(self._browse_btn, 0, 2)

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
        merge_layout.addWidget(self._open_folder_btn, 0, 3)

        # 输出文件名
        merge_layout.addWidget(QLabel("输出文件名:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        self._filename_edit = QLineEdit()
        self._filename_edit.setText("merged.pdf")
        self._filename_edit.setPlaceholderText("merged.pdf")
        self._filename_edit.setMinimumWidth(150)
        merge_layout.addWidget(self._filename_edit, 1, 1, 1, 2)

        merge_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(merge_group)

        # 使用说明组
        hint_group = QGroupBox("使用说明")
        hint_group.setStyleSheet("""
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
        hint_layout = QVBoxLayout(hint_group)
        hint_layout.setContentsMargins(10, 15, 10, 10)

        hint_label = QLabel("将多个PDF文件合并为一个PDF文件。\n使用上移/下移按钮调整合并顺序。")
        hint_label.setStyleSheet("color: #666; font-size: 12px;")
        hint_label.setWordWrap(True)
        hint_layout.addWidget(hint_label)

        settings_layout.addWidget(hint_group)

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
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )

        if files:
            paths = [Path(f) for f in files]
            self._add_files(paths)

    def _on_add_folder(self):
        """添加文件夹按钮点击处理"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择PDF文件夹"
        )

        if folder:
            folder_path = Path(folder)
            # 过滤PDF文件
            files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() == '.pdf'
            ]
            self._add_files(files)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
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
        """移除指定行的文件"""
        if 0 <= row < len(self._files):
            removed_file = self._files[row]
            del self._files[row]
            self._refresh_table()
            logger.debug(f"移除文件: {removed_file.name}")

    def _move_file_up(self):
        """上移选中的文件"""
        selected = self._table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if row <= 0 or row >= len(self._files):
            return

        # 交换位置
        self._files[row], self._files[row - 1] = self._files[row - 1], self._files[row]
        self._refresh_table()

        # 重新选中
        self._table.selectRow(row - 1)

    def _move_file_down(self):
        """下移选中的文件"""
        selected = self._table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if row < 0 or row >= len(self._files) - 1:
            return

        # 交换位置
        self._files[row], self._files[row + 1] = self._files[row + 1], self._files[row]
        self._refresh_table()

        # 重新选中
        self._table.selectRow(row + 1)

    def _browse_output_dir(self):
        """浏览输出目录"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self._output_dir_edit.text()
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
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

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
            ext = file_path.suffix.lower().lstrip('.')
            if ext != 'pdf':
                logger.debug(f"忽略非PDF文件: {file_path.name}")
                continue

            # 检查重复
            if any(f.file_path == file_path for f in self._files):
                logger.debug(f"文件已存在，跳过: {file_path.name}")
                continue

            self._files.append(FileItem(file_path))
            added_count += 1

        self._refresh_table()
        logger.info(f"添加文件: {added_count} 个，总计: {len(self._files)} 个")

    def _clear_files(self):
        """清空文件列表"""
        count = len(self._files)
        self._files.clear()
        self._refresh_table()
        logger.info(f"清空文件列表: 移除 {count} 个文件")

    def _refresh_table(self):
        """刷新表格显示"""
        self._table.setUpdatesEnabled(False)

        try:
            self._table.setRowCount(len(self._files))

            for row, file_item in enumerate(self._files):
                # 文件名
                name_item = QTableWidgetItem(file_item.name)
                name_item.setToolTip(str(file_item.file_path))
                self._table.setItem(row, 0, name_item)

                # 大小
                size_item = QTableWidgetItem(file_item.size_formatted)
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, 1, size_item)

                # 状态
                status_item = QTableWidgetItem(file_item.status_text)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 根据状态设置颜色
                if file_item.status == ConversionStatus.COMPLETED:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif file_item.status == ConversionStatus.FAILED:
                    status_item.setForeground(Qt.GlobalColor.red)
                elif file_item.status == ConversionStatus.PROCESSING:
                    status_item.setForeground(Qt.GlobalColor.blue)

                self._table.setItem(row, 2, status_item)

        finally:
            self._table.setUpdatesEnabled(True)

        self._count_label.setText(f"待合并文件 ({len(self._files)})")

    # ==================== 合并操作 ====================
    def _start_merge(self):
        """开始合并"""
        # 检查文件列表
        if len(self._files) < 2:
            QMessageBox.warning(self, "提示", "请至少添加2个PDF文件进行合并")
            return

        # 获取设置
        output_dir = Path(self._output_dir_edit.text())
        output_filename = self._filename_edit.text().strip()
        if not output_filename:
            output_filename = "merged.pdf"

        # 确保输出目录存在
        ensure_dir(output_dir)

        # 重置文件状态
        for file_item in self._files:
            file_item.status = ConversionStatus.PENDING
            file_item.message = ""
        self._refresh_table()

        # 更新UI状态
        self._start_btn.setEnabled(False)
        self._up_btn.setEnabled(False)
        self._down_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在合并...")

        # 创建工作线程
        files = [f.file_path for f in self._files]
        self._worker = MergeWorker(
            self._converter,
            files,
            output_dir,
            output_filename
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_merge_finished)

        # 启动合并
        self._worker.start()
        logger.info(f"开始PDF合并: {len(files)} 个文件")

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
            self._refresh_table()

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

        self._refresh_table()

        # 获取结果
        result = results[0] if results else None

        # 更新UI状态
        self._start_btn.setEnabled(True)
        self._up_btn.setEnabled(True)
        self._down_btn.setEnabled(True)

        if result and result.success():
            self._progress_bar.setValue(100)
            message = result.message or "合并成功"
            self._status_label.setText(message)
            QMessageBox.information(self, "合并完成", message)
            logger.info(f"PDF合并成功: {message}")
        else:
            error = result.error if result else "未知错误"
            self._status_label.setText(f"合并失败: {error}")
            QMessageBox.warning(self, "合并失败", f"合并过程中出现错误:\n{error}")
            logger.error(f"PDF合并失败: {error}")

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
        self._refresh_table()

        # 重置进度条和状态
        self._progress_bar.setValue(0)
        self._status_label.setText("就绪 - 请添加文件开始转换")

        # 重置按钮状态
        self._start_btn.setEnabled(True)
        self._up_btn.setEnabled(True)
        self._down_btn.setEnabled(True)

        logger.info("开始新转换 - 已重置所有状态")

    def is_converting(self) -> bool:
        """
        检查是否正在进行合并

        Returns:
            bool: 如果正在合并返回True
        """
        return self._worker is not None and self._worker.isRunning()
