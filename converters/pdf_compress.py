# -*- coding: utf-8 -*-
"""
PDF压缩转换器
"""
from pathlib import Path
from typing import List

import pikepdf

from config.constants import ConversionStatus
from config.settings import Settings
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir, get_file_size, get_unique_filename
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfCompressConverter(BaseConverter):
    """PDF压缩转换器"""

    name = "PDF压缩"
    description = "压缩PDF文件以减小文件大小"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    # 压缩级别
    COMPRESSION_LOW = "low"           # 低压缩（保持质量）
    COMPRESSION_MEDIUM = "medium"     # 中等压缩
    COMPRESSION_HIGH = "high"         # 高压缩（可能损失质量）

    def __init__(self):
        super().__init__()
        self._compression_level = self.COMPRESSION_MEDIUM
        self._quality = 85

    def set_compression_level(self, level: str):
        """设置压缩级别"""
        self._compression_level = level

    def set_quality(self, quality: int):
        """设置质量（1-100）"""
        self._quality = max(1, min(100, quality))

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF压缩

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数 (level, quality)

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        level = kwargs.get('level', self._compression_level)
        quality = kwargs.get('quality', self._quality)

        # 确保输出目录存在
        ensure_dir(output_dir)

        total_files = len(input_files)

        for i, input_file in enumerate(input_files):
            if self._check_cancelled():
                break

            # 报告进度
            progress = ConversionProgress(
                current=i + 1,
                total=total_files,
                current_file=input_file.name,
                message=f"正在压缩: {input_file.name}"
            )
            self._report_progress(progress)

            result = self._compress_pdf(input_file, output_dir, level, quality)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="压缩完成"
            )
            self._report_progress(progress)

        return results

    def _compress_pdf(self, input_file: Path, output_dir: Path,
                      level: str, quality: int) -> ConversionResult:
        """
        压缩单个PDF

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            level: 压缩级别
            quality: 质量

        Returns:
            转换结果
        """
        result = ConversionResult(input_file=input_file)

        try:
            original_size = get_file_size(input_file)

            # 生成输出文件名
            output_filename = f"{input_file.stem}_compressed.pdf"
            output_path = output_dir / output_filename

            # 确保文件名唯一
            if output_path.exists():
                output_filename = get_unique_filename(output_dir, output_filename)
                output_path = output_dir / output_filename

            # 根据压缩级别设置参数
            if level == self.COMPRESSION_LOW:
                # 低压缩 - 只移除重复资源
                compress_fonts = False
                compress_streams = True
                object_stream_mode = pikepdf.ObjectStreamMode.preserve
            elif level == self.COMPRESSION_HIGH:
                # 高压缩 - 激进压缩
                compress_fonts = True
                compress_streams = True
                object_stream_mode = pikepdf.ObjectStreamMode.generate
            else:
                # 中等压缩 - 平衡质量和大小
                compress_fonts = True
                compress_streams = True
                object_stream_mode = pikepdf.ObjectStreamMode.preserve

            # 打开PDF
            with pikepdf.open(str(input_file)) as pdf:
                # 压缩图片（如果需要）
                if level in [self.COMPRESSION_MEDIUM, self.COMPRESSION_HIGH]:
                    self._compress_images(pdf, quality)

                # 保存压缩后的PDF
                pdf.save(
                    str(output_path),
                    compress_streams=compress_streams,
                    object_stream_mode=object_stream_mode
                )

            compressed_size = get_file_size(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            result.output_file = output_path
            result.status = ConversionStatus.COMPLETED
            result.message = f"压缩 {compression_ratio:.1f}% ({self._format_size(original_size)} -> {self._format_size(compressed_size)})"

            logger.info(f"PDF压缩成功: {input_file.name}, 压缩率: {compression_ratio:.1f}%")

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"PDF压缩失败: {input_file.name} - {e}")

        return result

    def _compress_images(self, pdf, quality: int):
        """
        压缩PDF中的图片

        Args:
            pdf: pikepdf对象
            quality: 压缩质量
        """
        try:
            from PIL import Image
            import io

            for page in pdf.pages:
                if self._check_cancelled():
                    break

                if '/Resources' in page and '/XObject' in page['/Resources']:
                    xobject = page['/Resources']['/XObject']

                    for key in xobject.keys():
                        obj = xobject[key]

                        # 检查是否是图片
                        if obj.get('/Subtype') == '/Image':
                            try:
                                # 获取图片数据
                                if obj.get('/Filter') == '/DCTDecode':
                                    # JPEG图片，已经压缩
                                    continue

                                # 尝试重新压缩
                                raw_data = obj.read_raw_bytes()
                                if len(raw_data) > 0:
                                    # 使用PIL处理图片
                                    img = Image.open(io.BytesIO(raw_data))

                                    # 转换为RGB（如果需要）
                                    if img.mode in ('RGBA', 'LA', 'P'):
                                        background = Image.new('RGB', img.size, (255, 255, 255))
                                        if img.mode == 'P':
                                            img = img.convert('RGBA')
                                        if img.mode in ('RGBA', 'LA'):
                                            background.paste(img, mask=img.split()[-1])
                                            img = background
                                        else:
                                            img = img.convert('RGB')

                                    # 压缩为JPEG
                                    output = io.BytesIO()
                                    img.save(output, format='JPEG', quality=quality)
                                    compressed_data = output.getvalue()

                                    # 如果压缩后更小，更新图片
                                    if len(compressed_data) < len(raw_data):
                                        obj.write(compressed_data, filter=pikepdf.Name.DCTDecode)

                            except Exception as e:
                                logger.debug(f"压缩图片时出错: {e}")
                                continue

        except Exception as e:
            logger.warning(f"压缩PDF图片失败: {e}")

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def validate_input(self, file_path: Path) -> bool:
        """
        验证输入文件

        Args:
            file_path: 文件路径

        Returns:
            如果文件有效返回 True
        """
        if not file_path.exists():
            return False

        return file_path.suffix.lower() == '.pdf'