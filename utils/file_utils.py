# -*- coding: utf-8 -*-
"""
文件操作工具模块

该模块提供了常用的文件操作函数，包括：
- 目录操作（创建、清理）
- 文件信息获取（大小、扩展名）
- 文件验证（有效性、类型判断）
- 文件操作（复制、移动、删除）
- 文件名处理（唯一命名）
- 目录遍历（获取文件列表）

所有函数都使用pathlib.Path作为路径参数类型，确保跨平台兼容性。

使用方式：
    from utils.file_utils import ensure_dir, get_file_size, is_valid_file

    # 确保目录存在
    ensure_dir(Path("output"))

    # 获取文件大小
    size = get_file_size(Path("document.pdf"))

    # 检查文件有效性
    if is_valid_file(Path("image.jpg")):
        print("文件有效")
"""
import os
import shutil
import time
from pathlib import Path
from typing import List, Optional

from config.constants import IMAGE_EXTENSIONS, format_file_size
from config.settings import Settings


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建

    创建目录及其所有父目录。如果目录已存在，不会抛出异常。

    Args:
        path: 目录路径，可以是相对路径或绝对路径

    Returns:
        Path: 传入的目录路径（便于链式调用）

    Raises:
        OSError: 如果创建目录失败（如权限不足）

    Example:
        >>> from pathlib import Path
        >>> output_dir = ensure_dir(Path("output/pdf"))
        >>> output_dir.exists()
        True
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        # 重新抛出异常，提供更详细的错误信息
        raise OSError(f"创建目录失败: {path}, 错误: {e}")


def get_file_size(file_path: Path) -> int:
    """
    获取文件大小

    以字节为单位返回文件大小。如果文件不存在或不是常规文件，返回0。

    Args:
        file_path: 文件路径

    Returns:
        int: 文件大小（字节），文件不存在时返回0

    Example:
        >>> size = get_file_size(Path("document.pdf"))
        >>> print(f"文件大小: {size} 字节")
    """
    # 检查文件是否存在
    if not file_path.exists():
        return 0

    try:
        return file_path.stat().st_size
    except OSError:
        # 文件被占用或权限问题
        return 0


def get_file_size_formatted(file_path: Path) -> str:
    """
    获取格式化的文件大小

    将文件大小转换为人类可读的格式（如 "1.50 MB"）。

    Args:
        file_path: 文件路径

    Returns:
        str: 格式化的文件大小字符串，如 "1.50 MB"

    Example:
        >>> size_str = get_file_size_formatted(Path("video.mp4"))
        >>> print(size_str)  # 输出: "125.50 MB"
    """
    size = get_file_size(file_path)
    return format_file_size(size)


def is_valid_file(file_path: Path, max_size: Optional[int] = None) -> bool:
    """
    检查文件是否有效

    验证文件是否存在、是否为常规文件、大小是否在限制内。

    Args:
        file_path: 文件路径
        max_size: 最大文件大小（字节），None表示使用默认值（Settings.MAX_FILE_SIZE）

    Returns:
        bool: 如果文件有效返回True，否则返回False

        文件有效的条件：
        1. 文件存在
        2. 是常规文件（不是目录或链接）
        3. 文件大小不超过限制

    Example:
        >>> if is_valid_file(Path("document.pdf")):
        ...     print("文件有效")
        >>> if is_valid_file(Path("large.pdf"), max_size=10*1024*1024):
        ...     print("文件大小在10MB以内")
    """
    # 检查文件是否存在
    if not file_path.exists():
        return False

    # 检查是否为常规文件
    if not file_path.is_file():
        return False

    # 使用默认最大大小
    if max_size is None:
        max_size = Settings.MAX_FILE_SIZE

    # 检查文件大小
    if get_file_size(file_path) > max_size:
        return False

    return True


