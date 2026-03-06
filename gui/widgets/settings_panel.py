# -*- coding: utf-8 -*-
"""
设置面板组件

该组件提供转换设置的界面，包括：
- 输出目录选择
- 输出格式选择
- DPI设置
- 压缩质量设置

使用方式：
    from gui.widgets import SettingsPanel

    # 创建设置面板
    settings = SettingsPanel()

    # 获取设置
    output_dir = settings.get_output_dir()
    dpi = settings.get_dpi()

    # 设置输出格式选项
    settings.set_output_formats(['pdf', 'jpg', 'png'])

    # 连接设置变化信号
    settings.settings_changed.connect(self.on_settings_changed)
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFileDialog
)

from config.settings import Settings
from utils.logger import get_logger


# 获取模块日志器
logger = get_logger(__name__)


class SettingsPanel(QWidget):
    """
    设置面板组件

    提供转换参数的设置界面，包括输出目录、格式、DPI和质量等。

    Signals:
        settings_changed(): 设置变化信号，当任何设置改变时发送

    Attributes:
        _output_formats: 可选的输出格式列表
        _output_dir_edit: 输出目录输入框
        _format_combo: 格式选择下拉框
        _dpi_spin: DPI设置输入框
        _quality_spin: 质量设置输入框

    Example:
        >>> settings = SettingsPanel()
        >>> settings.set_output_formats(['pdf', 'jpg'])
        >>> print(settings.get_output_dir())
    """

    # 设置变化信号
    settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化设置面板

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 可选的输出格式列表
        self._output_formats: List[str] = []

        # 初始化UI
        self._init_ui()

        logger.debug("SettingsPanel初始化完成")

    def _init_ui(self) -> None:
        """
        初始化UI布局和控件

        创建输出设置组和质量设置组。
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ==================== 输出设置组 ====================
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)

        # 输出目录行
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("输出目录:"))

        # 输出目录输入框（只读）
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setText(str(Settings.DEFAULT_OUTPUT_DIR))
        self._output_dir_edit.setReadOnly(True)
        dir_layout.addWidget(self._output_dir_edit)

        # 浏览按钮
        self._browse_btn = QPushButton("浏览...")
        self._browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(self._browse_btn)

        output_layout.addLayout(dir_layout)

        # 输出格式行
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))

        # 格式选择下拉框
        self._format_combo = QComboBox()
        self._format_combo.setEnabled(False)  # 初始禁用
        self._format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self._format_combo)

        format_layout.addStretch()  # 左侧弹簧
        output_layout.addLayout(format_layout)

        layout.addWidget(output_group)

        # ==================== 质量设置组 ====================
        self._quality_group = QGroupBox("质量设置")
        quality_layout = QVBoxLayout(self._quality_group)

        # DPI设置行
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("DPI:"))

        self._dpi_spin = QSpinBox()
        self._dpi_spin.setMinimum(72)    # 最小DPI
        self._dpi_spin.setMaximum(600)   # 最大DPI
        self._dpi_spin.setValue(Settings.PDF_DEFAULT_DPI)
        self._dpi_spin.setSuffix(" dpi")  # 后缀
        self._dpi_spin.valueChanged.connect(self._on_dpi_changed)
        dpi_layout.addWidget(self._dpi_spin)

        dpi_layout.addStretch()
        quality_layout.addLayout(dpi_layout)

        # 压缩质量行
        compress_layout = QHBoxLayout()
        compress_layout.addWidget(QLabel("压缩质量:"))

        self._quality_spin = QSpinBox()
        self._quality_spin.setMinimum(1)    # 最小质量
        self._quality_spin.setMaximum(100)  # 最大质量
        self._quality_spin.setValue(Settings.PDF_COMPRESSION_QUALITY)
        self._quality_spin.setSuffix(" %")  # 后缀
        self._quality_spin.valueChanged.connect(self._on_quality_changed)
        compress_layout.addWidget(self._quality_spin)

        compress_layout.addStretch()
        quality_layout.addLayout(compress_layout)

        layout.addWidget(self._quality_group)

        # 添加弹性空间
        layout.addStretch()

    # ==================== 事件处理 ====================
    def _browse_output_dir(self) -> None:
        """浏览输出目录按钮点击处理"""
        # 打开目录选择对话框
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self._output_dir_edit.text()  # 起始目录
        )

        if folder:
            self._output_dir_edit.setText(folder)
            self.settings_changed.emit()
            logger.info(f"输出目录已更改: {folder}")

    def _on_format_changed(self, format_name: str) -> None:
        """
        格式选择变化处理

        Args:
            format_name: 新选择的格式名称
        """
        logger.debug(f"输出格式已更改: {format_name}")
        self.settings_changed.emit()

    def _on_dpi_changed(self, value: int) -> None:
        """
        DPI值变化处理

        Args:
            value: 新的DPI值
        """
        logger.debug(f"DPI已更改: {value}")
        self.settings_changed.emit()

    def _on_quality_changed(self, value: int) -> None:
        """
        质量值变化处理

        Args:
            value: 新的质量值
        """
        logger.debug(f"压缩质量已更改: {value}")
        self.settings_changed.emit()

    # ==================== 公共方法 ====================
    def get_output_dir(self) -> Path:
        """
        获取输出目录路径

        Returns:
            Path: 输出目录路径

        Example:
            >>> output_dir = settings.get_output_dir()
            >>> print(output_dir)
            Path('/home/user/Documents/output')
        """
        return Path(self._output_dir_edit.text())

    def get_output_format(self) -> str:
        """
        获取选择的输出格式

        Returns:
            str: 输出格式名称，如果未选择返回空字符串

        Example:
            >>> format_name = settings.get_output_format()
            >>> print(format_name)
            'pdf'
        """
        return self._format_combo.currentText()

    def get_dpi(self) -> int:
        """
        获取DPI设置值

        Returns:
            int: DPI值 (72-600)

        Example:
            >>> dpi = settings.get_dpi()
            >>> print(dpi)
            150
        """
        return self._dpi_spin.value()

    def get_quality(self) -> int:
        """
        获取压缩质量设置值

        Returns:
            int: 质量值 (1-100)

        Example:
            >>> quality = settings.get_quality()
            >>> print(quality)
            85
        """
        return self._quality_spin.value()

    def set_output_formats(self, formats: List[str]) -> None:
        """
        设置可选的输出格式

        Args:
            formats: 格式列表，如 ['pdf', 'jpg', 'png']

        Example:
            >>> settings.set_output_formats(['pdf', 'jpg'])
        """
        self._output_formats = formats
        self._format_combo.clear()

        if formats:
            self._format_combo.addItems(formats)
            self._format_combo.setEnabled(True)
            logger.debug(f"设置输出格式选项: {formats}")
        else:
            self._format_combo.setEnabled(False)
            logger.debug("清空输出格式选项")

    def set_quality_visible(self, visible: bool) -> None:
        """
        设置质量设置是否可见

        Args:
            visible: True显示，False隐藏

        Example:
            >>> settings.set_quality_visible(False)
        """
        self._quality_group.setVisible(visible)

    def set_dpi_visible(self, visible: bool) -> None:
        """
        设置DPI设置是否可见

        注意：此方法设置整个质量设置组的可见性。
        如果需要单独控制DPI，需要修改布局。

        Args:
            visible: True显示，False隐藏

        Example:
            >>> settings.set_dpi_visible(True)
        """
        # 由于DPI在质量设置组内，这里设置整个组的可见性
        self._quality_group.setVisible(visible)

    def reset_to_defaults(self) -> None:
        """
        重置所有设置为默认值

        Example:
            >>> settings.reset_to_defaults()
        """
        # 重置输出目录
        self._output_dir_edit.setText(str(Settings.DEFAULT_OUTPUT_DIR))

        # 重置DPI
        self._dpi_spin.setValue(Settings.PDF_DEFAULT_DPI)

        # 重置质量
        self._quality_spin.setValue(Settings.PDF_COMPRESSION_QUALITY)

        logger.info("设置已重置为默认值")
        self.settings_changed.emit()

    def __str__(self) -> str:
        """返回组件的字符串表示"""
        return (
            f"SettingsPanel("
            f"output_dir='{self.get_output_dir()}', "
            f"format='{self.get_output_format()}', "
            f"dpi={self.get_dpi()}, "
            f"quality={self.get_quality()})"
        )