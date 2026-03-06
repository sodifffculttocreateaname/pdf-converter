# -*- coding: utf-8 -*-
"""
Word转PDF转换器
支持多种转换方式:
1. Windows COM (仅Windows，需要安装Microsoft Word)
2. python-docx + reportlab (跨平台，但格式可能不完全准确)
"""
import platform
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from config.settings import Settings
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class WordToPdfConverter(BaseConverter):
    """Word转PDF转换器"""

    name = "Word转PDF"
    description = "将Word文档转换为PDF"
    supported_input_formats = ["doc", "docx"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        super().__init__()
        self._use_com = self._check_com_available()

    def _check_com_available(self) -> bool:
        """检查COM是否可用（仅Windows）"""
        if platform.system() != 'Windows':
            return False

        try:
            import win32com.client
            return True
        except ImportError:
            return False

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行Word转PDF转换

        Args:
            input_files: 输入Word文件列表
            output_dir: 输出目录
            **kwargs: 额外参数

        Returns:
            转换结果列表
        """
        results = []

        # 确保输出目录存在
        ensure_dir(output_dir)

        # 选择转换方法
        if self._use_com:
            results = self._convert_with_com(input_files, output_dir)
        else:
            results = self._convert_with_docx(input_files, output_dir)

        return results

    def _convert_with_com(self, input_files: List[Path], output_dir: Path) -> List[ConversionResult]:
        """
        使用Windows COM转换（需要安装Microsoft Word）

        Args:
            input_files: 输入文件列表
            output_dir: 输出目录

        Returns:
            转换结果列表
        """
        import win32com.client
        import pythoncom

        results = []
        word_app = None

        try:
            # 初始化COM
            pythoncom.CoInitialize()

            # 创建Word应用
            word_app = win32com.client.Dispatch("Word.Application")
            word_app.Visible = False

            total_files = len(input_files)

            for i, input_file in enumerate(input_files):
                if self._check_cancelled():
                    break

                # 报告进度
                progress = ConversionProgress(
                    current=i + 1,
                    total=total_files,
                    current_file=input_file.name,
                    message=f"正在转换: {input_file.name}"
                )
                self._report_progress(progress)

                result = ConversionResult(input_file=input_file)

                try:
                    # 打开文档
                    doc = word_app.Documents.Open(str(input_file.absolute()))

                    # 生成输出文件名
                    output_filename = self.get_output_filename(input_file, 'pdf')
                    output_path = output_dir / output_filename

                    # 导出为PDF
                    # wdFormatPDF = 17
                    doc.SaveAs(str(output_path), FileFormat=17)
                    doc.Close()

                    result.output_file = output_path
                    result.status = ConversionStatus.COMPLETED
                    result.message = "转换成功"

                    logger.info(f"Word转PDF成功: {input_file.name}")

                except Exception as e:
                    result.status = ConversionStatus.FAILED
                    result.error = str(e)
                    logger.error(f"Word转PDF失败: {input_file.name} - {e}")

                results.append(result)

        except Exception as e:
            logger.error(f"COM转换失败: {e}")
            # 如果COM失败，回退到docx方法
            return self._convert_with_docx(input_files, output_dir)

        finally:
            # 关闭Word应用
            if word_app:
                try:
                    word_app.Quit()
                except Exception:
                    pass

            # 清理COM
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=len(input_files),
                total=len(input_files),
                message="处理完成"
            )
            self._report_progress(progress)

        return results

    def _convert_with_docx(self, input_files: List[Path], output_dir: Path) -> List[ConversionResult]:
        """
        使用python-docx和reportlab转换（跨平台，格式可能不完全准确）

        Args:
            input_files: 输入文件列表
            output_dir: 输出目录

        Returns:
            转换结果列表
        """
        from docx import Document
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        results = []

        # 注册字体
        self._register_font()

        total_files = len(input_files)

        for i, input_file in enumerate(input_files):
            if self._check_cancelled():
                break

            # 报告进度
            progress = ConversionProgress(
                current=i + 1,
                total=total_files,
                current_file=input_file.name,
                message=f"正在转换: {input_file.name}"
            )
            self._report_progress(progress)

            result = ConversionResult(input_file=input_file)

            try:
                # 读取Word文档
                doc = Document(str(input_file))

                # 生成输出文件名
                output_filename = self.get_output_filename(input_file, 'pdf')
                output_path = output_dir / output_filename

                # 创建PDF
                pdf_doc = SimpleDocTemplate(
                    str(output_path),
                    pagesize=A4,
                    leftMargin=2*cm,
                    rightMargin=2*cm,
                    topMargin=2*cm,
                    bottomMargin=2*cm
                )

                # 创建样式
                styles = getSampleStyleSheet()
                normal_style = ParagraphStyle(
                    'NormalStyle',
                    parent=styles['Normal'],
                    fontName=self._font_name,
                    fontSize=11,
                    leading=16,
                )
                heading_style = ParagraphStyle(
                    'HeadingStyle',
                    parent=styles['Heading1'],
                    fontName=self._font_name,
                    fontSize=16,
                    leading=22,
                )

                # 构建内容
                story = []

                for para in doc.paragraphs:
                    if self._check_cancelled():
                        break

                    text = para.text.strip()
                    if not text:
                        story.append(Spacer(1, 8))
                        continue

                    # 转义特殊字符
                    text = text.replace('&', '&amp;')
                    text = text.replace('<', '&lt;')
                    text = text.replace('>', '&gt;')

                    # 根据段落样式选择样式
                    if para.style.name.startswith('Heading'):
                        story.append(Paragraph(text, heading_style))
                    else:
                        story.append(Paragraph(text, normal_style))

                if self._check_cancelled():
                    result.status = ConversionStatus.CANCELLED
                    if output_path.exists():
                        output_path.unlink()
                    results.append(result)
                    continue

                # 生成PDF
                pdf_doc.build(story)

                result.output_file = output_path
                result.status = ConversionStatus.COMPLETED
                result.message = "转换成功"

                logger.info(f"Word转PDF成功: {input_file.name}")

            except Exception as e:
                result.status = ConversionStatus.FAILED
                result.error = str(e)
                logger.error(f"Word转PDF失败: {input_file.name} - {e}")

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

    _font_registered = False
    _font_name = "SimSun"

    def _register_font(self):
        """注册中文字体"""
        if self._font_registered:
            return

        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            font_paths = [
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\simsun.ttc",
                r"C:\Windows\Fonts\msyh.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/System/Library/Fonts/PingFang.ttc",
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

            self._font_name = "Helvetica"

        except Exception as e:
            logger.warning(f"注册字体失败: {e}")
            self._font_name = "Helvetica"

        self._font_registered = True

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

        return file_path.suffix.lower() in ['.doc', '.docx']