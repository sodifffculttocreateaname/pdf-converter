# -*- coding: utf-8 -*-
"""
QSS样式表模块

该模块提供应用程序的样式表定义，包括：
- 全局样式表
- 组件专用样式

样式采用Material Design风格，使用蓝色作为主色调。

使用方式：
    from gui.styles import get_stylesheet

    # 应用全局样式
    app.setStyleSheet(get_stylesheet())
"""


def get_stylesheet() -> str:
    """
    获取全局样式表

    返回应用程序的全局样式表字符串，包括：
    - 全局字体设置
    - 按钮样式（普通、成功、危险）
    - 输入框样式
    - 下拉框样式
    - 数字输入框样式
    - 分组框样式
    - 列表样式
    - 滚动条样式
    - 状态栏样式
    - 工具提示样式
    - 菜单样式

    Returns:
        str: QSS样式表字符串

    Example:
        >>> from PySide6.QtWidgets import QApplication
        >>> app = QApplication()
        >>> app.setStyleSheet(get_stylesheet())
    """
    return """
        /* ==================== 全局样式 ==================== */
        QWidget {
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            font-size: 13px;
        }

        /* ==================== 主窗口 ==================== */
        QMainWindow {
            background-color: #f5f5f5;
        }

        /* ==================== 按钮样式 ==================== */
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #1976D2;
        }

        QPushButton:pressed {
            background-color: #0D47A1;
        }

        QPushButton:disabled {
            background-color: #BDBDBD;
            color: #757575;
        }

        /* 成功按钮 - 绿色 */
        QPushButton[class="success"] {
            background-color: #4CAF50;
        }

        QPushButton[class="success"]:hover {
            background-color: #388E3C;
        }

        /* 危险按钮 - 红色 */
        QPushButton[class="danger"] {
            background-color: #f44336;
        }

        QPushButton[class="danger"]:hover {
            background-color: #d32f2f;
        }

        /* ==================== 输入框样式 ==================== */
        QLineEdit {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: white;
        }

        QLineEdit:focus {
            border-color: #2196F3;
        }

        QLineEdit:read-only {
            background-color: #f5f5f5;
        }

        /* ==================== 下拉框样式 ==================== */
        QComboBox {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: white;
            min-width: 100px;
        }

        QComboBox:focus {
            border-color: #2196F3;
        }

        QComboBox::drop-down {
            border: none;
            width: 24px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #666;
            margin-right: 8px;
        }

        QComboBox QAbstractItemView {
            border: 1px solid #ddd;
            background-color: white;
            selection-background-color: #e3f2fd;
            selection-color: black;
        }

        /* ==================== 数字输入框样式 ==================== */
        QSpinBox {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 6px 10px;
            background-color: white;
        }

        QSpinBox:focus {
            border-color: #2196F3;
        }

        /* ==================== 分组框样式 ==================== */
        QGroupBox {
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            background-color: #f5f5f5;
        }

        /* ==================== 列表样式 ==================== */
        QListWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }

        QListWidget::item {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }

        QListWidget::item:selected {
            background-color: #e3f2fd;
            color: #1976D2;
        }

        QListWidget::item:hover {
            background-color: #f5f5f5;
        }

        /* ==================== 滚动条样式 ==================== */
        /* 垂直滚动条 */
        QScrollBar:vertical {
            border: none;
            background-color: #f5f5f5;
            width: 10px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background-color: #ccc;
            border-radius: 5px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #999;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }

        /* 水平滚动条 */
        QScrollBar:horizontal {
            border: none;
            background-color: #f5f5f5;
            height: 10px;
            margin: 0;
        }

        QScrollBar::handle:horizontal {
            background-color: #ccc;
            border-radius: 5px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #999;
        }

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0;
        }

        /* ==================== 状态栏样式 ==================== */
        QStatusBar {
            background-color: #f5f5f5;
            border-top: 1px solid #ddd;
        }

        /* ==================== 工具提示样式 ==================== */
        QToolTip {
            background-color: #333;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px;
        }

        /* ==================== 菜单样式 ==================== */
        QMenu {
            background-color: white;
            border: 1px solid #ddd;
        }

        QMenu::item {
            padding: 8px 20px;
        }

        QMenu::item:selected {
            background-color: #e3f2fd;
        }

        QMenu::separator {
            height: 1px;
            background-color: #ddd;
            margin: 5px 0;
        }
    """


def get_list_item_style(selected: bool = False) -> str:
    """
    获取列表项样式

    返回列表项的内联样式字符串，用于QListWidget等控件。

    Args:
        selected: 是否选中状态

    Returns:
        str: QSS样式字符串

    Example:
        >>> style = get_list_item_style(selected=True)
        >>> item.setStyleSheet(style)
    """
    if selected:
        return """
            background-color: #e3f2fd;
            color: #1976D2;
            border-left: 3px solid #2196F3;
        """
    return """
        background-color: white;
        border-left: 3px solid transparent;
    """


def get_button_style(style_type: str = "primary") -> str:
    """
    获取按钮样式

    根据类型返回按钮的内联样式字符串。

    Args:
        style_type: 按钮类型，可选值：
            - "primary": 主要按钮（蓝色）
            - "success": 成功按钮（绿色）
            - "danger": 危险按钮（红色）
            - "warning": 警告按钮（橙色）

    Returns:
        str: QSS样式字符串

    Example:
        >>> button.setStyleSheet(get_button_style("success"))
    """
    styles = {
        "primary": """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
        """,
        "success": """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:pressed { background-color: #1B5E20; }
        """,
        "danger": """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:pressed { background-color: #b71c1c; }
        """,
        "warning": """
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:pressed { background-color: #E65100; }
        """,
    }

    return styles.get(style_type, styles["primary"])