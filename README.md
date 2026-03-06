# PDF工具箱

一个基于 PySide6 开发的桌面端 PDF 处理工具，支持 25 种文档转换和处理功能。

## 功能特性

### 文档转换类（12个功能）
| 功能 | 说明 |
|------|------|
| 图片转PDF | 支持 JPG/PNG/BMP/TIFF/GIF 等格式 |
| PDF转图片 | 导出为 PNG/JPEG/BMP/TIFF 格式 |
| PDF转Word | 保留原始格式和布局 |
| PDF转Excel | 智能识别表格结构 |
| Word转PDF | 支持 DOC/DOCX 格式 |
| Excel转PDF | 支持 XLS/XLSX 格式，自动适配页面 |
| PPT转PDF | 支持 PPT/PPTX 格式 |
| TXT转PDF | 支持多种编码自动检测 |
| 网页转PDF | 支持 URL 和 HTML 文件 |
| 通用文档转PDF | 自动识别文档类型并转换 |
| PDF合并 | 多文件合并，支持拖拽排序 |
| PDF拆分 | 支持单页、范围、奇偶页拆分 |

### PDF处理类（13个功能）
| 功能 | 说明 |
|------|------|
| PDF压缩 | 低/中/高压缩级别可选 |
| PDF提取图片 | 提取内嵌图片，支持最小尺寸过滤 |
| PDF旋转页面 | 90°/180°/270° 旋转 |
| PDF增删页 | 删除页面或插入空白页 |
| PDF编排页面 | 可视化拖拽排序 |
| PDF转长图 | 多页合并为一张长图 |
| PDF转黑白 | 灰度或二值化处理 |
| PDF添加页码 | 自定义位置、格式、字体 |
| PDF分割裁剪 | 裁剪边距或水平/垂直分割 |
| PDF页面合并 | 2合1/4合1/6合1 布局 |
| PDF去水印 | 基于颜色/透明度/位置检测 |
| PDF加水印 | 文字或图片水印 |
| PDF加密 | 设置打开密码和权限密码 |
| 发票合并 | 多张发票合并为单个PDF |

## 系统要求

- **操作系统**: Windows 10/11（当前仅支持Windows）
- **Python**: 3.10 或更高版本
- **内存**: 建议 4GB 以上
- **磁盘空间**: 至少 500MB 可用空间

## 安装步骤

### 1. 克隆仓库

