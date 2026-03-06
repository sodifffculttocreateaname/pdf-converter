# -*- coding: utf-8 -*-
"""
Utils模块初始化

该模块提供工具函数和日志功能。

导出内容:
    # 文件操作工具
    - ensure_dir: 确保目录存在
    - get_file_size: 获取文件大小
    - get_file_size_formatted: 获取格式化的文件大小
    - is_valid_file: 检查文件是否有效
    - get_file_extension: 获取文件扩展名
    - is_image_file: 检查是否为图片文件
    - get_unique_filename: 获取唯一文件名
    - cleanup_temp_files: 清理临时文件
    - copy_file: 复制文件
    - move_file: 移动文件
    - delete_file: 删除文件
    - get_files_in_directory: 获取目录中的文件列表
    - get_directory_size: 获取目录大小

    # 日志工具
    - get_logger: 获取日志器
    - configure_logger: 配置日志系统
    - set_log_level: 设置日志级别
    - get_log_file_path: 获取日志文件路径
    - get_error_log_path: 获取错误日志文件路径

使用方式：
    from utils import get_logger, ensure_dir

    logger = get_logger(__name__)
    logger.info("开始处理")

    output_dir = ensure_dir(Path("output"))
"""
from utils.file_utils import (
    # 目录操作
    ensure_dir,
    get_directory_size,

    # 文件信息
    get_file_size,
    get_file_size_formatted,
    get_file_extension,

    # 文件验证
    is_valid_file,
    is_image_file,

    # 文件名处理
    get_unique_filename,

    # 文件操作
    copy_file,
    move_file,
    delete_file,

    # 目录遍历
    get_files_in_directory,

    # 清理功能
    cleanup_temp_files,
)

from utils.logger import (
    get_logger,
    configure_logger,
    set_log_level,
    get_log_file_path,
    get_error_log_path,
)


__all__ = [
    # ==================== 文件操作工具 ====================
    # 目录操作
    'ensure_dir',
    'get_directory_size',

    # 文件信息
    'get_file_size',
    'get_file_size_formatted',
    'get_file_extension',

    # 文件验证
    'is_valid_file',
    'is_image_file',

    # 文件名处理
    'get_unique_filename',

    # 文件操作
    'copy_file',
    'move_file',
    'delete_file',

    # 目录遍历
    'get_files_in_directory',

    # 清理功能
    'cleanup_temp_files',

    # ==================== 日志工具 ====================
    'get_logger',
    'configure_logger',
    'set_log_level',
    'get_log_file_path',
    'get_error_log_path',
]