# -*- coding: utf-8 -*-
"""
GUI Widgets模块初始化

该模块提供PDF工具箱的所有UI组件。

导出内容:
    - DragDropArea: 拖拽上传区域组件
    - FileListWidget: 文件列表组件
    - FileItem: 文件项数据类
    - ProgressWidget: 进度显示组件
    - SettingsPanel: 设置面板组件

使用方式：
    from gui.widgets import DragDropArea, FileListWidget

    # 创建拖拽区域
    drag_area = DragDropArea()
    drag_area.files_dropped.connect(self.on_files_dropped)

    # 创建文件列表
    file_list = FileListWidget()
    file_list.add_files([Path("file.pdf")])
"""
from gui.widgets.drag_drop_area import DragDropArea
from gui.widgets.file_list_widget import FileListWidget, FileItem
from gui.widgets.progress_widget import ProgressWidget
from gui.widgets.settings_panel import SettingsPanel


__all__ = [
    # 拖拽上传组件
    'DragDropArea',

    # 文件列表组件
    'FileListWidget',
    'FileItem',

    # 进度显示组件
    'ProgressWidget',

    # 设置面板组件
    'SettingsPanel',
]