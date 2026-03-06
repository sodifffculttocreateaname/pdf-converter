# -*- coding: utf-8 -*-
"""
任务调度器模块

该模块实现了任务调度器，负责：
- 管理转换器注册表
- 维护任务队列
- 在后台线程中执行任务
- 提供进度和完成回调
- 支持任务取消

调度器使用单例模式，确保整个应用程序只有一个调度器实例。

使用方式：
    from core.dispatcher import TaskDispatcher

    # 获取调度器实例
    dispatcher = TaskDispatcher()

    # 注册转换器
    dispatcher.register_converter(my_converter)

    # 添加任务
    dispatcher.add_task("图片转PDF", [Path("image.jpg")], Path("output"))

    # 设置回调
    dispatcher.set_progress_callback(on_progress)
    dispatcher.set_completion_callback(on_complete)

    # 启动任务处理
    dispatcher.start()
"""
import threading
from collections import deque
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type

from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from config.constants import ConversionStatus
from utils.logger import get_logger


# 获取模块日志器
logger = get_logger(__name__)


class TaskDispatcher:
    """
    任务调度器单例类

    负责管理转换任务队列和分发任务到对应的转换器。
    使用单例模式确保全局只有一个调度器实例。

    该类是线程安全的，可以在多线程环境中使用。

    Attributes:
        _instance: 单例实例
        _lock: 线程锁，保证单例创建的线程安全

    Example:
        >>> dispatcher = TaskDispatcher()
        >>> dispatcher.register_converter(ImageToPdfConverter())
        >>> dispatcher.add_task("图片转PDF", [Path("a.jpg")], Path("output"))
        True
        >>> dispatcher.start()
        True
    """

    # 单例实例
    _instance: Optional['TaskDispatcher'] = None

    # 线程锁，保证单例创建的线程安全
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> 'TaskDispatcher':
        """
        创建或返回单例实例

        使用双重检查锁定模式确保线程安全。

        Returns:
            TaskDispatcher: 调度器单例实例
        """
        # 第一次检查，避免不必要的锁竞争
        if cls._instance is None:
            with cls._lock:
                # 第二次检查，确保只创建一个实例
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 标记为未初始化
                    cls._instance._initialized = False
                    logger.debug("创建TaskDispatcher单例实例")
        return cls._instance

    def __init__(self):
        """
        初始化调度器

        由于单例模式的特殊性质，需要检查初始化标志避免重复初始化。
        """
        # 检查是否已初始化，避免重复初始化
        if self._initialized:
            logger.debug("TaskDispatcher已初始化，跳过")
            return

        logger.info("开始初始化TaskDispatcher")

        # 标记为已初始化
        self._initialized: bool = True

        # 已注册的转换器字典 {转换器名称: 转换器实例}
        self._converters: Dict[str, BaseConverter] = {}

        # 任务队列，使用双端队列支持高效的两端操作
        self._task_queue: deque = deque()

        # 当前正在执行的任务
        self._current_task: Optional[dict] = None

        # 调度器运行状态标志
        self._is_running: bool = False

        # 工作线程引用
        self._worker_thread: Optional[threading.Thread] = None

        # 进度回调函数
        self._progress_callback: Optional[Callable[[ConversionProgress], None]] = None

        # 完成回调函数
        self._completion_callback: Optional[Callable[[List[ConversionResult]], None]] = None

        logger.info("TaskDispatcher初始化完成")

    # ==================== 转换器管理方法 ====================
    def register_converter(self, converter: BaseConverter) -> None:
        """
        注册转换器

        将转换器添加到注册表，使其可以被调度器使用。
        转换器名称必须唯一，重复注册会覆盖之前的转换器。

        Args:
            converter: 要注册的转换器实例

        Example:
            >>> dispatcher.register_converter(ImageToPdfConverter())
        """
        converter_name = converter.name

        if converter_name in self._converters:
            logger.warning(f"转换器'{converter_name}'已存在，将被覆盖")

        self._converters[converter_name] = converter
        logger.debug(f"注册转换器: {converter_name} -> {converter.__class__.__name__}")

    def get_converter(self, name: str) -> Optional[BaseConverter]:
        """
        获取转换器

        根据名称从注册表中获取转换器实例。

        Args:
            name: 转换器名称

        Returns:
            BaseConverter: 转换器实例，如果不存在返回None

        Example:
            >>> converter = dispatcher.get_converter("图片转PDF")
            >>> if converter:
            ...     print(converter.description)
        """
        converter = self._converters.get(name)

        if converter is None:
            logger.warning(f"未找到转换器: {name}")

        return converter

    def get_all_converters(self) -> Dict[str, BaseConverter]:
        """
        获取所有已注册的转换器

        返回转换器字典的副本，避免外部修改影响内部状态。

        Returns:
            Dict[str, BaseConverter]: 转换器名称到实例的映射字典

        Example:
            >>> converters = dispatcher.get_all_converters()
            >>> for name, converter in converters.items():
            ...     print(f"{name}: {converter.description}")
        """
        logger.debug(f"获取所有转换器，共{len(self._converters)}个")
        return self._converters.copy()

    def get_supported_formats(self, converter_name: str) -> Dict[str, List[str]]:
        """
        获取指定转换器支持的格式

        Args:
            converter_name: 转换器名称

        Returns:
            Dict[str, List[str]]: 包含以下键的字典：
                - input: 支持的输入格式列表
                - output: 支持的输出格式列表

        Example:
            >>> formats = dispatcher.get_supported_formats("图片转PDF")
            >>> print(formats['input'])
            ['jpg', 'png', 'bmp']
        """
        converter = self._converters.get(converter_name)

        if converter is None:
            logger.warning(f"获取格式失败，未找到转换器: {converter_name}")
            return {'input': [], 'output': []}

        formats = {
            'input': converter.supported_input_formats,
            'output': converter.supported_output_formats
        }

        logger.debug(f"转换器'{converter_name}'支持的格式: {formats}")
        return formats

    # ==================== 回调设置方法 ====================
    def set_progress_callback(self, callback: Callable[[ConversionProgress], None]) -> None:
        """
        设置进度回调函数

        进度回调会在转换过程中被调用，用于更新UI或记录日志。

        Args:
            callback: 回调函数，接收ConversionProgress对象

        Example:
            >>> def on_progress(progress):
            ...     print(f"进度: {progress.percentage:.1f}%")
            >>> dispatcher.set_progress_callback(on_progress)
        """
        self._progress_callback = callback
        logger.debug("已设置进度回调函数")

    def set_completion_callback(self, callback: Callable[[List[ConversionResult]], None]) -> None:
        """
        设置完成回调函数

        完成回调会在任务完成（成功或失败）后被调用。

        Args:
            callback: 回调函数，接收转换结果列表

        Example:
            >>> def on_complete(results):
            ...     success = sum(1 for r in results if r.success())
            ...     print(f"成功: {success}/{len(results)}")
            >>> dispatcher.set_completion_callback(on_complete)
        """
        self._completion_callback = callback
        logger.debug("已设置完成回调函数")

    # ==================== 任务管理方法 ====================
    def add_task(self, converter_name: str, input_files: List[Path],
                 output_dir: Path, **kwargs) -> bool:
        """
        添加任务到队列

        将转换任务添加到任务队列等待执行。
        任务会按照先进先出的顺序执行。

        Args:
            converter_name: 转换器名称
            input_files: 输入文件路径列表
            output_dir: 输出目录路径
            **kwargs: 传递给转换器的额外参数

        Returns:
            bool: 如果成功添加返回True，如果转换器不存在返回False

        Example:
            >>> success = dispatcher.add_task(
            ...     "图片转PDF",
            ...     [Path("image1.jpg"), Path("image2.png")],
            ...     Path("output"),
            ...     dpi=300
            ... )
            >>> print(success)
            True
        """
        # 验证转换器是否存在
        if converter_name not in self._converters:
            logger.error(f"添加任务失败: 未知的转换器'{converter_name}'")
            return False

        # 验证输入文件列表
        if not input_files:
            logger.error("添加任务失败: 输入文件列表为空")
            return False

        # 创建任务字典
        task = {
            'converter_name': converter_name,
            'input_files': input_files,
            'output_dir': output_dir,
            'kwargs': kwargs
        }

        # 添加到队列
        self._task_queue.append(task)

        logger.info(
            f"任务已添加到队列 | "
            f"转换器: {converter_name} | "
            f"文件数: {len(input_files)} | "
            f"输出目录: {output_dir} | "
            f"队列大小: {len(self._task_queue)}"
        )

        return True

    def start(self) -> bool:
        """
        启动任务处理

        在后台线程中开始处理任务队列中的任务。
        如果已经在运行或队列为空，则不会启动。

        Returns:
            bool: 如果成功启动返回True，否则返回False

        Example:
            >>> if dispatcher.start():
            ...     print("任务处理已启动")
        """
        # 检查是否已在运行
        if self._is_running:
            logger.warning("启动失败: 调度器已在运行中")
            return False

        # 检查队列是否为空
        if not self._task_queue:
            logger.info("启动失败: 任务队列为空")
            return False

        # 设置运行状态
        self._is_running = True

        # 创建并启动工作线程
        self._worker_thread = threading.Thread(
            target=self._process_tasks,
            daemon=True,  # 设置为守护线程，主线程退出时自动结束
            name="TaskDispatcher-Worker"
        )
        self._worker_thread.start()

        logger.info(f"任务调度器已启动 | 队列大小: {len(self._task_queue)}")
        return True

    def stop(self) -> None:
        """
        停止任务处理

        设置停止标志，并取消当前正在执行的任务。
        注意：这不会立即停止线程，而是等待当前文件处理完成后停止。

        Example:
            >>> dispatcher.stop()
        """
        logger.info("正在停止任务调度器...")

        # 设置停止标志
        self._is_running = False

        # 取消当前任务
        if self._current_task:
            converter_name = self._current_task.get('converter_name')
            if converter_name in self._converters:
                self._converters[converter_name].cancel()
                logger.debug(f"已发送取消信号给转换器: {converter_name}")

        logger.info("任务调度器已停止")

    def cancel_current(self) -> None:
        """
        取消当前任务

        仅取消当前正在执行的任务，不会停止整个调度器。

        Example:
            >>> dispatcher.cancel_current()
        """
        if self._current_task is None:
            logger.warning("取消失败: 没有正在执行的任务")
            return

        converter_name = self._current_task.get('converter_name')

        if converter_name and converter_name in self._converters:
            self._converters[converter_name].cancel()
            logger.info(f"已取消当前任务: {converter_name}")
        else:
            logger.warning(f"取消失败: 找不到转换器'{converter_name}'")

    def clear_queue(self) -> None:
        """
        清空任务队列

        清除所有等待中的任务，不会影响正在执行的任务。

        Example:
            >>> dispatcher.clear_queue()
        """
        queue_size = len(self._task_queue)
        self._task_queue.clear()
        logger.info(f"任务队列已清空 | 清除任务数: {queue_size}")

    def get_queue_size(self) -> int:
        """
        获取队列大小

        Returns:
            int: 队列中等待的任务数量

        Example:
            >>> size = dispatcher.get_queue_size()
            >>> print(f"队列中有{size}个任务等待处理")
        """
        return len(self._task_queue)

    def is_running(self) -> bool:
        """
        检查调度器是否在运行

        Returns:
            bool: 如果正在运行返回True，否则返回False

        Example:
            >>> if dispatcher.is_running():
            ...     print("调度器正在运行")
        """
        return self._is_running

    # ==================== 内部方法 ====================
    def _process_tasks(self) -> None:
        """
        处理任务队列（内部方法）

        在后台线程中运行，不断从队列中取出任务并执行。
        当队列为空或收到停止信号时退出。

        该方法不应该直接调用，由start()方法启动。
        """
        logger.info("任务处理线程已启动")

        # 循环处理任务，直到队列为空或收到停止信号
        while self._is_running and self._task_queue:
            # 从队列头部取出任务
            self._current_task = self._task_queue.popleft()

            try:
                logger.debug(f"开始处理任务: {self._current_task.get('converter_name')}")
                self._execute_task(self._current_task)

            except Exception as e:
                # 记录异常但不中断处理
                logger.error(
                    f"任务执行出错 | "
                    f"转换器: {self._current_task.get('converter_name')} | "
                    f"错误: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )

            finally:
                # 清除当前任务引用
                self._current_task = None

        # 处理完成
        self._is_running = False
        logger.info(f"任务处理线程已退出 | 剩余任务: {len(self._task_queue)}")

    def _execute_task(self, task: dict) -> None:
        """
        执行单个任务（内部方法）

        Args:
            task: 任务字典，包含以下键：
                - converter_name: 转换器名称
                - input_files: 输入文件列表
                - output_dir: 输出目录
                - kwargs: 额外参数

        该方法会：
        1. 获取对应的转换器
        2. 重置转换器状态
        3. 设置进度回调
        4. 执行转换
        5. 调用完成回调
        """
        # 提取任务参数
        converter_name = task['converter_name']
        input_files = task['input_files']
        output_dir = task['output_dir']
        kwargs = task.get('kwargs', {})

        logger.info(
            f"执行任务 | "
            f"转换器: {converter_name} | "
            f"文件数: {len(input_files)} | "
            f"输出目录: {output_dir}"
        )

        # 获取转换器
        converter = self._converters.get(converter_name)

        if converter is None:
            logger.error(f"执行任务失败: 找不到转换器'{converter_name}'")
            return

        try:
            # 重置转换器状态（清除取消标志等）
            converter.reset()
            logger.debug(f"转换器状态已重置: {converter_name}")

            # 设置进度回调
            if self._progress_callback:
                converter.set_progress_callback(self._progress_callback)
                logger.debug("进度回调已设置")

            # 执行转换
            logger.info(f"开始转换: {converter_name}")
            results = converter.convert(input_files, output_dir, **kwargs)

            # 统计结果
            success_count = sum(1 for r in results if r.success())
            fail_count = len(results) - success_count

            logger.info(
                f"任务完成 | "
                f"转换器: {converter_name} | "
                f"总数: {len(results)} | "
                f"成功: {success_count} | "
                f"失败: {fail_count}"
            )

            # 调用完成回调
            if self._completion_callback:
                try:
                    self._completion_callback(results)
                    logger.debug("完成回调已执行")
                except Exception as e:
                    logger.error(f"完成回调执行出错: {e}", exc_info=True)

        except Exception as e:
            logger.error(
                f"任务执行异常 | "
                f"转换器: {converter_name} | "
                f"错误: {type(e).__name__}: {str(e)}",
                exc_info=True
            )

    def __str__(self) -> str:
        """返回调度器的字符串表示"""
        return (
            f"TaskDispatcher("
            f"converters={len(self._converters)}, "
            f"queue={len(self._task_queue)}, "
            f"running={self._is_running})"
        )

    def __repr__(self) -> str:
        """返回调度器的调试表示"""
        return f"<TaskDispatcher at {hex(id(self))}>"