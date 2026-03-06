# -*- coding: utf-8 -*-
"""
PDF工具箱 - 程序入口

该模块是PDF工具箱应用程序的主入口点，负责：
- 初始化配置和目录
- 配置日志系统
- 创建Qt应用程序
- 显示主窗口

使用方式：
    python main.py

或作为模块运行：
    python -m pdfTools
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from config.settings import Settings
from gui import MainWindow
from gui.styles import get_stylesheet
from utils.logger import get_logger, configure_logger


def initialize_application() -> None:
    """
    初始化应用程序

    执行以下初始化步骤：
    1. 确保必要的目录存在
    2. 配置日志系统
    """
    # 确保必要的目录存在（输出目录、临时目录、日志目录）
    Settings.ensure_directories()

    # 配置日志系统
    configure_logger()


def create_application() -> QApplication:
    """
    创建Qt应用程序实例

    Returns:
        QApplication: 应用程序实例
    """
    # 创建应用程序
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName(Settings.APP_NAME)
    app.setApplicationVersion(Settings.APP_VERSION)
    app.setOrganizationName("PDF Tools")

    # 应用全局样式表
    app.setStyleSheet(get_stylesheet())

    return app


def main() -> int:
    """
    程序主入口

    该函数是应用程序的主入口点，负责：
    1. 初始化应用程序配置
    2. 创建Qt应用程序
    3. 显示主窗口
    4. 运行事件循环

    Returns:
        int: 退出码，0表示正常退出

    Example:
        >>> exit_code = main()
        >>> print(f"程序退出，退出码: {exit_code}")
    """
    # 初始化应用程序
    initialize_application()

    # 获取日志器
    logger = get_logger(__name__)

    try:
        # 记录启动日志
        logger.info(f"启动 {Settings.APP_NAME} v{Settings.APP_VERSION}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {Path.cwd()}")

        # 创建应用程序
        app = create_application()

        # 创建并显示主窗口
        window = MainWindow()
        window.show()

        logger.info("主窗口已显示，进入事件循环")

        # 运行事件循环
        exit_code = app.exec()

        # 记录退出日志
        logger.info(f"退出 {Settings.APP_NAME}，退出码: {exit_code}")

        return exit_code

    except Exception as e:
        # 记录未捕获的异常
        logger.critical(f"应用程序发生致命错误: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())