# -*- coding: utf-8 -*-
"""
Core模块初始化

该模块是PDF工具箱的核心模块，提供转换器基类和任务调度器。

导出内容:
    - BaseConverter: 转换器抽象基类，所有转换器必须继承此类
    - ConversionResult: 转换结果数据类，存储单个文件的转换结果
    - ConversionProgress: 转换进度数据类，报告转换进度
    - TaskDispatcher: 任务调度器单例类，管理任务队列和转换器注册

使用方式:
    from core import BaseConverter, TaskDispatcher, ConversionResult

    # 创建自定义转换器
    class MyConverter(BaseConverter):
        name = "我的转换器"
        ...

    # 使用调度器
    dispatcher = TaskDispatcher()
    dispatcher.register_converter(MyConverter())
"""
from core.base_converter import (
    BaseConverter,
    ConversionResult,
    ConversionProgress,
)
from core.dispatcher import TaskDispatcher


__all__ = [
    # 转换器基类和数据类
    'BaseConverter',
    'ConversionResult',
    'ConversionProgress',

    # 任务调度器
    'TaskDispatcher',
]