```bash
git clone <仓库地址>
cd pdfTools
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# 或使用 conda
conda create -n pdf_tools python=3.12
conda activate pdf_tools
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 Poppler（Windows必需）

Poppler 是 PDF 转图片功能必需的依赖工具。

#### 方法一：下载预编译版本（推荐）

1. 访问 [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases/)
2. 下载最新版本的 `Release-x.x.x.zip`
3. 解压到项目根目录下的 `tools/poppler-25.12.0/` 文件夹

目录结构示例：
```
pdfTools/
├── tools/
│   └── poppler-25.12.0/
│       └── Library/
│           └── bin/
│               ├── pdftoppm.exe
│               ├── pdftocairo.exe
│               └── ...
├── main.py
└── ...
```

#### 方法二：通过环境变量指定路径

如果已安装 Poppler 在其他位置，可设置环境变量：

```bash
setx POPPLER_PATH "C:\path\to\poppler\Library\bin"
```

#### 方法三：添加到系统 PATH

将 Poppler 的 `Library\bin` 目录添加到系统 PATH 环境变量。

### 5. 验证安装

```bash
python main.py
```

## 运行方式

### 开发模式

```bash
python main.py
```

### 打包为可执行文件

#### 安装 PyInstaller

```bash
pip install pyinstaller
```

#### 打包命令

```bash
pyinstaller pdf_tools.spec
```

打包完成后，可执行文件位于 `dist/PDF工具箱/` 目录。

## 项目结构

```
pdfTools/
├── config/                 # 配置文件
│   ├── __init__.py
│   ├── constants.py        # 常量定义
│   └── settings.py         # 应用设置
├── converters/             # 转换器模块（25个功能）
│   ├── image_to_pdf.py
│   ├── pdf_to_image.py
│   ├── pdf_to_word.py
│   ├── pdf_to_excel.py
│   ├── word_to_pdf.py
│   ├── excel_to_pdf.py
│   ├── ppt_to_pdf.py
│   ├── txt_to_pdf.py
│   ├── pdf_merge.py
│   ├── pdf_split.py
│   ├── pdf_compress.py
│   ├── pdf_extract_images.py
│   ├── pdf_add_watermark.py
│   ├── pdf_remove_watermark.py
│   ├── pdf_encrypt.py
│   ├── pdf_rotate.py
│   ├── pdf_organize.py
│   ├── pdf_add_page_numbers.py
│   ├── pdf_crop_split.py
│   ├── pdf_page_merge.py
│   ├── pdf_to_grayscale.py
│   ├── pdf_to_long_image.py
│   ├── pdf_add_remove_pages.py
│   ├── doc_to_pdf.py
│   └── invoice_merge.py
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── base_converter.py   # 转换器基类
│   └── dispatcher.py       # 任务调度器
├── gui/                    # GUI界面
│   ├── __init__.py
│   ├── main_window.py      # 主窗口
│   ├── pages/              # 功能页面
│   ├── styles/             # 样式表
│   └── widgets/            # 自定义控件
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── file_utils.py
│   └── logger.py
├── tools/                  # 外部工具（自行下载）
│   └── poppler-25.12.0/    # PDF处理工具
├── tests/                  # 测试代码
├── main.py                 # 程序入口
├── requirements.txt        # 依赖清单
├── pdf_tools.spec          # PyInstaller打包配置
├── setup.iss               # Inno Setup安装程序配置
└── README.md               # 本文件
```

## 依赖说明

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| PySide6 | >=6.6.0 | GUI框架 |
| Pillow | >=10.0.0 | 图片处理 |
| loguru | >=0.7.0 | 日志记录 |
| chardet | >=5.0.0 | 编码检测 |

### PDF处理依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| pypdf | >=6.0.0 | PDF读写 |
| PyPDF2 | >=3.0.0 | PDF合并拆分 |
| pdf2image | >=1.16.0 | PDF转图片（需poppler） |
| pikepdf | >=8.0.0 | PDF高级处理 |
| pdfplumber | >=0.10.0 | PDF表格提取 |
| pdf2docx | >=0.5.0 | PDF转Word |
| PyMuPDF | >=1.23.0 | PDF渲染处理 |

### 文档处理依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| python-docx | >=1.0.0 | Word处理 |
| python-pptx | >=0.6.21 | PPT处理 |
| openpyxl | >=3.1.0 | Excel处理 |
| reportlab | >=4.0.0 | PDF生成 |

## 常见问题

### 1. ImportError: Unable to find poppler

**原因**: 未安装 Poppler 或路径配置不正确。

**解决**:
- 按上述步骤安装 Poppler
- 确保 `tools/poppler-25.12.0/Library/bin` 目录存在
- 或设置 `POPPLER_PATH` 环境变量

### 2. 转换Word/Excel需要Microsoft Office

**原因**: 某些转换功能使用 COM 接口调用 Office 应用。

**解决**:
- 安装 Microsoft Office 2016 或更高版本
- 或使用开源替代方案（部分功能可能受限）

### 3. 打包后程序无法运行

**原因**: PyInstaller 可能遗漏某些依赖。

**解决**:
- 检查 `pdf_tools.spec` 中的 `hiddenimports`
- 确保所有依赖都安装在打包环境中
- 使用 `--clean` 参数重新打包

### 4. 中文显示异常

**原因**: 缺少中文字体。

**解决**:
- Windows 通常自带中文字体，无需额外配置
- 如遇到乱码，请确保系统安装了常见中文字体（如宋体、微软雅黑）

## 开发指南

### 添加新功能

1. 在 `converters/` 目录创建新的转换器类，继承 `BaseConverter`
2. 在 `gui/pages/` 目录创建对应的页面类
3. 在 `config/constants.py` 添加模块名称映射
4. 在 `gui/pages/__init__.py` 导出页面类
5. 在 `gui/main_window.py` 注册新页面

### 代码规范

- 所有模块必须有文档字符串
- 类和方法必须有 Args、Returns 说明
- 私有成员使用下划线前缀（如 `_private_var`）
- 关键操作必须记录日志
- 所有公共方法必须有类型注解

## 许可证

本项目仅供学习交流使用。

## 更新日志

### 2026-03-06
- 优化 .gitignore 配置，移除构建产物和外部工具
- 创建 README 文档

### 2026-03-05
- 为所有功能模块添加详细运行日志
- 统一所有功能页面的按钮布局
- 修复 Excel 转 PDF 文字超出边界问题
- 添加"新转换"按钮到所有功能页面

### 2026-02-27
- 完成 PyInstaller 打包配置
- 添加"打开输出目录"功能

### 2026-02-26
- 完成 25 个功能模块开发
- 完成 GUI 界面开发

---

如有问题或建议，欢迎提交 Issue 或 Pull Request。
