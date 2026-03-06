# -*- coding: utf-8 -*-
"""
拖拽上传组件

该组件提供一个支持拖拽上传的区域，用户可以：
- 拖拽文件到区域上传
- 拖拽文件夹上传（自动获取其中的文件）
- 点击区域打开文件选择对话框

使用方式：
    from gui.widgets import DragDropArea

    # 创建拖拽区域
    drag_area = DragDropArea()

    # 连接信号
    drag_area.files_dropped.connect(self.on_files_dropped)

    # 设置提示文本
    drag_area.set_text("拖拽图片文件到此处")
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DragDropArea(QWidget):
    """
    拖拽上传区域组件

    提供可视化的拖拽上传区域，支持文件和文件夹的拖拽上传。

    Signals:
        files_dropped(list): 文件拖放信号，参数为Path列表

    Attributes:
        _label: 提示标签控件
        _default_style: 默认样式
        _hover_style: 悬停/拖拽样式

    Example:
        >>> drag_area = DragDropArea()
        >>> drag_area.files_dropped.connect(lambda files: print(files))
    """

    # ==================== 信号定义 ====================
    # 文件拖放信号，参数为List[Path]
    files_dropped = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化拖拽区域

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 初始化UI和样式
        self._init_ui()
        self._init_style()

    def _init_ui(self) -> None:
        """
        初始化UI布局

        创建提示标签并设置布局。
        """
        # 创建垂直布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 创建提示标签
        self._label = QLabel("拖拽文件到此处上传\n或点击选择文件")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        # 启用拖拽功能
        self.setAcceptDrops(True)

        # 设置鼠标样式为手型
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _init_style(self) -> None:
        """
        初始化/重置样式

        设置默认的样式表，包括背景色、边框等。
        """
        # 设置最小高度
        self.setMinimumHeight(120)

        # 应用默认样式
        self.setStyleSheet("""
            DragDropArea {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
            DragDropArea:hover {
                background-color: #e8f4e8;
                border-color: #4CAF50;
            }
            QLabel {
                color: #666;
                font-size: 14px;
            }
        """)

    def _get_drag_style(self) -> str:
        """
        获取拖拽悬停样式

        Returns:
            str: 拖拽悬停时的样式表
        """
        return """
            DragDropArea {
                background-color: #e8f4e8;
                border: 2px dashed #4CAF50;
                border-radius: 8px;
            }
            QLabel {
                color: #4CAF50;
                font-size: 14px;
                font-weight: bold;
            }
        """

    # ==================== 事件处理 ====================
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        拖拽进入事件

        当拖拽内容进入组件区域时触发。
        如果拖拽内容包含URL（文件），则接受事件并显示拖拽样式。

        Args:
            event: 拖拽进入事件对象
        """
        # 检查拖拽内容是否包含URL
        if event.mimeData().hasUrls():
            # 接受拖拽事件
            event.acceptProposedAction()
            # 应用拖拽悬停样式
            self.setStyleSheet(self._get_drag_style())
        else:
            # 拒绝非文件拖拽
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """
        拖拽离开事件

        当拖拽内容离开组件区域时触发。
        恢复默认样式。

        Args:
            event: 拖拽离开事件对象
        """
        # 恢复默认样式
        self._init_style()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        拖拽放下事件

        当用户放下拖拽内容时触发。
        解析拖拽的文件/文件夹并发送信号。

        Args:
            event: 拖拽放下事件对象
        """
        # 恢复默认样式
        self._init_style()

        # 收集所有文件路径
        files: List[Path] = []

        # 遍历拖拽的URL
        for url in event.mimeData().urls():
            # 转换为本地文件路径
            path = Path(url.toLocalFile())

            if path.is_file():
                # 单个文件，直接添加
                files.append(path)
            elif path.is_dir():
                # 文件夹，获取其中的所有文件
                for item in path.iterdir():
                    if item.is_file():
                        files.append(item)

        # 如果有文件，发送信号
        if files:
            self.files_dropped.emit(files)

        # 接受事件
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        """
        鼠标点击事件

        当用户点击组件时，打开文件选择对话框。

        Args:
            event: 鼠标事件对象
        """
        # 只响应左键点击
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()

    def _open_file_dialog(self) -> None:
        """
        打开文件选择对话框

        允许用户通过点击选择文件。
        """
        from PySide6.QtWidgets import QFileDialog

        # 打开文件选择对话框
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",  # 起始目录
            "所有文件 (*.*)"  # 文件过滤器
        )

        # 如果选择了文件，发送信号
        if files:
            paths = [Path(f) for f in files]
            self.files_dropped.emit(paths)

    # ==================== 公共方法 ====================
    def set_text(self, text: str) -> None:
        """
        设置提示文本

        Args:
            text: 要显示的提示文本，可以使用换行符

        Example:
            >>> drag_area.set_text("拖拽图片文件到此处\n支持 JPG、PNG 格式")
        """
        self._label.setText(text)

    def get_text(self) -> str:
        """
        获取当前提示文本

        Returns:
            str: 当前的提示文本
        """
        return self._label.text()