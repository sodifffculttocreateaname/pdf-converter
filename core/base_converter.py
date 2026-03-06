# -*- coding: utf-8 -*-
"""
转换器基类模块

该模块定义了所有转换器必须遵循的统一接口和数据结构，包括：
- ConversionResult: 转换结果数据类
- ConversionProgress: 转换进度数据类
- BaseConverter: 转换器抽象基类

所有具体的转换器模块（如图片转PDF、PDF转图片等）都必须继承BaseConverter类，
并实现其抽象方法。

使用方式：
    from core.base_converter import BaseConverter, ConversionResult, ConversionProgress

    class MyConverter(BaseConverter):
        name = "我的转换器"
        description = "转换器描述"
        supported_input_formats = ["txt"]
        supported_output_formats = ["pdf"]

        def convert(self, input_files, output_dir, **kwargs):
            # 实现转换逻辑
            pass

        def validate_input(self, file_path):
            # 实现输入验证
            pass
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from config.constants import ConversionStatus


@dataclass
class ConversionResult:
    """
    转换结果数据类

    用于存储单个文件的转换结果信息，包括输入输出路径、状态和消息。

    Attributes:
        input_file: 输入文件路径，必填
        output_file: 输出文件路径，转换成功时设置
        status: 转换状态，默认为PENDING（待处理）
        message: 结果消息，用于显示给用户
        error: 错误信息，转换失败时设置

    Example:
        >>> from pathlib import Path
        >>> result = ConversionResult(
        ...     input_file=Path("input.pdf"),
        ...     output_file=Path("output.jpg"),
        ...     status=ConversionStatus.COMPLETED,
        ...     message="转换成功"
        ... )
        >>> result.success()
        True
    """
    # 输入文件路径（必填）
    input_file: Path

    # 输出文件路径（转换成功时设置）
    output_file: Optional[Path] = None

    # 转换状态
    status: ConversionStatus = ConversionStatus.PENDING

    # 结果消息
    message: str = ""

    # 错误信息（转换失败时设置）
    error: Optional[str] = None

    def success(self) -> bool:
        """
        判断转换是否成功

        Returns:
            bool: 如果状态为COMPLETED返回True，否则返回False

        Example:
            >>> result.status = ConversionStatus.COMPLETED
            >>> result.success()
            True
        """
        return self.status == ConversionStatus.COMPLETED

    def __str__(self) -> str:
        """返回结果的字符串表示"""
        status_name = self.status.name
        if self.success():
            return f"[{status_name}] {self.input_file.name} -> {self.output_file.name if self.output_file else 'N/A'}"
        else:
            return f"[{status_name}] {self.input_file.name}: {self.error or self.message}"


@dataclass
class ConversionProgress:
    """
    转换进度数据类

    用于报告转换过程中的进度信息，支持进度回调和UI更新。

    Attributes:
        current: 当前已处理的数量
        total: 总数量
        current_file: 当前正在处理的文件名
        message: 进度消息，用于显示给用户

    Properties:
        percentage: 计算进度百分比（0-100）

    Example:
        >>> progress = ConversionProgress(
        ...     current=5,
        ...     total=10,
        ...     current_file="document.pdf",
        ...     message="正在处理..."
        ... )
        >>> progress.percentage
        50.0
    """
    # 当前已处理的数量
    current: int = 0

    # 总数量
    total: int = 0

    # 当前正在处理的文件名
    current_file: str = ""

    # 进度消息
    message: str = ""

    @property
    def percentage(self) -> float:
        """
        计算进度百分比

        Returns:
            float: 进度百分比（0-100），如果total为0则返回0

        Example:
            >>> progress = ConversionProgress(current=3, total=10)
            >>> progress.percentage
            30.0
        """
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100

    def __str__(self) -> str:
        """返回进度的字符串表示"""
        return f"[{self.current}/{self.total}] {self.percentage:.1f}% - {self.message}"


class BaseConverter(ABC):
    """
    转换器抽象基类

    所有转换器模块必须继承此类并实现相关抽象方法。
    该类提供了转换器的通用接口和公共功能。

    子类必须实现以下内容：
        - name: 类属性，模块名称
        - description: 类属性，模块描述
        - supported_input_formats: 类属性，支持的输入格式列表
        - supported_output_formats: 类属性，支持的输出格式列表
        - convert(): 抽象方法，执行转换逻辑
        - validate_input(): 抽象方法，验证输入文件

    类属性:
        name: 转换器名称，显示在GUI功能列表中
        description: 转换器描述，说明功能
        supported_input_formats: 支持的输入文件格式列表
        supported_output_formats: 支持的输出文件格式列表

    Example:
        >>> class ImageToPdfConverter(BaseConverter):
        ...     name = "图片转PDF"
        ...     description = "将图片文件转换为PDF文档"
        ...     supported_input_formats = ["jpg", "png"]
        ...     supported_output_formats = ["pdf"]
        ...
        ...     def convert(self, input_files, output_dir, **kwargs):
        ...         results = []
        ...         for input_file in input_files:
        ...             # 转换逻辑
        ...             result = ConversionResult(input_file=input_file)
        ...             results.append(result)
        ...         return results
        ...
        ...     def validate_input(self, file_path):
        ...         return file_path.suffix.lower() in ['.jpg', '.png']
    """

    # ==================== 类属性（子类必须重写）====================
    # 转换器名称，显示在GUI功能列表中
    name: str = "基础转换器"

    # 转换器描述，说明功能
    description: str = "基础转换器描述"

    # 支持的输入文件格式列表（不含点号的小写扩展名）
    supported_input_formats: List[str] = []

    # 支持的输出文件格式列表（不含点号的小写扩展名）
    supported_output_formats: List[str] = []

    def __init__(self):
        """
        初始化转换器

        设置进度回调和取消标志的初始值。
        子类如果重写__init__方法，必须调用super().__init__()。
        """
        # 进度回调函数，用于报告转换进度
        self._progress_callback: Optional[Callable[[ConversionProgress], None]] = None

        # 取消标志，用于中断正在进行的转换
        self._is_cancelled: bool = False

    # ==================== 公共方法 ====================
    def set_progress_callback(self, callback: Callable[[ConversionProgress], None]) -> None:
        """
        设置进度回调函数

        回调函数会在转换过程中被调用，用于报告进度更新。

        Args:
            callback: 回调函数，接收ConversionProgress对象作为参数

        Example:
            >>> def on_progress(progress):
            ...     print(f"进度: {progress.percentage:.1f}%")
            >>> converter.set_progress_callback(on_progress)
        """
        self._progress_callback = callback

    def cancel(self) -> None:
        """
        取消当前操作

        设置取消标志，正在执行的convert方法应该定期检查此标志，
        并在标志为True时停止处理并返回。

        Example:
            >>> converter.cancel()
            >>> converter._check_cancelled()
            True
        """
        self._is_cancelled = True

    def reset(self) -> None:
        """
        重置转换器状态

        将取消标志重置为False，使转换器可以重新开始新的转换任务。
        通常在开始新的转换之前调用。

        Example:
            >>> converter.cancel()
            >>> converter.reset()
            >>> converter._check_cancelled()
            False
        """
        self._is_cancelled = False

    # ==================== 抽象方法（子类必须实现）====================
    @abstractmethod
    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行转换（子类必须实现）

        这是转换器的核心方法，负责将输入文件转换为指定格式。
        实现时应该：
        1. 遍历输入文件列表
        2. 验证每个输入文件
        3. 执行转换逻辑
        4. 定期检查取消标志
        5. 报告进度
        6. 返回转换结果列表

        Args:
            input_files: 输入文件路径列表
            output_dir: 输出目录路径
            **kwargs: 额外参数，如dpi、quality等

        Returns:
            List[ConversionResult]: 转换结果列表，每个输入文件对应一个结果

        Example:
            >>> results = converter.convert([Path("a.jpg")], Path("output"))
            >>> len(results)
            1
        """
        pass

    @abstractmethod
    def validate_input(self, file_path: Path) -> bool:
        """
        验证输入文件是否有效（子类必须实现）

        检查输入文件是否符合转换器的要求，包括：
        - 文件是否存在
        - 文件格式是否支持
        - 文件是否可读

        Args:
            file_path: 要验证的文件路径

        Returns:
            bool: 如果文件有效返回True，否则返回False

        Example:
            >>> converter.validate_input(Path("test.jpg"))
            True
            >>> converter.validate_input(Path("nonexistent.pdf"))
            False
        """
        pass

    # ==================== 保护方法（供子类使用）====================
    def _report_progress(self, progress: ConversionProgress) -> None:
        """
        报告进度（供子类调用）

        调用进度回调函数，报告当前转换进度。
        子类在convert方法中应该定期调用此方法。

        Args:
            progress: 进度对象

        Example:
            >>> progress = ConversionProgress(current=1, total=10, message="处理中")
            >>> self._report_progress(progress)
        """
        if self._progress_callback:
            self._progress_callback(progress)

    def _check_cancelled(self) -> bool:
        """
        检查是否已取消（供子类调用）

        返回当前取消标志的值。
        子类在convert方法中应该定期检查此标志。

        Returns:
            bool: 如果已取消返回True，否则返回False

        Example:
            >>> if self._check_cancelled():
            ...     return results  # 提前返回
        """
        return self._is_cancelled

    # ==================== 工具方法 ====================
    def get_output_filename(self, input_file: Path, output_format: str) -> str:
        """
        根据输入文件名生成输出文件名

        保持输入文件的主文件名，只更改扩展名。

        Args:
            input_file: 输入文件路径
            output_format: 输出格式（不含点号的扩展名）

        Returns:
            str: 输出文件名

        Example:
            >>> converter.get_output_filename(Path("document.pdf"), "jpg")
            'document.jpg'
        """
        return f"{input_file.stem}.{output_format}"

    def supports_format(self, file_path: Path) -> bool:
        """
        检查是否支持该文件格式

        根据文件扩展名判断转换器是否支持该文件。

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果支持返回True，否则返回False

        Example:
            >>> converter.supports_format(Path("image.jpg"))
            True
            >>> converter.supports_format(Path("document.pdf"))
            False
        """
        # 获取文件扩展名（不含点号，小写）
        extension = file_path.suffix.lower().lstrip('.')

        # 检查是否在支持的格式列表中
        return extension in [fmt.lower() for fmt in self.supported_input_formats]

    # ==================== 魔术方法 ====================
    def __str__(self) -> str:
        """返回转换器的字符串表示"""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """返回转换器的调试表示"""
        return f"<{self.__class__.__name__}(name='{self.name}')>"