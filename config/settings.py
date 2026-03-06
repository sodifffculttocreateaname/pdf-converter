# -*- coding: utf-8 -*-
"""
全局配置模块

该模块定义了应用程序的全局配置项，包括：
- 应用程序基本信息
- 文件路径配置
- 日志配置
- PDF/图片处理参数
- 网页转换配置

使用方式：
    from config.settings import Settings
    Settings.ensure_directories()  # 确保必要目录存在
    output_dir = Settings.DEFAULT_OUTPUT_DIR
"""
import os
from pathlib import Path


class Settings:
    """
    全局配置类

    该类使用类属性存储所有配置项，避免实例化开销。
    所有配置项均为类属性，可直接通过类名访问。

    Attributes:
        APP_NAME: 应用程序名称
        APP_VERSION: 应用程序版本号
        DEFAULT_OUTPUT_DIR: 默认输出目录路径
        MAX_FILE_SIZE: 支持的最大文件大小（字节）
        MAX_CONCURRENT_TASKS: 最大并发任务数
        TEMP_DIR: 临时文件目录路径
        LOG_DIR: 日志文件目录路径
        LOG_LEVEL: 日志级别
        LOG_MAX_SIZE: 单个日志文件最大大小（字节）
        LOG_RETENTION: 日志保留时间
        PDF_DEFAULT_DPI: PDF默认DPI值
        PDF_COMPRESSION_QUALITY: PDF压缩质量（1-100）
        IMAGE_DEFAULT_FORMAT: 默认图片格式
        IMAGE_DEFAULT_DPI: 默认图片DPI值
        WEB_PAGE_LOAD_TIMEOUT: 网页加载超时时间（毫秒）

    Example:
        >>> Settings.APP_NAME
        'PDF工具箱'
        >>> Settings.DEFAULT_OUTPUT_DIR
        PosixPath('/home/user/Documents/PDF工具箱输出')
    """

    # ==================== 应用信息配置 ====================
    # 应用程序名称，显示在标题栏和关于对话框中
    APP_NAME: str = "PDF工具箱"

    # 应用程序版本号，格式为主版本.次版本.修订号
    APP_VERSION: str = "1.0.0"

    # ==================== 文件路径配置 ====================
    # 默认输出目录，转换后的文件将保存在此目录
    # 路径: 用户文档目录/PDF工具箱输出
    DEFAULT_OUTPUT_DIR: Path = Path.home() / "Documents" / "PDF工具箱输出"

    # 支持的最大文件大小，单位：字节
    # 默认100MB，超过此大小的文件将拒绝处理
    # 计算: 100 * 1024 * 1024 = 104857600 字节
    MAX_FILE_SIZE: int = 100 * 1024 * 1024

    # 最大并发任务数
    # 控制同时执行的转换任务数量，避免系统资源耗尽
    MAX_CONCURRENT_TASKS: int = 3

    # 临时文件目录
    # 用于存储转换过程中的临时文件，程序退出时可能不会自动清理
    # 路径: 用户主目录/.pdf_tools/temp
    TEMP_DIR: Path = Path.home() / ".pdf_tools" / "temp"

    # ==================== 日志配置 ====================
    # 日志文件目录
    # 路径: 程序根目录/logs
    LOG_DIR: Path = Path(__file__).parent.parent / "logs"

    # 日志级别
    # 可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = "INFO"

    # 单个日志文件最大大小，单位：字节
    # 默认10MB，超过此大小将自动轮转
    LOG_MAX_SIZE: int = 10 * 1024 * 1024

    # 日志保留时间
    # 超过此时间的日志文件将被自动删除
    LOG_RETENTION: str = "7 days"

    # ==================== PDF处理配置 ====================
    # PDF默认DPI值
    # 用于PDF转图片和图片转PDF时的分辨率设置
    # 常用值: 72(屏幕), 150(标准), 300(高清)
    PDF_DEFAULT_DPI: int = 150

    # PDF压缩质量
    # 范围: 1-100，值越大质量越高，文件越大
    # 推荐: 85(平衡质量和大小)
    PDF_COMPRESSION_QUALITY: int = 85

    # ==================== 图片处理配置 ====================
    # 默认图片格式
    # PDF转图片时的默认输出格式
    IMAGE_DEFAULT_FORMAT: str = "PNG"

    # 默认图片DPI值
    # 图片处理时的默认分辨率
    IMAGE_DEFAULT_DPI: int = 150

    # ==================== 网页转换配置 ====================
    # 网页加载超时时间，单位：毫秒
    # 网页转PDF时等待页面加载的最大时间
    WEB_PAGE_LOAD_TIMEOUT: int = 30000  # 30秒

    @classmethod
    def ensure_directories(cls) -> None:
        """
        确保必要的目录存在

        在应用程序启动时调用此方法，创建以下目录：
        - DEFAULT_OUTPUT_DIR: 默认输出目录
        - TEMP_DIR: 临时文件目录
        - LOG_DIR: 日志文件目录

        如果目录已存在，此方法不会产生任何副作用。

        Example:
            >>> Settings.ensure_directories()
            # 目录已创建或已存在
        """
        # 创建默认输出目录
        cls.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 创建临时文件目录
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # 创建日志目录
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_log_config(cls) -> dict:
        """
        获取日志配置字典

        返回用于配置日志系统的参数字典。

        Returns:
            dict: 包含日志配置的字典，包括：
                - log_dir: 日志目录路径
                - log_level: 日志级别
                - log_max_size: 最大日志文件大小
                - log_retention: 日志保留时间

        Example:
            >>> config = Settings.get_log_config()
            >>> print(config['log_level'])
            'INFO'
        """
        return {
            'log_dir': cls.LOG_DIR,
            'log_level': cls.LOG_LEVEL,
            'log_max_size': cls.LOG_MAX_SIZE,
            'log_retention': cls.LOG_RETENTION,
        }