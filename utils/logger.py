# -*- coding: utf-8 -*-
"""
日志工具模块

该模块提供了统一的日志配置和获取接口，基于loguru实现。

功能特点：
- 控制台彩色输出
- 文件日志自动轮转
- 错误日志单独记录
- 日志自动压缩
- 线程安全

日志级别：
- DEBUG: 调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

使用方式：
    from utils.logger import get_logger

    # 获取当前模块的日志器
    logger = get_logger(__name__)

    # 记录日志
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")

    # 记录异常信息
    try:
        # ... 代码 ...
    except Exception as e:
        logger.exception("发生异常")  # 自动记录堆栈跟踪
"""
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import Settings


# ==================== 模块级变量 ====================
# 移除loguru默认的处理器，使用我们自己的配置
logger.remove()

# 全局标志，表示日志是否已配置
# 避免重复配置导致的日志重复输出
_configured: bool = False


def configure_logger(
    log_level: Optional[str] = None,
    log_dir: Optional[Path] = None
) -> None:
    """
    配置日志系统

    配置控制台和文件日志输出。该函数只会执行一次，
    后续调用会被忽略。如需重新配置，请先调用set_log_level()。

    Args:
        log_level: 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
                   None表示使用Settings中的默认值
        log_dir: 日志文件存储目录
                  None表示使用Settings中的默认值

    日志输出：
        - 控制台：彩色输出，显示时间、级别、模块、函数、行号和消息
        - 常规日志文件：记录所有级别的日志，按天轮转，自动压缩
        - 错误日志文件：仅记录ERROR及以上级别的日志

    Example:
        >>> # 使用默认配置
        >>> configure_logger()

        >>> # 自定义配置
        >>> configure_logger(log_level="DEBUG", log_dir=Path("logs"))
    """
    global _configured

    # 检查是否已配置，避免重复配置
    if _configured:
        logger.debug("日志系统已配置，跳过重复配置")
        return

    # 使用默认配置值
    if log_level is None:
        log_level = Settings.LOG_LEVEL

    if log_dir is None:
        log_dir = Settings.LOG_DIR

    # 确保日志级别有效
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level.upper() not in valid_levels:
        log_level = 'INFO'  # 使用安全的默认值

    # 确保日志目录存在
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # 如果无法创建日志目录，只使用控制台输出
        print(f"警告: 无法创建日志目录 {log_dir}: {e}")
        log_dir = None

    # ==================== 定义日志格式 ====================
    # 控制台输出格式（带颜色）
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 文件输出格式（不带颜色）
    file_format = (
        "{time: YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # ==================== 添加控制台处理器 ====================
    try:
        logger.add(
            sys.stdout,
            format=console_format,
            level=log_level,
            colorize=True,       # 启用颜色输出
            enqueue=True,        # 启用线程安全队列
            backtrace=True,      # 显示完整的回溯信息
            diagnose=True,       # 显示变量值
        )
    except Exception as e:
        print(f"警告: 无法配置控制台日志: {e}")

    # ==================== 添加文件处理器 ====================
    if log_dir is not None:
        # 常规日志文件
        try:
            logger.add(
                log_dir / "pdf_tools_{time:YYYY-MM-DD}.log",
                format=file_format,
                level=log_level,
                rotation=Settings.LOG_MAX_SIZE,    # 文件大小达到限制时轮转
                retention=Settings.LOG_RETENTION,   # 旧日志保留时间
                compression="zip",                   # 压缩旧日志
                encoding="utf-8",
                enqueue=True,                        # 线程安全
                backtrace=True,
                diagnose=True,
            )
        except Exception as e:
            print(f"警告: 无法配置文件日志: {e}")

        # 错误日志文件（仅记录错误和严重错误）
        try:
            logger.add(
                log_dir / "error_{time:YYYY-MM-DD}.log",
                format=file_format,
                level="ERROR",                       # 仅记录ERROR及以上
                rotation=Settings.LOG_MAX_SIZE,
                retention=Settings.LOG_RETENTION,
                compression="zip",
                encoding="utf-8",
                enqueue=True,
                backtrace=True,                      # 显示完整回溯
                diagnose=True,                       # 显示变量值
            )
        except Exception as e:
            print(f"警告: 无法配置错误日志: {e}")

    # 标记为已配置
    _configured = True

    # 记录初始化日志
    logger.info(
        f"日志系统初始化完成 | "
        f"级别: {log_level} | "
        f"目录: {log_dir}"
    )


def get_logger(name: Optional[str] = None):
    """
    获取日志器

    返回配置好的日志器实例。如果日志系统尚未配置，会自动配置。

    Args:
        name: 模块名称，通常使用 __name__
              如果提供，会在日志中显示模块名

    Returns:
        Logger: 配置好的日志器实例

    Example:
        >>> # 获取当前模块的日志器
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条日志")

        >>> # 获取默认日志器
        >>> logger = get_logger()
        >>> logger.info("这是一条日志")
    """
    global _configured

    # 如果未配置，先配置日志系统
    if not _configured:
        try:
            configure_logger()
        except Exception as e:
            # 配置失败时打印警告，但不影响程序运行
            print(f"警告: 日志系统配置失败: {e}")

    # 如果提供了名称，返回绑定了名称的日志器
    if name:
        return logger.bind(name=name)

    return logger


def set_log_level(level: str) -> None:
    """
    设置日志级别

    重新配置日志系统，使用新的日志级别。
    注意：这会重新配置所有日志处理器。

    Args:
        level: 日志级别，可选值：
               - DEBUG: 调试信息（最详细）
               - INFO: 一般信息
               - WARNING: 警告信息
               - ERROR: 错误信息
               - CRITICAL: 严重错误（最不详细）

    Example:
        >>> set_log_level("DEBUG")  # 显示所有日志
        >>> set_log_level("WARNING")  # 只显示警告和错误
    """
    global _configured

    # 验证日志级别
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level = level.upper()

    if level not in valid_levels:
        logger.warning(f"无效的日志级别: {level}, 使用默认值 INFO")
        level = 'INFO'

    # 移除所有现有处理器
    logger.remove()

    # 标记为未配置，以便重新配置
    _configured = False

    # 更新设置
    Settings.LOG_LEVEL = level

    # 重新配置日志系统
    configure_logger()

    logger.info(f"日志级别已更改为: {level}")


def get_log_file_path() -> Optional[Path]:
    """
    获取当前日志文件路径

    返回今天的主日志文件路径。

    Returns:
        Path: 日志文件路径，如果日志目录不存在返回None

    Example:
        >>> path = get_log_file_path()
        >>> if path:
        ...     print(f"日志文件: {path}")
    """
    log_dir = Settings.LOG_DIR
    if not log_dir.exists():
        return None

    # 返回今天的日志文件路径
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"pdf_tools_{today}.log"


def get_error_log_path() -> Optional[Path]:
    """
    获取当前错误日志文件路径

    返回今天的错误日志文件路径。

    Returns:
        Path: 错误日志文件路径，如果日志目录不存在返回None

    Example:
        >>> path = get_error_log_path()
        >>> if path:
        ...     print(f"错误日志文件: {path}")
    """
    log_dir = Settings.LOG_DIR
    if not log_dir.exists():
        return None

    # 返回今天的错误日志文件路径
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"error_{today}.log"


# ==================== 模块初始化 ====================
# 在模块加载时自动配置日志系统
try:
    configure_logger()
except Exception as e:
    # 配置失败时打印警告，但不影响程序运行
    print(f"警告: 日志系统自动配置失败: {e}")