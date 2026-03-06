# -*- coding: utf-8 -*-
"""
进度显示组件

该组件提供可视化的进度显示功能，包括：
- 进度条显示
- 状态文本显示
- 取消按钮

使用方式：
    from gui.widgets import ProgressWidget

    # 创建进度组件
    progress = ProgressWidget()

    # 设置进度
    progress.set_progress(5, 10)  # 50%
    progress.set_percentage(75.5)  # 75.5%

    # 设置状态
    progress.set_status("正在处理...")

    # 连接取消信号
    progress.cancelled.connect(self.on_cancel)
"""
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QProgressBar,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton
)

from utils.logger import get_logger


# 获取模块日志器
logger = get_logger(__name__)


class ProgressWidget(QWidget):
    """
    进度显示组件

    提供可视化的进度显示，包括进度条、状态文本和取消按钮。

    Signals:
        cancelled(): 取消信号，当用户点击取消按钮时发送

    Attributes:
        _progress_bar: 进度条控件
        _status_label: 状态标签
        _cancel_btn: 取消按钮

    Example:
        >>> progress = ProgressWidget()
        >>> progress.start()
        >>> progress.set_progress(5, 10)
        >>> progress.set_status("正在处理文件 5/10")
    """

    # 取消信号
    cancelled = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化进度显示组件

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 初始化UI
        self._init_ui()

        logger.debug("ProgressWidget初始化完成")

    def _init_ui(self) -> None:
        """
        初始化UI布局和控件

        创建进度条、状态标签和取消按钮。
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # ==================== 进度条 ====================
        self._progress_bar = QProgressBar()

        # 设置进度条范围
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)

        # 显示百分比文本
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")

        # 设置最小高度
        self._progress_bar.setMinimumHeight(25)

        # 设置进度条样式
        self._set_progress_style()

        layout.addWidget(self._progress_bar)

        # ==================== 状态标签 ====================
        self._status_label = QLabel("就绪")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # ==================== 取消按钮 ====================
        self._cancel_btn = QPushButton("取消")

        # 初始状态为禁用
        self._cancel_btn.setEnabled(False)

        # 设置最大宽度
        self._cancel_btn.setMaximumWidth(100)

        # 连接点击信号
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)

        # 设置按钮样式
        self._set_button_style()

        # 居中布局
        btn_layout = QVBoxLayout()
        btn_layout.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(btn_layout)

    def _set_progress_style(self) -> None:
        """设置进度条样式"""
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

    def _set_button_style(self) -> None:
        """设置取消按钮样式"""
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)

    # ==================== 事件处理 ====================
    def _on_cancel_clicked(self) -> None:
        """取消按钮点击处理"""
        logger.info("用户点击取消按钮")
        self.cancelled.emit()

    # ==================== 公共方法 ====================
    def set_progress(self, value: int, total: int = 100) -> None:
        """
        设置进度

        根据当前值和总值计算百分比并更新进度条。

        Args:
            value: 当前进度值
            total: 总进度值，默认100

        Example:
            >>> progress.set_progress(5, 10)  # 设置为50%
            >>> progress.set_progress(3, 5)   # 设置为60%
        """
        if total > 0:
            percentage = int((value / total) * 100)
            self._progress_bar.setValue(percentage)
            logger.debug(f"进度更新: {value}/{total} = {percentage}%")
        else:
            self._progress_bar.setValue(0)

    def set_percentage(self, percentage: float) -> None:
        """
        直接设置百分比

        Args:
            percentage: 百分比值 (0-100)

        Example:
            >>> progress.set_percentage(75.5)  # 设置为75.5%
        """
        # 限制范围在0-100
        percentage = max(0, min(100, percentage))
        self._progress_bar.setValue(int(percentage))
        logger.debug(f"进度设置: {percentage:.1f}%")

    def set_status(self, status: str) -> None:
        """
        设置状态文本

        Args:
            status: 状态文本

        Example:
            >>> progress.set_status("正在处理文件...")
        """
        self._status_label.setText(status)
        logger.debug(f"状态更新: {status}")

    def start(self) -> None:
        """
        开始处理状态

        重置进度条为0，设置状态为"处理中"，启用取消按钮。

        Example:
            >>> progress.start()
        """
        self._progress_bar.setValue(0)
        self._status_label.setText("处理中...")
        self._cancel_btn.setEnabled(True)
        logger.info("进度组件启动")

    def complete(self) -> None:
        """
        完成处理状态

        设置进度条为100%，设置状态为"处理完成"，禁用取消按钮。

        Example:
            >>> progress.complete()
        """
        self._progress_bar.setValue(100)
        self._status_label.setText("处理完成")
        self._cancel_btn.setEnabled(False)
        logger.info("进度组件完成")

    def reset(self) -> None:
        """
        重置进度

        重置进度条为0，设置状态为"就绪"，禁用取消按钮。

        Example:
            >>> progress.reset()
        """
        self._progress_bar.setValue(0)
        self._status_label.setText("就绪")
        self._cancel_btn.setEnabled(False)
        logger.debug("进度组件重置")

    def error(self, message: str = "处理失败") -> None:
        """
        设置错误状态

        显示错误消息，禁用取消按钮。

        Args:
            message: 错误消息，默认"处理失败"

        Example:
            >>> progress.error("文件读取失败")
        """
        self._status_label.setText(message)
        self._cancel_btn.setEnabled(False)
        logger.error(f"进度组件错误: {message}")

    def is_cancel_enabled(self) -> bool:
        """
        检查取消按钮是否可用

        Returns:
            bool: 如果取消按钮可用返回True

        Example:
            >>> if progress.is_cancel_enabled():
            ...     print("可以取消")
        """
        return self._cancel_btn.isEnabled()

    def get_progress(self) -> int:
        """
        获取当前进度值

        Returns:
            int: 当前进度百分比 (0-100)
        """
        return self._progress_bar.value()

    def get_status(self) -> str:
        """
        获取当前状态文本

        Returns:
            str: 当前状态文本
        """
        return self._status_label.text()

    def __str__(self) -> str:
        """返回组件的字符串表示"""
        return f"ProgressWidget(progress={self.get_progress()}%, status='{self.get_status()}')"