# -*- coding: utf-8 -*-
"""
图片转PDF转换器

该转换器将图片文件（JPG、PNG、BMP等）转换为PDF文档。

功能特点：
- 支持多种图片格式（JPG、PNG、BMP、TIFF、GIF、WEBP）
- 支持单图片转PDF或多图片合并为一个PDF
- 自动处理透明通道（转换为白色背景）
- 可设置DPI和压缩质量

依赖：
- Pillow: 图片处理库

使用方式：
    from converters.image_to_pdf import ImageToPdfConverter

    converter = ImageToPdfConverter()
    converter.set_dpi(300)
    converter.set_quality(90)
    results = converter.convert([Path("image.jpg")], Path("output"))
"""
from pathlib import Path
from typing import List

from PIL import Image

from config.constants import ConversionStatus, IMAGE_EXTENSIONS
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir, get_file_extension, get_unique_filename
from utils.logger import get_logger


# 获取模块日志器
logger = get_logger(__name__)


class ImageToPdfConverter(BaseConverter):
    """
    图片转PDF转换器

    将图片文件转换为PDF文档，支持单图片转换和多图片合并。

    支持的输入格式：
        - JPG/JPEG
        - PNG
        - BMP
        - TIFF
        - GIF
        - WEBP

    支持的输出格式：
        - PDF

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表

    Example:
        >>> converter = ImageToPdfConverter()
        >>> converter.set_dpi(300)
        >>> results = converter.convert(
        ...     [Path("photo.jpg"), Path("picture.png")],
        ...     Path("output"),
        ...     merge=True  # 合并为一个PDF
        ... )
    """

    # 转换器名称（显示在功能列表中）
    name: str = "图片转PDF"

    # 转换器描述
    description: str = "将图片文件转换为PDF文档"

    # 支持的输入格式
    supported_input_formats: List[str] = IMAGE_EXTENSIONS

    # 支持的输出格式
    supported_output_formats: List[str] = ["pdf"]

    def __init__(self):
        """
        初始化图片转PDF转换器

        设置默认的DPI和质量参数。
        """
        super().__init__()

        # DPI设置（影响PDF的分辨率）
        self._dpi: int = 150

        # 压缩质量（1-100）
        self._quality: int = 85

        logger.debug(f"ImageToPdfConverter初始化完成 | DPI: {self._dpi}, 质量: {self._quality}")

    # ==================== 公共方法 ====================
    def set_dpi(self, dpi: int) -> None:
        """
        设置输出PDF的DPI

        DPI影响PDF的分辨率，值越大图像越清晰但文件越大。
        常用值：72（屏幕）、150（标准）、300（高清）。

        Args:
            dpi: DPI值，范围72-600

        Example:
            >>> converter.set_dpi(300)
        """
        # 限制DPI范围
        self._dpi = max(72, min(600, dpi))
        logger.debug(f"DPI已设置: {self._dpi}")

    def set_quality(self, quality: int) -> None:
        """
        设置压缩质量

        质量越高图像越清晰但文件越大。

        Args:
            quality: 质量值，范围1-100

        Example:
            >>> converter.set_quality(90)
        """
        # 限制质量范围
        self._quality = max(1, min(100, quality))
        logger.debug(f"压缩质量已设置: {self._quality}")

    # ==================== 实现基类抽象方法 ====================
    def convert(
        self,
        input_files: List[Path],
        output_dir: Path,
        **kwargs
    ) -> List[ConversionResult]:
        """
        执行图片转PDF转换

        将输入的图片文件转换为PDF文档。可以通过merge参数控制
        是将所有图片合并为一个PDF还是每张图片单独生成PDF。

        Args:
            input_files: 输入图片文件路径列表
            output_dir: 输出目录路径
            **kwargs: 额外参数
                - dpi: DPI设置，覆盖默认值
                - quality: 压缩质量，覆盖默认值
                - merge: 是否合并为一个PDF，默认False

        Returns:
            List[ConversionResult]: 转换结果列表

        Example:
            >>> results = converter.convert(
            ...     [Path("1.jpg"), Path("2.png")],
            ...     Path("output"),
            ...     merge=True
            ... )
        """
        results: List[ConversionResult] = []

        # 应用参数
        dpi = kwargs.get('dpi', self._dpi)
        quality = kwargs.get('quality', self._quality)
        merge = kwargs.get('merge', False)

        logger.info(
            f"开始图片转PDF转换 | "
            f"文件数: {len(input_files)} | "
            f"DPI: {dpi} | "
            f"质量: {quality} | "
            f"合并: {merge}"
        )

        # 确保输出目录存在
        ensure_dir(output_dir)

        total_files = len(input_files)
        processed = 0

        try:
            if merge and total_files > 1:
                # 合并所有图片到一个PDF
                result = self._merge_images_to_pdf(input_files, output_dir, dpi, quality)
                results.append(result)
                processed = total_files
            else:
                # 每个图片单独转换为PDF
                for i, input_file in enumerate(input_files):
                    # 检查取消标志
                    if self._check_cancelled():
                        logger.info("转换已取消")
                        break

                    # 报告进度
                    progress = ConversionProgress(
                        current=i + 1,
                        total=total_files,
                        current_file=input_file.name,
                        message=f"正在处理: {input_file.name}"
                    )
                    self._report_progress(progress)

                    # 转换单个图片
                    result = self._convert_single(input_file, output_dir, dpi, quality)
                    results.append(result)
                    processed = i + 1

            # 报告完成进度
            if not self._check_cancelled():
                progress = ConversionProgress(
                    current=processed,
                    total=total_files,
                    message="处理完成"
                )
                self._report_progress(progress)

        except Exception as e:
            logger.error(f"图片转PDF转换出错: {e}", exc_info=True)

        # 统计结果
        success_count = sum(1 for r in results if r.success())
        logger.info(
            f"图片转PDF转换完成 | "
            f"总数: {len(results)} | "
            f"成功: {success_count} | "
            f"失败: {len(results) - success_count}"
        )

        return results

    def validate_input(self, file_path: Path) -> bool:
        """
        验证输入文件是否有效

        检查文件是否存在且格式受支持。

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果文件有效返回True，否则返回False

        Example:
            >>> converter.validate_input(Path("photo.jpg"))
            True
        """
        # 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return False

        # 检查是否为文件
        if not file_path.is_file():
            logger.warning(f"路径不是文件: {file_path}")
            return False

        # 检查文件格式
        extension = get_file_extension(file_path)
        if extension.lower() not in [fmt.lower() for fmt in self.supported_input_formats]:
            logger.warning(f"不支持的图片格式: {extension}")
            return False

        return True

    # ==================== 内部方法 ====================
    def _convert_single(
        self,
        input_file: Path,
        output_dir: Path,
        dpi: int,
        quality: int
    ) -> ConversionResult:
        """
        转换单个图片为PDF

        Args:
            input_file: 输入图片文件路径
            output_dir: 输出目录路径
            dpi: DPI设置
            quality: 压缩质量

        Returns:
            ConversionResult: 转换结果
        """
        result = ConversionResult(input_file=input_file)

        try:
            logger.debug(f"开始转换图片: {input_file.name}")

            # 打开图片
            img = Image.open(input_file)

            # 转换为RGB模式（PDF不支持透明通道）
            original_mode = img.mode
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))

                # 处理调色板模式
                if img.mode == 'P':
                    img = img.convert('RGBA')

                # 处理透明通道
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')

                logger.debug(f"图片模式转换: {original_mode} -> RGB")

            # 生成输出文件名
            output_filename = self.get_output_filename(input_file, 'pdf')
            output_path = output_dir / output_filename

            # 如果文件已存在，生成唯一文件名
            if output_path.exists():
                output_filename = get_unique_filename(output_dir, output_filename)
                output_path = output_dir / output_filename

            # 保存为PDF
            img.save(
                output_path,
                'PDF',
                resolution=dpi,
                quality=quality
            )

            # 关闭图片
            img.close()

            result.output_file = output_path
            result.status = ConversionStatus.COMPLETED
            result.message = "转换成功"

            logger.info(f"图片转换成功: {input_file.name} -> {output_filename}")

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"图片转换失败: {input_file.name} - {e}", exc_info=True)

        return result

    def _merge_images_to_pdf(
        self,
        input_files: List[Path],
        output_dir: Path,
        dpi: int,
        quality: int
    ) -> ConversionResult:
        """
        将多个图片合并为一个PDF

        Args:
            input_files: 输入图片文件路径列表
            output_dir: 输出目录路径
            dpi: DPI设置
            quality: 压缩质量

        Returns:
            ConversionResult: 转换结果
        """
        # 使用第一个文件名作为输出文件名
        first_file = input_files[0]
        result = ConversionResult(input_file=first_file)

        images: List[Image.Image] = []

        try:
            logger.debug(f"开始合并 {len(input_files)} 张图片")

            for i, input_file in enumerate(input_files):
                # 检查取消标志
                if self._check_cancelled():
                    logger.info("合并已取消")
                    result.status = ConversionStatus.CANCELLED
                    return result

                # 报告进度
                progress = ConversionProgress(
                    current=i + 1,
                    total=len(input_files),
                    current_file=input_file.name,
                    message=f"正在处理: {input_file.name}"
                )
                self._report_progress(progress)

                # 打开图片
                img = Image.open(input_file)

                # 转换为RGB模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    else:
                        img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                images.append(img)

            # 生成输出文件名
            output_filename = f"{first_file.stem}_merged.pdf"
            output_path = output_dir / output_filename

            # 如果文件已存在，生成唯一文件名
            if output_path.exists():
                output_filename = get_unique_filename(output_dir, output_filename)
                output_path = output_dir / output_filename

            # 保存为PDF（第一页保存，其余页追加）
            if images:
                first_img = images[0]
                other_imgs = images[1:] if len(images) > 1 else []

                first_img.save(
                    output_path,
                    'PDF',
                    resolution=dpi,
                    quality=quality,
                    save_all=True,
                    append_images=other_imgs
                )

                # 关闭所有图片
                for img in images:
                    img.close()

            result.output_file = output_path
            result.status = ConversionStatus.COMPLETED
            result.message = f"成功合并 {len(images)} 张图片"

            logger.info(f"图片合并成功: {len(images)} 张图片 -> {output_filename}")

        except Exception as e:
            # 关闭所有已打开的图片
            for img in images:
                try:
                    img.close()
                except Exception:
                    pass

            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"图片合并失败: {e}", exc_info=True)

        return result