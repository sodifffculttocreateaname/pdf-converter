# -*- coding: utf-8 -*-
"""
GUI模块初始化

该模块是PDF工具箱的图形界面模块，提供：
- 主窗口（MainWindow）
- UI组件（拖拽区域、文件列表、进度显示、设置面板）
- 样式表

导出内容:
    - MainWindow: 主窗口类
    - DragDropArea: 拖拽上传区域组件
    - FileListWidget: 文件列表组件
    - FileItem: 文件项数据类
    - ProgressWidget: 进度显示组件
    - SettingsPanel: 设置面板组件
    - get_stylesheet: 获取全局样式表函数
    - get_list_item_style: 获取列表项样式函数
    - get_button_style: 获取按钮样式函数

使用方式：
    from gui import MainWindow, get_stylesheet

    app = QApplication()
    app.setStyleSheet(get_stylesheet())
    window = MainWindow()
    window.show()
"""
from gui.main_window import MainWindow
from gui.widgets import (
    DragDropArea,
    FileListWidget,
    FileItem,
    ProgressWidget,
    SettingsPanel
)
from gui.styles import get_stylesheet, get_list_item_style, get_button_style


__all__ = [
    # 主窗口
    'MainWindow',

    # UI组件
    'DragDropArea',
    'FileListWidget',
    'FileItem',
    'ProgressWidget',
    'SettingsPanel',

    # 样式表
    'get_stylesheet',
    'get_list_item_style',
    'get_button_style',
]