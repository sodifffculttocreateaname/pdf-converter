# -*- coding: utf-8 -*-
"""
PyInstaller 打包配置文件

用于将 PDF工具箱 打包为 Windows 可执行程序。

使用方式:
    pyinstaller pdf_tools.spec

输出目录: dist/PDF工具箱/
"""
import sys
from pathlib import Path

block_cipher = None

# 项目根目录
PROJECT_ROOT = Path(SPECPATH)

# Poppler 工具路径
POPPLER_PATH = PROJECT_ROOT / 'tools' / 'poppler-25.12.0' / 'Library' / 'bin'

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # 包含 Poppler 工具（整个 Library 目录）
        (str(PROJECT_ROOT / 'tools' / 'poppler-25.12.0' / 'Library'), 'tools/poppler-25.12.0/Library'),
    ],
    hiddenimports=[
        # PySide6 隐式导入
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # PDF库隐式导入
        'pypdf',
        'PyPDF2',
        'pdf2image',
        'pikepdf',
        'pdfplumber',
        'pdf2docx',
        'fitz',  # PyMuPDF
        'PIL',
        'docx',
        'pptx',
        'openpyxl',
        'reportlab',
        'chardet',
        'loguru',
        # pdf2docx 依赖
        'numpy',
        'cv2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块
        'tkinter',
        'matplotlib',
        'pandas',
        'scipy',
        'pytest',
        'playwright',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDF工具箱',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='resources/icon.ico',  # 应用图标（如有可取消注释）
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDF工具箱',
)