def get_file_extension(file_path: Path) -> str:
    """
    获取文件扩展名（不含点号）

    返回文件扩展名的小写形式，不含前导点号。

    Args:
        file_path: 文件路径

    Returns:
        str: 文件扩展名（小写），如果文件没有扩展名返回空字符串

    Example:
        >>> get_file_extension(Path("document.PDF"))
        'pdf'
        >>> get_file_extension(Path("README"))
        ''
    """
    # 获取扩展名并转换为小写，去掉前导点号
    return file_path.suffix.lower().lstrip('.')


def is_image_file(file_path: Path) -> bool:
    """
    检查是否为图片文件

    根据文件扩展名判断文件是否为支持的图片格式。

    Args:
        file_path: 文件路径

    Returns:
        bool: 如果是支持的图片格式返回True，否则返回False

    Note:
        支持的图片格式定义在 config.constants.IMAGE_EXTENSIONS 中

    Example:
        >>> is_image_file(Path("photo.jpg"))
        True
        >>> is_image_file(Path("document.pdf"))
        False
    """
    ext = get_file_extension(file_path)
    return ext in IMAGE_EXTENSIONS


def get_unique_filename(directory: Path, filename: str) -> str:
    """
    获取唯一的文件名

    如果目标目录中已存在同名文件，自动添加数字后缀以避免冲突。
    例如：document.pdf -> document_1.pdf -> document_2.pdf

    Args:
        directory: 目标目录路径
        filename: 原始文件名

    Returns:
        str: 唯一的文件名（不含路径）

    Example:
        >>> # 假设目录中已有 document.pdf
        >>> get_unique_filename(Path("output"), "document.pdf")
        'document_1.pdf'
    """
    file_path = directory / filename

    # 如果文件不存在，直接返回原文件名
    if not file_path.exists():
        return filename

    # 分离文件名和扩展名
    stem = file_path.stem      # 文件名（不含扩展名）
    suffix = file_path.suffix  # 扩展名（含点号）

    # 添加数字后缀直到找到唯一的文件名
    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = directory / new_filename

        if not new_path.exists():
            return new_filename

        counter += 1

        # 防止无限循环（极端情况）
        if counter > 10000:
            raise ValueError(f"无法生成唯一文件名: {filename}")


def cleanup_temp_files(directory: Optional[Path] = None, max_age_days: int = 7) -> int:
    """
    清理临时文件

    删除指定目录中超过一定天数的文件。
    注意：该函数只删除文件，不删除目录。

    Args:
        directory: 要清理的目录路径，None表示使用默认临时目录（Settings.TEMP_DIR）
        max_age_days: 文件最大保留天数，超过此天数的文件将被删除

    Returns:
        int: 删除的文件数量

    Example:
        >>> deleted_count = cleanup_temp_files(max_age_days=3)
        >>> print(f"删除了 {deleted_count} 个临时文件")
    """
    # 使用默认临时目录
    if directory is None:
        directory = Settings.TEMP_DIR

    # 检查目录是否存在
    if not directory.exists():
        return 0

    # 计算截止时间
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60  # 天数转秒数
    deleted_count = 0

    try:
        # 遍历目录中的所有项
        for item in directory.iterdir():
            # 只处理文件，不处理目录
            if item.is_file():
                # 获取文件修改时间
                file_mtime = item.stat().st_mtime

                # 如果文件超过最大年龄，删除它
                if current_time - file_mtime > max_age_seconds:
                    try:
                        item.unlink()
                        deleted_count += 1
                    except OSError:
                        # 文件可能被占用，跳过
                        pass
    except OSError:
        # 目录访问失败
        pass

    return deleted_count


