# -*- coding: utf-8 -*-
"""
文件列表组件

该组件显示待处理的文件列表，支持：
- 显示文件名、大小、类型、状态
- 添加/删除/清空文件
- 右键菜单操作
- 状态更新和颜色指示

使用方式：
    from gui.widgets import FileListWidget

    # 创建文件列表
    file_list = FileListWidget()

    # 添加文件
    file_list.add_files([Path("file1.pdf"), Path("file2.pdf")])

    # 获取文件
    files = file_list.get_files()

    # 连接信号
    file_list.files_changed.connect(self.on_files_changed)
"""
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel
)

from config.constants import ConversionStatus, format_file_size
from utils.file_utils import get_file_size
from utils.logger import get_logger


# 获取模块日志器
logger = get_logger(__name__)


class FileItem:
    """
    文件项数据类

    存储单个文件的元数据和状态信息。

    Attributes:
        file_path: 文件路径
        status: 转换状态
        message: 状态消息

    Properties:
        name: 文件名（不含路径）
        size: 文件大小（字节）
        size_formatted: 格式化的文件大小字符串
        extension: 文件扩展名（大写）
        status_text: 状态文本（中文）

    Example:
        >>> item = FileItem(Path("document.pdf"))
        >>> print(item.name)  # "document.pdf"
        >>> print(item.extension)  # "PDF"
    """

    def __init__(self, file_path: Path):
        """
        初始化文件项

        Args:
            file_path: 文件路径
        """
        # 文件路径
        self.file_path: Path = file_path

        # 转换状态，默认为待处理
        self.status: ConversionStatus = ConversionStatus.PENDING

        # 状态消息
        self.message: str = ""

    @property
    def name(self) -> str:
        """
        获取文件名

        Returns:
            str: 文件名（含扩展名，不含路径）
        """
        return self.file_path.name

    @property
    def size(self) -> int:
        """
        获取文件大小

        Returns:
            int: 文件大小（字节）
        """
        return get_file_size(self.file_path)

    @property
    def size_formatted(self) -> str:
        """
        获取格式化的文件大小

        Returns:
            str: 人类可读的文件大小，如 "1.50 MB"
        """
        return format_file_size(self.size)

    @property
    def extension(self) -> str:
        """
        获取文件扩展名

        Returns:
            str: 文件扩展名（大写，不含点号）
        """
        return self.file_path.suffix.upper().lstrip('.')

    @property
    def status_text(self) -> str:
        """
        获取状态文本

        Returns:
            str: 中文状态文本
        """
        # 状态映射到中文文本
        status_map = {
            ConversionStatus.PENDING: "待处理",
            ConversionStatus.PROCESSING: "处理中",
            ConversionStatus.COMPLETED: "已完成",
            ConversionStatus.FAILED: "失败",
            ConversionStatus.CANCELLED: "已取消"
        }
        return status_map.get(self.status, "未知")

    def __str__(self) -> str:
        """返回文件项的字符串表示"""
        return f"FileItem({self.name}, {self.status_text})"


