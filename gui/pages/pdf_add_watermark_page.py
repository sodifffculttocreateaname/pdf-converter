# -*- coding: utf-8 -*-
"""
PDF加水印功能页面
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot, QThread
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QRadioButton, QSpinBox,
    QVBoxLayout, QWidget, QButtonGroup, QScrollArea, QFrame, QGridLayout,
    QSlider
)

from config.constants import ConversionStatus, format_file_size
from config.settings import Settings
from converters.pdf_add_watermark import PdfAddWatermarkConverter
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

    def __init__(self, converter: PdfAddWatermarkConverter, files: List[Path],
                 output_dir: Path, watermark_type: str, text: str, font_size: int,
                 opacity: float, position: str, rotation: int, spacing_x: int, spacing_y: int,
                 image_path: Optional[Path], parent=None):
        super().__init__(parent)
        self._converter = converter
        self._files = files
        self._output_dir = output_dir
        self._watermark_type = watermark_type
        self._text = text
        self._font_size = font_size
        self._opacity = opacity
        self._position = position
        self._rotation = rotation
        self._spacing_x = spacing_x
        self._spacing_y = spacing_y
        self._image_path = image_path
        self._cancelled = False

    def run(self):
        def on_progress(progress: ConversionProgress):
            if not self._cancelled:
                self.progress.emit(progress)
        self._converter.set_progress_callback(on_progress)
        self._converter.set_opacity(self._opacity)
        self._converter.set_position(self._position)
        self._converter.set_rotation(self._rotation)
        self._converter.set_spacing(self._spacing_x, self._spacing_y)
        if self._watermark_type == "text":
            self._converter.set_text_watermark(self._text, self._font_size)
        else:
            self._converter.set_image_watermark(self._image_path)
        results = self._converter.convert(self._files, self._output_dir)
        self.finished.emit(results)

    def cancel(self):
        self._cancelled = True
        self._converter.cancel()


class PdfDropArea(QWidget):
    files_dropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self._label = QLabel("拖拽PDF文件到此处上传\n支持 PDF 格式\n或点击选择文件")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._label)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setStyleSheet("PdfDropArea { background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 8px; } PdfDropArea:hover { background-color: #fff3e0; border-color: #FF9800; } QLabel { color: #666; }")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("PdfDropArea { background-color: #fff3e0; border: 2px dashed #FF9800; border-radius: 8px; } QLabel { color: #FF9800; font-weight: bold; }")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("PdfDropArea { background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 8px; } PdfDropArea:hover { background-color: #fff3e0; border-color: #FF9800; } QLabel { color: #666; }")

    def dropEvent(self, event):
        self.setStyleSheet("PdfDropArea { background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 8px; } PdfDropArea:hover { background-color: #fff3e0; border-color: #FF9800; } QLabel { color: #666; }")
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
            files, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)")
            if files:
                self.files_dropped.emit([Path(f) for f in files])


class PdfAddWatermarkPage(QWidget):
    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._files: List[FileItem] = []
        self._image_path: Optional[Path] = None
        self._converter = PdfAddWatermarkConverter()
        self._worker: Optional[ConversionWorker] = None
        self._init_ui()
        logger.info("PDF加水印页面初始化完成")

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
        self._title_label = QLabel("PDF加水印")
        self._title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        left_layout.addWidget(self._title_label)

        # 说明
        desc_label = QLabel("在PDF中添加文字或图片水印，支持透明度、旋转角度和密集程度调节")
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        left_layout.addWidget(desc_label)

        # 文件管理区
        file_manage_widget = QWidget()
        file_manage_widget.setStyleSheet("background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px;")
        file_manage_layout = QHBoxLayout(file_manage_widget)
        file_manage_layout.setContentsMargins(10, 10, 10, 10)
        file_manage_layout.setSpacing(10)

        # 拖拽区域
        self._drop_area = PdfDropArea()
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

        self._count_label = QLabel("待处理文件 (0)")
        self._count_label.setStyleSheet("font-size: 12px; color: #666;")
        list_layout.addWidget(self._count_label)

        self._file_list = QWidget()
        self._file_list_layout = QVBoxLayout(self._file_list)
        self._file_list_layout.setContentsMargins(0, 0, 0, 0)
        self._file_list_layout.setSpacing(5)
        self._file_list_layout.addStretch()
        list_layout.addWidget(self._file_list, 1)

        # 操作按钮
        file_btn_layout = QHBoxLayout()
        file_btn_layout.setSpacing(5)
        self._add_btn = QPushButton("添加")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-size: 12px; } QPushButton:hover { background-color: #1976D2; }")
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
        progress_group = QGroupBox("处理进度")
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
        self._new_conversion_btn.setFixedWidth(100)
        self._new_conversion_btn.setFixedHeight(32)
        self._new_conversion_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:pressed { background-color: #E65100; }
        """)
        self._new_conversion_btn.clicked.connect(self._start_new_conversion)
        action_layout.addWidget(self._new_conversion_btn)
        self._start_btn = QPushButton("开始添加")
        self._start_btn.setFixedWidth(100)
        self._start_btn.setFixedHeight(32)
        self._start_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 4px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #F57C00; } QPushButton:disabled { background-color: #ccc; color: #666; }")
        self._start_btn.clicked.connect(self._start_add)
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

        output_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(output_group)

        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(10)
        basic_layout.setVerticalSpacing(8)

        # 水印类型
        basic_layout.addWidget(QLabel("水印类型:"), 0, 0)
        type_widget = QWidget()
        type_layout = QHBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        self._type_group = QButtonGroup(self)
        self._text_radio = QRadioButton("文字水印")
        self._text_radio.setChecked(True)
        self._type_group.addButton(self._text_radio)
        type_layout.addWidget(self._text_radio)
        self._image_radio = QRadioButton("图片水印")
        self._type_group.addButton(self._image_radio)
        type_layout.addWidget(self._image_radio)
        type_layout.addStretch()
        basic_layout.addWidget(type_widget, 0, 1, 1, 2)

        # 位置模式
        basic_layout.addWidget(QLabel("位置模式:"), 1, 0)
        self._position_combo = QComboBox()
        self._position_combo.addItems(["对角线", "居中", "平铺"])
        basic_layout.addWidget(self._position_combo, 1, 1, 1, 2)

        # 透明度
        basic_layout.addWidget(QLabel("透明度:"), 2, 0)
        opacity_widget = QWidget()
        opacity_layout = QHBoxLayout(opacity_widget)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(10, 100)
        self._opacity_slider.setValue(30)
        self._opacity_slider.setMinimumWidth(80)
        opacity_layout.addWidget(self._opacity_slider, 1)
        self._opacity_label = QLabel("30%")
        self._opacity_label.setMinimumWidth(35)
        opacity_layout.addWidget(self._opacity_label)
        basic_layout.addWidget(opacity_widget, 2, 1, 1, 2)

        basic_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(basic_group)

        # 文字水印设置组
        self._text_group = QGroupBox("文字水印设置")
        self._text_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        text_layout = QGridLayout(self._text_group)
        text_layout.setSpacing(10)
        text_layout.setVerticalSpacing(8)

        # 水印文字
        text_layout.addWidget(QLabel("水印文字:"), 0, 0)
        self._text_edit = QLineEdit()
        self._text_edit.setText("WATERMARK")
        self._text_edit.setPlaceholderText("输入水印文字")
        text_layout.addWidget(self._text_edit, 0, 1, 1, 2)

        # 字体大小和旋转角度
        text_layout.addWidget(QLabel("字体大小:"), 1, 0)
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 200)
        self._font_size_spin.setValue(50)
        text_layout.addWidget(self._font_size_spin, 1, 1)
        text_layout.addWidget(QLabel("旋转:"), 1, 2)
        self._rotation_spin = QSpinBox()
        self._rotation_spin.setRange(-180, 180)
        self._rotation_spin.setValue(45)
        self._rotation_spin.setSuffix("°")
        text_layout.addWidget(self._rotation_spin, 1, 3)

        # 水平间距和垂直间距
        text_layout.addWidget(QLabel("水平间距:"), 2, 0)
        self._spacing_x_spin = QSpinBox()
        self._spacing_x_spin.setRange(50, 500)
        self._spacing_x_spin.setValue(200)
        self._spacing_x_spin.setSuffix(" px")
        text_layout.addWidget(self._spacing_x_spin, 2, 1)
        text_layout.addWidget(QLabel("垂直间距:"), 2, 2)
        self._spacing_y_spin = QSpinBox()
        self._spacing_y_spin.setRange(50, 500)
        self._spacing_y_spin.setValue(150)
        self._spacing_y_spin.setSuffix(" px")
        text_layout.addWidget(self._spacing_y_spin, 2, 3)

        # 提示
        hint_label = QLabel("提示：间距越小水印越密集")
        hint_label.setStyleSheet("color: #888; font-size: 11px;")
        text_layout.addWidget(hint_label, 3, 0, 1, 4)

        text_layout.setColumnStretch(1, 1)
        settings_layout.addWidget(self._text_group)

        # 图片水印设置组
        self._image_group = QGroupBox("图片水印设置")
        self._image_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e0e0e0; border-radius: 6px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        image_layout = QHBoxLayout(self._image_group)
        image_layout.addWidget(QLabel("水印图片:"))
        self._image_path_edit = QLineEdit()
        self._image_path_edit.setReadOnly(True)
        self._image_path_edit.setPlaceholderText("选择图片文件")
        image_layout.addWidget(self._image_path_edit, 1)
        self._select_image_btn = QPushButton("选择")
        self._select_image_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; padding: 5px 10px; font-size: 12px; } QPushButton:hover { background-color: #1976D2; }")
        self._select_image_btn.clicked.connect(self._select_image)
        image_layout.addWidget(self._select_image_btn)
        self._image_group.setVisible(False)
        settings_layout.addWidget(self._image_group)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_widget)

        main_layout.addWidget(settings_scroll, 1)

        # 连接信号
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self._text_radio.toggled.connect(self._on_type_changed)

    def _on_opacity_changed(self, value):
        self._opacity_label.setText(f"{value}%")

    def _on_type_changed(self):
        is_text = self._text_radio.isChecked()
        self._text_group.setVisible(is_text)
        self._image_group.setVisible(not is_text)

    def _select_image(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择水印图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)")
        if files:
            self._image_path = Path(files[0])
            self._image_path_edit.setText(self._image_path.name)

    def _on_files_dropped(self, files: List[Path]):
        self._add_files(files)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", "", "PDF文件 (*.pdf);;所有文件 (*.*)")
        if files:
            self._add_files([Path(f) for f in files])

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
        for file_item in self._files:
            item_widget = self._create_file_item_widget(file_item)
            self._file_list_layout.insertWidget(self._file_list_layout.count() - 1, item_widget)

        self._count_label.setText(f"待处理文件 ({len(self._files)})")

    def _create_file_item_widget(self, file_item: FileItem) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("QWidget { background-color: white; border: 1px solid #e0e0e0; border-radius: 4px; padding: 5px; } QWidget:hover { background-color: #f5f5f5; }")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # PDF标签
        pdf_label = QLabel("PDF")
        pdf_label.setStyleSheet("background-color: #FF9800; color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px; font-weight: bold;")
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

    def _start_add(self):
        if not self._files:
            QMessageBox.warning(self, "提示", "请先添加PDF文件")
            return

        watermark_type = "text" if self._text_radio.isChecked() else "image"
        if watermark_type == "text" and not self._text_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入水印文字")
            return
        if watermark_type == "image" and not self._image_path:
            QMessageBox.warning(self, "提示", "请选择水印图片")
            return

        output_dir = Path(self._output_dir_edit.text())
        ensure_dir(output_dir)

        for file_item in self._files:
            file_item.status = ConversionStatus.PENDING
        self._refresh_file_list()

        self._start_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在添加水印...")

        files = [f.file_path for f in self._files]
        pos_map = {0: "diagonal", 1: "center", 2: "tile"}

        self._worker = ConversionWorker(
            self._converter, files, output_dir,
            watermark_type, self._text_edit.text(), self._font_size_spin.value(),
            self._opacity_slider.value() / 100, pos_map[self._position_combo.currentIndex()],
            self._rotation_spin.value(),
            self._spacing_x_spin.value(), self._spacing_y_spin.value(),
            self._image_path
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_add_finished)
        self._worker.start()

    def _cancel_add(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_label.setText("正在取消...")

    @Slot(object)
    def _on_progress(self, progress: ConversionProgress):
        self._progress_bar.setValue(int(progress.percentage))
        self._status_label.setText(progress.message)

    @Slot(list)
    def _on_add_finished(self, results: List[ConversionResult]):
        success_count = sum(1 for r in results if r.success())
        fail_count = len(results) - success_count

        for result in results:
            for file_item in self._files:
                if file_item.file_path == result.input_file:
                    file_item.status = result.status
                    break

        self._start_btn.setEnabled(True)
        self._progress_bar.setValue(100)

        message = f"添加水印完成: 成功 {success_count} 个"
        if fail_count > 0:
            message += f"，失败 {fail_count} 个"
        self._status_label.setText(message)

        if fail_count > 0:
            QMessageBox.warning(self, "完成", message)
        else:
            QMessageBox.information(self, "完成", message)

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
            self._cancel_add()

        # 清空文件列表
        self._files.clear()
        self._refresh_file_list()

        # 重置进度条和状态
        self._progress_bar.setValue(0)
        self._status_label.setText("就绪 - 请添加文件开始转换")

        # 重置按钮状态
        self._start_btn.setEnabled(True)

        # 重置水印设置
        self._text_edit.clear()
        self._image_path = None
        self._image_path_label.setText("未选择图片")

        logger.info("开始新转换 - 已重置所有状态")

    def is_converting(self) -> bool:
        return self._worker is not None and self._worker.isRunning()