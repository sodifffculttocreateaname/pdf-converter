# -*- coding: utf-8 -*-
"""
TXT转PDF转换器
"""
import chardet
from pathlib import Path
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from config.constants import ConversionStatus
from config.settings import Settings
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class TxtToPdfConverter(BaseConverter):
    """TXT转PDF转换器"""

    name = "TXT转PDF"
    description = "将文本文件转换为PDF文档"
    supported_input_formats = ["txt"]
    supported_output_formats = ["pdf"]

    # 支持的编码
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'utf-16', 'utf-32']

    def __init__(self):
        super().__init__()
        self._font_registered = False
        self._font_name = "SimSun"
        self._font_size = 12
        self._line_height = 1.5

    def _register_font(self):
        """注册中文字体"""
        if self._font_registered:
            return

        try:
            # 尝试注册常见的中文字体
            font_paths = [
                # Windows字体路径
                r"C:\Windows\Fonts\simhei.ttf",  # 黑体
                r"C:\Windows\Fonts\simsun.ttc",  # 宋体
                r"C:\Windows\Fonts\msyh.ttc",    # 微软雅黑
                # Linux字体路径
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                # macOS字体路径
                "/System/Library/Fonts/PingFang.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]

            for font_path in font_paths:
                if Path(font_path).exists():
                    try:
                        pdfmetrics.registerFont(TTFont(self._font_name, font_path))
                        self._font_registered = True
                        logger.info(f"成功注册字体: {font_path}")
                        return
                    except Exception:
                        continue

            # 如果没有找到中文字体，使用默认字体
            logger.warning("未找到中文字体，使用默认字体")
            self._font_name = "Helvetica"

        except Exception as e:
            logger.warning(f"注册字体失败: {e}")
            self._font_name = "Helvetica"

        self._font_registered = True

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行TXT转PDF转换

        Args:
            input_files: 输入文本文件列表
            output_dir: 输出目录
            **kwargs: 额外参数 (font_size, line_height)

        Returns:
            转换结果列表
        """
        results = []

        # 注册字体
        self._register_font()

        # 应用参数
        font_size = kwargs.get('font_size', self._font_size)
        line_height = kwargs.get('line_height', self._line_height)

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
                message=f"正在处理: {input_file.name}"
            )
            self._report_progress(progress)

            result = self._convert_txt(input_file, output_dir, font_size, line_height)
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="处理完成"
            )
            self._report_progress(progress)

        return results

    def _convert_txt(self, input_file: Path, output_dir: Path,
                     font_size: int, line_height: float) -> ConversionResult:
        """
        转换单个文本文件

        Args:
            input_file: 输入文件
            output_dir: 输出目录
            font_size: 字体大小
            line_height: 行高

        Returns:
            转换结果
        """
        result = ConversionResult(input_file=input_file)

        try:
            # 读取文本内容
            text_content = self._read_text_file(input_file)

            if not text_content:
                result.status = ConversionStatus.FAILED
                result.error = "文件内容为空"
                return result

            # 生成输出文件名
            output_filename = self.get_output_filename(input_file, 'pdf')
            output_path = output_dir / output_filename

            # 创建PDF
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                leftMargin=2*cm,
                rightMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 创建样式
            styles = getSampleStyleSheet()
            text_style = ParagraphStyle(
                'TextStyle',
                parent=styles['Normal'],
                fontName=self._font_name,
                fontSize=font_size,
                leading=font_size * line_height,
                wordWrap='CJK',
            )

            # 构建内容
            story = []

            # 按行分割文本
            lines = text_content.split('\n')
            for line in lines:
                if self._check_cancelled():
                    break

                # 转义特殊字符
                line = line.replace('&', '&amp;')
                line = line.replace('<', '&lt;')
                line = line.replace('>', '&gt;')

                if line.strip():
                    story.append(Paragraph(line, text_style))
                else:
                    story.append(Spacer(1, font_size * line_height))

            if self._check_cancelled():
                result.status = ConversionStatus.CANCELLED
                # 删除未完成的文件
                if output_path.exists():
                    output_path.unlink()
                return result

            # 生成PDF
            doc.build(story)

            result.output_file = output_path
            result.status = ConversionStatus.COMPLETED
            result.message = "转换成功"

            logger.info(f"TXT转PDF成功: {input_file.name}")

        except Exception as e:
            result.status = ConversionStatus.FAILED
            result.error = str(e)
            logger.error(f"TXT转PDF失败: {input_file.name} - {e}")

        return result

    def _read_text_file(self, file_path: Path) -> str:
        """
        读取文本文件（自动检测编码）

        Args:
            file_path: 文件路径

        Returns:
            文本内容
        """
        # 尝试使用chardet检测编码
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8')

            # 尝试使用检测到的编码解码
            try:
                return raw_data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                pass

            # 尝试常见编码
            for enc in self.SUPPORTED_ENCODINGS:
                try:
                    return raw_data.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue

            # 最后尝试utf-8并忽略错误
            return raw_data.decode('utf-8', errors='ignore')

        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return ""

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

        return file_path.suffix.lower() == '.txt'