class FileListWidget(QWidget):
    """
    文件列表组件

    显示和管理待处理文件的列表。提供表格视图展示文件信息，
    支持添加、删除、清空文件操作。

    Signals:
        files_changed(): 文件列表变化信号，当添加或删除文件时发送

    Attributes:
        _files: 文件项列表
        _table: 表格控件
        _count_label: 文件计数标签

    Example:
        >>> file_list = FileListWidget()
        >>> file_list.add_files([Path("doc.pdf")])
        >>> print(file_list.get_file_count())
        1
    """

    # 文件列表变化信号
    files_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化文件列表组件

        Args:
            parent: 父控件
        """
        super().__init__(parent)

        # 文件项列表
        self._files: List[FileItem] = []

        # 初始化UI
        self._init_ui()

        logger.debug("FileListWidget初始化完成")

    def _init_ui(self) -> None:
        """
        初始化UI布局和控件

        创建文件计数标签、文件表格和操作按钮。
        """
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ==================== 文件计数标签 ====================
        self._count_label = QLabel("共 0 个文件")
        layout.addWidget(self._count_label)

        # ==================== 文件表格 ====================
        self._table = QTableWidget()

        # 设置列数和列标题
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["文件名", "大小", "类型", "状态"])

        # 设置选择行为：整行选择
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # 设置选择模式：单选
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # 禁止编辑
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 启用交替行颜色
        self._table.setAlternatingRowColors(True)

        # 隐藏网格线
        self._table.setShowGrid(False)

        # 隐藏垂直标题（行号）
        self._table.verticalHeader().setVisible(False)

        # 设置列宽模式
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 文件名列自动拉伸
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 大小列适应内容
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 类型列适应内容
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 状态列适应内容

        # 启用右键菜单
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # 设置表格样式
        self._set_table_style()

        layout.addWidget(self._table)

        # ==================== 操作按钮 ====================
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 左侧弹簧，使按钮靠右

        # 添加文件按钮
        self._add_btn = QPushButton("添加文件")
        self._add_btn.clicked.connect(self._on_add_files)

        # 添加文件夹按钮
        self._add_folder_btn = QPushButton("添加文件夹")
        self._add_folder_btn.clicked.connect(self._on_add_folder)

        # 清空按钮
        self._clear_btn = QPushButton("清空")
        self._clear_btn.clicked.connect(self.clear_files)

        button_layout.addWidget(self._add_btn)
        button_layout.addWidget(self._add_folder_btn)
        button_layout.addWidget(self._clear_btn)

        layout.addLayout(button_layout)

    def _set_table_style(self) -> None:
        """设置表格样式"""
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)

    # ==================== 事件处理 ====================
    def _show_context_menu(self, pos) -> None:
        """
        显示右键菜单

        Args:
            pos: 鼠标位置（相对于表格）
        """
        # 获取点击位置的项
        item = self._table.itemAt(pos)
        if not item:
            return

        # 获取行号
        row = item.row()

        # 创建右键菜单
        menu = QMenu(self)

        # 添加移除动作
        remove_action = menu.addAction("移除")
        remove_action.triggered.connect(lambda: self._remove_file(row))

        # 显示菜单
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _remove_file(self, row: int) -> None:
        """
        移除指定行的文件

        Args:
            row: 要移除的行号
        """
        # 验证行号有效性
        if 0 <= row < len(self._files):
            removed_file = self._files[row]
            del self._files[row]

            # 刷新表格
            self._refresh_table()

            # 发送信号
            self.files_changed.emit()

            logger.debug(f"移除文件: {removed_file.name}")

    def _on_add_files(self) -> None:
        """添加文件按钮点击处理"""
        from PySide6.QtWidgets import QFileDialog

        # 打开文件选择对话框
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",  # 起始目录
            "所有文件 (*.*)"  # 文件过滤器
        )

        if files:
            # 转换为Path对象
            paths = [Path(f) for f in files]
            self.add_files(paths)

    def _on_add_folder(self) -> None:
        """添加文件夹按钮点击处理"""
        from PySide6.QtWidgets import QFileDialog

        # 打开文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹"
        )

        if folder:
            # 获取文件夹中的所有文件
            folder_path = Path(folder)
            files = [f for f in folder_path.iterdir() if f.is_file()]
            self.add_files(files)

    # ==================== 公共方法 ====================
    def add_files(self, files: List[Path]) -> None:
        """
        添加文件到列表

        过滤已存在的文件，只添加新文件。

        Args:
            files: 要添加的文件路径列表

        Example:
            >>> file_list.add_files([Path("doc1.pdf"), Path("doc2.pdf")])
        """
        added_count = 0

        for file_path in files:
            # 只处理文件
            if not file_path.is_file():
                logger.debug(f"跳过非文件路径: {file_path}")
                continue

            # 检查是否已存在
            if any(f.file_path == file_path for f in self._files):
                logger.debug(f"文件已存在，跳过: {file_path.name}")
                continue

            # 添加文件项
            self._files.append(FileItem(file_path))
            added_count += 1

        # 刷新表格
        self._refresh_table()

        # 发送信号
        self.files_changed.emit()

        logger.info(f"添加文件: {added_count} 个，总计: {len(self._files)} 个")

    def clear_files(self) -> None:
        """
        清空文件列表

        移除所有文件项并刷新显示。

        Example:
            >>> file_list.clear_files()
        """
        count = len(self._files)
        self._files.clear()
        self._refresh_table()
        self.files_changed.emit()

        logger.info(f"清空文件列表: 移除 {count} 个文件")

    def get_files(self) -> List[Path]:
        """
        获取所有文件路径

        Returns:
            List[Path]: 文件路径列表

        Example:
            >>> files = file_list.get_files()
            >>> print(len(files))
            5
        """
        return [f.file_path for f in self._files]

    def get_file_count(self) -> int:
        """
        获取文件数量

        Returns:
            int: 文件数量
        """
        return len(self._files)

    def update_file_status(
        self,
        file_path: Path,
        status: ConversionStatus,
        message: str = ""
    ) -> None:
        """
        更新文件状态

        Args:
            file_path: 要更新的文件路径
            status: 新的状态
            message: 状态消息

        Example:
            >>> file_list.update_file_status(
            ...     Path("doc.pdf"),
            ...     ConversionStatus.COMPLETED,
            ...     "转换成功"
            ... )
        """
        # 查找并更新文件项
        for file_item in self._files:
            if file_item.file_path == file_path:
                file_item.status = status
                file_item.message = message
                logger.debug(f"更新文件状态: {file_item.name} -> {file_item.status_text}")
                break

        # 刷新表格显示
        self._refresh_table()

    # ==================== 内部方法 ====================
    def _refresh_table(self) -> None:
        """
        刷新表格显示

        根据文件列表重新填充表格内容。
        """
        # 阻塞信号，避免频繁刷新
        self._table.setUpdatesEnabled(False)

        try:
            # 设置行数
            self._table.setRowCount(len(self._files))

            # 填充数据
            for row, file_item in enumerate(self._files):
                # 文件名列
                name_item = QTableWidgetItem(file_item.name)
                name_item.setToolTip(str(file_item.file_path))  # 鼠标悬停显示完整路径
                self._table.setItem(row, 0, name_item)

                # 大小列
                size_item = QTableWidgetItem(file_item.size_formatted)
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, 1, size_item)

                # 类型列
                type_item = QTableWidgetItem(file_item.extension)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, 2, type_item)

                # 状态列
                status_item = QTableWidgetItem(file_item.status_text)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 根据状态设置颜色
                if file_item.status == ConversionStatus.COMPLETED:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif file_item.status == ConversionStatus.FAILED:
                    status_item.setForeground(Qt.GlobalColor.red)
                elif file_item.status == ConversionStatus.PROCESSING:
                    status_item.setForeground(Qt.GlobalColor.blue)

                self._table.setItem(row, 3, status_item)

        finally:
            # 恢复更新
            self._table.setUpdatesEnabled(True)

        # 更新文件计数标签
        self._count_label.setText(f"共 {len(self._files)} 个文件")

    def __str__(self) -> str:
        """返回组件的字符串表示"""
        return f"FileListWidget({len(self._files)} files)"