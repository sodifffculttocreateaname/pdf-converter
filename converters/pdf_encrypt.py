# -*- coding: utf-8 -*-
"""
PDF加密转换器

该模块提供PDF加密功能，支持：
- 添加打开密码
- 添加权限密码
- 设置打印、复制、修改权限

使用方式：
    from converters.pdf_encrypt import PdfEncryptConverter

    converter = PdfEncryptConverter()
    results = converter.convert([Path("input.pdf")], Path("output"))
"""
from pathlib import Path
from typing import List

from config.constants import ConversionStatus
from core.base_converter import BaseConverter, ConversionProgress, ConversionResult
from utils.file_utils import ensure_dir
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfEncryptConverter(BaseConverter):
    """
    PDF加密转换器

    为PDF文件添加密码保护和权限控制。

    Attributes:
        name: 转换器名称
        description: 转换器描述
        supported_input_formats: 支持的输入格式列表
        supported_output_formats: 支持的输出格式列表
    """

    name = "PDF加密"
    description = "为PDF添加密码保护和权限控制"
    supported_input_formats = ["pdf"]
    supported_output_formats = ["pdf"]

    def __init__(self):
        """初始化PDF加密转换器"""
        super().__init__()
        self._user_password = ""
        self._owner_password = ""
        self._allow_printing = True
        self._allow_copying = False
        self._allow_modifying = False

    def set_passwords(self, user_password: str, owner_password: str = ""):
        """
        设置密码

        Args:
            user_password: 打开密码（用户密码）
            owner_password: 权限密码（所有者密码），可选
        """
        self._user_password = user_password
        self._owner_password = owner_password if owner_password else user_password

    def set_permissions(self, allow_printing: bool = True,
                        allow_copying: bool = False,
                        allow_modifying: bool = False):
        """
        设置权限

        Args:
            allow_printing: 允许打印
            allow_copying: 允许复制
            allow_modifying: 允许修改
        """
        self._allow_printing = allow_printing
        self._allow_copying = allow_copying
        self._allow_modifying = allow_modifying

    def convert(self, input_files: List[Path], output_dir: Path, **kwargs) -> List[ConversionResult]:
        """
        执行PDF加密

        Args:
            input_files: 输入PDF文件列表
            output_dir: 输出目录
            **kwargs: 额外参数
                - user_password: 打开密码
                - owner_password: 权限密码
                - allow_printing: 允许打印
                - allow_copying: 允许复制
                - allow_modifying: 允许修改

        Returns:
            转换结果列表
        """
        results = []

        # 应用参数
        user_password = kwargs.get('user_password', self._user_password)
        owner_password = kwargs.get('owner_password', self._owner_password)
        allow_printing = kwargs.get('allow_printing', self._allow_printing)
        allow_copying = kwargs.get('allow_copying', self._allow_copying)
        allow_modifying = kwargs.get('allow_modifying', self._allow_modifying)

        # 验证密码
        if not user_password:
            return [ConversionResult(
                input_file=input_files[0] if input_files else Path(""),
                status=ConversionStatus.FAILED,
                error="必须设置打开密码"
            )]

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
                message=f"正在加密: {input_file.name}"
            )
            self._report_progress(progress)

            # 执行加密
            result = self._encrypt_pdf(
                input_file, output_dir,
                user_password, owner_password,
                allow_printing, allow_copying, allow_modifying
            )
            results.append(result)

        # 报告完成进度
        if not self._check_cancelled():
            progress = ConversionProgress(
                current=total_files,
                total=total_files,
                message="加密完成"
            )
            self._report_progress(progress)

        return results

    def _encrypt_pdf(self, input_file: Path, output_dir: Path,
                     user_password: str, owner_password: str,
                     allow_printing: bool, allow_copying: bool,
                     allow_modifying: bool) -> ConversionResult:
        """
        加密PDF文件

        Args:
            input_file: 输入PDF文件
            output_dir: 输出目录
            user_password: 打开密码
            owner_password: 权限密码
            allow_printing: 允许打印
            allow_copying: 允许复制
            allow_modifying: 允许修改

        Returns:
            转换结果
        """
        try:
            # 尝试使用pikepdf（更强大的加密功能）
            try:
                import pikepdf

                pdf = pikepdf.open(str(input_file))

                # 设置权限
                perm = pikepdf.Permissions()
                perm.print = allow_printing
                perm.copy = allow_copying
                perm.modify = allow_modifying

                # 保存加密文件
                output_path = output_dir / f"{input_file.stem}_encrypted.pdf"
                pdf.save(
                    str(output_path),
                    encryption=pikepdf.Encryption(
                        user=user_password,
                        owner=owner_password,
                        R=4  # 使用128位AES加密
                    )
                )
                pdf.close()

                result = ConversionResult(
                    input_file=input_file,
                    output_file=output_path,
                    status=ConversionStatus.COMPLETED,
                    message="PDF加密完成"
                )
                logger.info(f"PDF加密成功: {input_file.name}")
                return result

            except ImportError:
                # 回退到PyPDF2
                from pypdf import PdfReader, PdfWriter

                reader = PdfReader(str(input_file))
                writer = PdfWriter()

                # 复制所有页面
                for page in reader.pages:
                    writer.add_page(page)

                # 设置加密
                output_path = output_dir / f"{input_file.stem}_encrypted.pdf"
                with open(output_path, 'wb') as f:
                    writer.encrypt(user_password, owner_password)
                    writer.write(f)

                result = ConversionResult(
                    input_file=input_file,
                    output_file=output_path,
                    status=ConversionStatus.COMPLETED,
                    message="PDF加密完成"
                )
                logger.info(f"PDF加密成功: {input_file.name}")
                return result

        except Exception as e:
            logger.error(f"PDF加密失败: {input_file.name} - {e}")
            return ConversionResult(
                input_file=input_file,
                status=ConversionStatus.FAILED,
                error=str(e)
            )

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