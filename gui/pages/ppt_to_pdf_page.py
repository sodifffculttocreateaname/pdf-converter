# -*- coding: utf-8 -*-
"""
PPT转PDF功能页面

该模块提供PPT转PDF功能的完整界面，包括：
- PPT文件拖拽上传区域
- 文件列表管理
- 进度显示和取消功能
- 后台线程转换

使用方式：
    from gui.pages import PptToPdfPage

    # 创建页面
    page = PptToPdfPage()

    # 添加到布局或堆栈窗口
    stack.addWidget(page)
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFontMetrics
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
    QVBoxLayout,
    QWidget
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.ppt_to_pdf import PptToPdfConverter
from core.base_converter import ConversionProgress, ConversionResult
from utils.file_utils import get_file_size, ensure_dir
from utils.logger import get_logger


logger = get_logger(__name__)

# 支持的PPT文件扩展名
PPT_EXTENSIONS = {'ppt', 'pptx'}


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


class ConversionWorker(QThread):
    """
    转换工作线程

    在后台执行PPT转PDF转换任务，避免阻塞UI。

    Signals:
        progress: 进度信号，参数为ConversionProgress对象
        finished: 完成信号，参数为结果列表
    """

    progress = Signal(object)  # ConversionProgress
    finished = Signal(list)    # List[ConversionResult]

    def __init__(
        self,
        converter: PptToPdfConverter,
        files: List[Path],
        output_dir: Path,
        parent=None
    ):
        """
        初始化工作线程

        Args:
            converter: PPT转PDF转换器实例
            files: 要转换的文件列表
            output_dir: 输出目录
            parent: 父对象
        """
        super().__init__(parent)
        self._converter = converter
        self._files = files
        self._output_dir = output_dir
        self._cancelled = False

    def run(self):
        """执行转换任务"""
        # 设置进度回调
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)

        self._converter.set_progress_callback(on_progress)

        # 执行转换
        results = self._converter.convert(
            self._files,
            self._output_dir
        )

        self.finished.emit(results)

    def cancel(self):
        """取消转换"""
        self._cancelled = True
        self._converter.cancel()


class PptDropArea(QWidget):
    """
    PPT文件拖拽上传区域

    专门用于PPT文件（.ppt, .pptx）的拖拽上传组件（紧凑版本，用于左右分栏布局）。

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
            "拖拽PPT文件到此处\n"
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
            PptDropArea {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
            PptDropArea:hover {
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
            PptDropArea {
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
                # 检查是否为PPT格式
                ext = path.suffix.lower().lstrip('.')
                if ext in PPT_EXTENSIONS:
                    files.append(path)
            elif path.is_dir():
                # 获取文件夹中的PPT文件
                for item in path.iterdir():
                    if item.is_file():
                        ext = item.suffix.lower().lstrip('.')
                        if ext in PPT_EXTENSIONS:
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
        # 构建PPT过滤器
        filters = [
            "PowerPoint文件 (*.ppt *.pptx)",
            "PPT文件 (*.ppt)",
            "PPTX文件 (*.pptx)",
            "所有文件 (*.*)"
        ]

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PPT文件",
            "",
            ";;".join(filters)
        )

        if files:
            paths = [Path(f) for f in files]
            self.files_dropped.emit(paths)


class PptToPdfPage(QWidget):
    """
    PPT转PDF功能页面

    提供完整的PPT转PDF功能界面，包括：
    - PPT文件拖拽/选择上传
    - 文件列表管理
    - 转换进度显示
    - 开始/取消转换按钮

    Signals:
        back_requested: 请求返回主页面信号
    """

    # 请求返回主页面信号
    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化PPT转PDF页面

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 文件列表
        self._files: List[FileItem] = []

        # 转换器
        self._converter = PptToPdfConverter()

        # 工作线程
        self._worker: Optional[ConversionWorker] = None

        # 初始化UI
        self._init_ui()

        logger.info("PPT转PDF页面初始化完成")

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
        self._title_label = QLabel("PPT转PDF")
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
        self._drop_area = PptDropArea()
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
        progress_group = QGroupBox("转换进度")
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
        self._start_btn = QPushButton("开始转换")
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
        self._start_btn.clicked.connect(self._start_conversion)
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

        # 支持格式说明
        format_group = QGroupBox("支持的格式")
        format_group.setStyleSheet("""
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
        format_layout = QVBoxLayout(format_group)
        format_layout.setContentsMargins(10, 15, 10, 10)

        format_label = QLabel("PPT、PPTX")
        format_label.setStyleSheet("color: #666; font-size: 12px;")
        format_label.setWordWrap(True)
        format_layout.addWidget(format_label)

        settings_layout.addWidget(format_group)

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
        filters = [
            "PowerPoint文件 (*.ppt *.pptx)",
            "PPT文件 (*.ppt)",
            "PPTX文件 (*.pptx)",
            "所有文件 (*.*)"
        ]

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PPT文件",
            "",
            ";;".join(filters)
        )

        if files:
            paths = [Path(f) for f in files]
            self._add_files(paths)

    def _on_add_folder(self):
        """添加文件夹按钮点击处理"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择PPT文件夹"
        )

        if folder:
            folder_path = Path(folder)
            # 过滤PPT文件
            files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower().lstrip('.') in PPT_EXTENSIONS
            ]
            self._add_files(files)

    def _remove_file(self, row: int):
        """移除指定行的文件"""
        if 0 <= row < len(self._files):
            removed_file = self._files[row]
            del self._files[row]
            self._refresh_file_list()
            logger.debug(f"移除文件: {removed_file.name}")

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
            ext = file_path.suffix.lower().lstrip('.')
            if ext not in PPT_EXTENSIONS:
                logger.debug(f"忽略非PPT文件: {file_path.name}")
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

        # 文件图标（使用扩展名）
        ext_label = QLabel(file_item.extension[:3])
        ext_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                color: #1976D2;
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
        name_label.setToolTip(str(file_item.file_path))  # 悬停显示完整路径
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

    # ==================== 转换操作 ====================
    def _start_conversion(self):
        """开始转换"""
        # 检查文件列表
        if not self._files:
            QMessageBox.warning(self, "提示", "请先添加要转换的PPT文件")
            return

        # 获取设置
        output_dir = Path(self._output_dir_edit.text())

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
        self._status_label.setText("正在转换...")

        # 创建工作线程
        files = [f.file_path for f in self._files]
        self._worker = ConversionWorker(
            self._converter,
            files,
            output_dir
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_conversion_finished)

        # 启动转换
        self._worker.start()
        logger.info(f"开始PPT转PDF转换: {len(files)} 个文件")

    def _cancel_conversion(self):
        """取消转换"""
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
    def _on_conversion_finished(self, results: List[ConversionResult]):
        """转换完成处理"""
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

        message = f"转换完成: 成功 {success_count} 个"
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

            QMessageBox.warning(self, "转换完成", f"{message}\n\n失败详情:\n{error_messages}")
        else:
            self._status_label.setText(message)
            QMessageBox.information(self, "转换完成", message)

        logger.info(f"PPT转PDF转换完成: 成功 {success_count}, 失败 {fail_count}")

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
            self._cancel_conversion()

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
        """
        检查是否正在转换

        Returns:
            如果正在转换返回True
        """
        return self._worker is not None and self._worker.isRunning()