def copy_file(source: Path, destination: Path, overwrite: bool = False) -> bool:
    """
    复制文件

    将源文件复制到目标位置，保留文件元数据（修改时间等）。

    Args:
        source: 源文件路径
        destination: 目标文件路径
        overwrite: 是否覆盖已存在的目标文件，默认False

    Returns:
        bool: 如果成功复制返回True，否则返回False

    Note:
        - 会自动创建目标目录
        - 使用shutil.copy2保留文件元数据

    Example:
        >>> success = copy_file(
        ...     Path("source/document.pdf"),
        ...     Path("backup/document.pdf"),
        ...     overwrite=True
        ... )
    """
    # 检查源文件是否存在
    if not source.exists():
        return False

    # 检查目标文件是否存在
    if destination.exists() and not overwrite:
        return False

    try:
        # 确保目标目录存在
        ensure_dir(destination.parent)

        # 复制文件（保留元数据）
        shutil.copy2(source, destination)
        return True

    except OSError:
        return False


def move_file(source: Path, destination: Path, overwrite: bool = False) -> bool:
    """
    移动文件

    将源文件移动到目标位置。

    Args:
        source: 源文件路径
        destination: 目标文件路径
        overwrite: 是否覆盖已存在的目标文件，默认False

    Returns:
        bool: 如果成功移动返回True，否则返回False

    Note:
        会自动创建目标目录

    Example:
        >>> success = move_file(
        ...     Path("temp/file.pdf"),
        ...     Path("archive/file.pdf")
        ... )
    """
    # 检查源文件是否存在
    if not source.exists():
        return False

    # 检查目标文件是否存在
    if destination.exists() and not overwrite:
        return False

    try:
        # 确保目标目录存在
        ensure_dir(destination.parent)

        # 移动文件
        shutil.move(str(source), str(destination))
        return True

    except OSError:
        return False


def delete_file(file_path: Path) -> bool:
    """
    删除文件

    安全地删除指定文件。

    Args:
        file_path: 要删除的文件路径

    Returns:
        bool: 如果成功删除返回True，文件不存在或删除失败返回False

    Example:
        >>> if delete_file(Path("temp/file.pdf")):
        ...     print("文件已删除")
    """
    try:
        # 检查文件是否存在且为常规文件
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
    except OSError:
        return False


def get_files_in_directory(
    directory: Path,
    extensions: Optional[List[str]] = None,
    recursive: bool = False
) -> List[Path]:
    """
    获取目录中的文件列表

    返回目录中的所有文件路径，可选择按扩展名过滤和递归搜索。

    Args:
        directory: 目录路径
        extensions: 文件扩展名过滤列表（如 ['.pdf', '.doc']），
                   None表示不过滤，返回所有文件
        recursive: 是否递归搜索子目录，默认False

    Returns:
        List[Path]: 文件路径列表

    Example:
        # 获取目录中所有PDF文件
        >>> pdf_files = get_files_in_directory(
        ...     Path("documents"),
        ...     extensions=['.pdf']
        ... )

        # 递归获取所有文件
        >>> all_files = get_files_in_directory(
        ...     Path("project"),
        ...     recursive=True
        ... )
    """
    # 检查目录是否存在
    if not directory.exists() or not directory.is_dir():
        return []

    files = []

    # 确定搜索模式
    if recursive:
        pattern = '**/*'  # 递归搜索
    else:
        pattern = '*'      # 仅当前目录

    # 标准化扩展名列表（确保小写且含点号）
    if extensions:
        extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                      for ext in extensions]

    # 遍历目录
    try:
        for item in directory.glob(pattern):
            # 只处理文件
            if item.is_file():
                # 如果有扩展名过滤，检查是否符合
                if extensions is None or item.suffix.lower() in extensions:
                    files.append(item)
    except OSError:
        pass

    return files


def get_directory_size(directory: Path) -> int:
    """
    获取目录大小

    计算目录中所有文件的总大小（字节）。

    Args:
        directory: 目录路径

    Returns:
        int: 目录总大小（字节），目录不存在返回0

    Example:
        >>> size = get_directory_size(Path("output"))
        >>> print(f"目录大小: {format_file_size(size)}")
    """
    if not directory.exists() or not directory.is_dir():
        return 0

    total_size = 0

    try:
        for item in directory.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass

    return total_size