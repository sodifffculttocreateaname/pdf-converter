# -*- coding: utf-8 -*-
"""
GUI Styles模块初始化

该模块提供应用程序的样式表定义。

导出内容:
    - get_stylesheet: 获取全局样式表
    - get_list_item_style: 获取列表项样式
    - get_button_style: 获取按钮样式

使用方式：
    from gui.styles import get_stylesheet, get_button_style

    # 应用全局样式
    app.setStyleSheet(get_stylesheet())

    # 设置按钮样式
    button.setStyleSheet(get_button_style("success"))
"""
from gui.styles.stylesheet import get_stylesheet, get_list_item_style, get_button_style


__all__ = [
    # 样式表函数
    'get_stylesheet',
    'get_list_item_style',
    'get_button_style',
]