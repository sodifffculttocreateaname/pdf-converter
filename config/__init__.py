# -*- coding: utf-8 -*-
"""
Config模块初始化

该模块统一导出配置相关的类、枚举和函数，方便其他模块导入使用。

导出内容:
    - Settings: 全局配置类
    - ConversionStatus: 转换状态枚举
    - FileFormat: 文件格式枚举
    - IMAGE_FORMATS: 图片格式列表
    - IMAGE_EXTENSIONS: 图片扩展名列表
    - DOCUMENT_FORMATS: 文档格式映射
    - MODULE_NAMES: 功能模块名称映射
    - format_file_size: 文件大小格式化函数
    - get_file_format: 获取文件格式枚举函数
    - is_image_extension: 检查是否为图片扩展名函数
    - is_document_extension: 检查是否为文档扩展名函数

使用方式:
    from config import Settings, ConversionStatus, MODULE_NAMES
    或者:
    from config.settings import Settings
"""
from config.settings import Settings
from config.constants import (
    ConversionStatus,
    FileFormat,
    IMAGE_FORMATS,
    IMAGE_EXTENSIONS,
    DOCUMENT_FORMATS,
    MODULE_NAMES,
    format_file_size,
    get_file_format,
    is_image_extension,
    is_document_extension,
)


__all__ = [
    # 配置类
    'Settings',

    # 枚举类
    'ConversionStatus',
    'FileFormat',

    # 常量列表和字典
    'IMAGE_FORMATS',
    'IMAGE_EXTENSIONS',
    'DOCUMENT_FORMATS',
    'MODULE_NAMES',

    # 工具函数
    'format_file_size',
    'get_file_format',
    'is_image_extension',
    'is_document_extension',
]