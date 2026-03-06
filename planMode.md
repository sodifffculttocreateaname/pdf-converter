# PDF工具箱项目架构文档

## 一、项目概述

PDF工具箱是一个功能完整的PDF转换工具，具备13个功能模块，采用PySide6图形界面，支持跨平台运行和拖拽上传。

## 二、项目结构

```
pdfTools/
├── main.py                      # 程序入口
├── requirements.txt             # 依赖清单
│
├── config/                      # 配置模块
│   ├── __init__.py
│   ├── settings.py              # 全局配置（应用信息、默认路径、日志配置等）
│   └── constants.py             # 常量定义（枚举、格式列表、模块名称等）
│
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── base_converter.py        # 转换器基类（BaseConverter、ConversionResult、ConversionProgress）
│   └── dispatcher.py            # 任务调度器（TaskDispatcher单例类）
│
├── converters/                  # 转换器模块（13个功能模块）
│   ├── __init__.py              # 模块初始化和注册函数
│   ├── image_to_pdf.py          # 图片转PDF
│   ├── pdf_to_image.py          # PDF转图片
│   ├── pdf_to_excel.py          # PDF转Excel
│   ├── pdf_to_word.py           # PDF转Word
│   ├── word_to_pdf.py           # Word转PDF
│   ├── ppt_to_pdf.py            # PPT转PDF
│   ├── excel_to_pdf.py          # Excel转PDF
│   ├── html_to_pdf.py           # 网页转PDF
│   ├── txt_to_pdf.py            # TXT转PDF
│   ├── doc_to_pdf.py            # 通用文档转PDF
│   ├── pdf_merge.py             # PDF合并
│   ├── pdf_split.py             # PDF拆分
│   └── pdf_compress.py          # PDF压缩
│
├── gui/                         # 图形界面模块
│   ├── __init__.py
│   ├── main_window.py           # 主窗口（MainWindow类）
│   ├── widgets/                 # UI组件
│   │   ├── __init__.py
│   │   ├── drag_drop_area.py    # 拖拽上传组件（DragDropArea）
│   │   ├── file_list_widget.py  # 文件列表组件（FileListWidget、FileItem）
│   │   ├── progress_widget.py   # 进度显示组件（ProgressWidget）
│   │   └── settings_panel.py    # 设置面板组件（SettingsPanel）
│   └── styles/
│       ├── __init__.py
│       └── stylesheet.py        # QSS样式表
│
├── utils/                       # 工具模块
│   ├── __init__.py
│   ├── file_utils.py            # 文件操作工具
│   └── logger.py                # 日志工具（基于loguru）
│
└── tests/                       # 测试目录
```

## 三、核心类设计

### 3.1 转换器基类 (core/base_converter.py)

```python
@dataclass
class ConversionResult:
    """转换结果数据类"""
    input_file: Path                           # 输入文件路径
    output_file: Optional[Path] = None         # 输出文件路径
    status: ConversionStatus = ConversionStatus.PENDING  # 状态
    message: str = ""                          # 消息
    error: Optional[str] = None                # 错误信息

@dataclass
class ConversionProgress:
    """转换进度数据类"""
    current: int = 0           # 当前进度
    total: int = 0             # 总数
    current_file: str = ""     # 当前处理的文件
    message: str = ""          # 进度消息

class BaseConverter(ABC):
    """转换器抽象基类"""

    name: str                           # 模块名称
    description: str                    # 模块描述
    supported_input_formats: List[str]  # 支持的输入格式
    supported_output_formats: List[str]  # 支持的输出格式

    def convert(input_files, output_dir, **kwargs) -> List[ConversionResult]
    def validate_input(file_path) -> bool
    def set_progress_callback(callback)
    def cancel()
```

### 3.2 任务调度器 (core/dispatcher.py)

```python
class TaskDispatcher:
    """任务调度器单例类"""

    def register_converter(converter: BaseConverter)    # 注册转换器
    def get_converter(name: str) -> BaseConverter       # 获取转换器
    def add_task(converter_name, input_files, output_dir, **kwargs)  # 添加任务
    def start() -> bool                                 # 启动任务处理
    def stop()                                          # 停止任务处理
    def cancel_current()                                # 取消当前任务
    def set_progress_callback(callback)                 # 设置进度回调
    def set_completion_callback(callback)               # 设置完成回调
```

### 3.3 GUI组件

```python
class DragDropArea(QWidget):
    """拖拽上传区域"""
    files_dropped = Signal(list)  # 文件拖放信号

class FileListWidget(QWidget):
    """文件列表组件"""
    files_changed = Signal()      # 文件列表变化信号

    def add_files(files: List[Path])
    def clear_files()
    def get_files() -> List[Path]
    def update_file_status(file_path, status, message)

class ProgressWidget(QWidget):
    """进度显示组件"""
    cancelled = Signal()          # 取消信号

    def set_progress(value, total)
    def set_percentage(percentage)
    def set_status(status)
    def start()
    def complete()
    def reset()

class SettingsPanel(QWidget):
    """设置面板组件"""
    settings_changed = Signal()   # 设置变化信号

    def get_output_dir() -> Path
    def get_output_format() -> str
    def get_dpi() -> int
    def get_quality() -> int

class MainWindow(QMainWindow):
    """主窗口"""
    conversion_started = Signal()   # 转换开始信号
    conversion_finished = Signal()  # 转换完成信号
```

## 四、功能模块说明

| 模块 | 类名 | 输入格式 | 输出格式 | 核心依赖 |
|------|------|----------|----------|----------|
| 图片转PDF | ImageToPdfConverter | jpg/jpeg/png/bmp/tiff/gif/webp | pdf | Pillow |
| PDF转图片 | PdfToImageConverter | pdf | png/jpg/bmp/tiff | pdf2image, poppler |
| PDF合并 | PdfMergeConverter | pdf | pdf | PyPDF2 |
| PDF拆分 | PdfSplitConverter | pdf | pdf | PyPDF2 |
| PDF压缩 | PdfCompressConverter | pdf | pdf | pikepdf |
| TXT转PDF | TxtToPdfConverter | txt | pdf | reportlab, chardet |
| Word转PDF | WordToPdfConverter | doc/docx | pdf | python-docx, pywin32(可选) |
| PPT转PDF | PptToPdfConverter | ppt/pptx | pdf | python-pptx, pywin32(可选) |
| Excel转PDF | ExcelToPdfConverter | xls/xlsx | pdf | openpyxl, pywin32(可选) |
| PDF转Word | PdfToWordConverter | pdf | docx | pdf2docx |
| PDF转Excel | PdfToExcelConverter | pdf | xlsx | pdfplumber, openpyxl |
| 网页转PDF | HtmlToPdfConverter | html/htm/url | pdf | playwright |
| 文档转PDF | DocToPdfConverter | 所有上述格式 | pdf | 组合上述转换器 |

## 五、数据流程

```
用户操作
    │
    ▼
┌─────────────────┐
│   MainWindow    │ ← 用户选择功能、添加文件、设置参数
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TaskDispatcher  │ ← 注册所有转换器，管理任务队列
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ BaseConverter   │ ← 具体转换器执行转换
│  (子类实现)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ConversionResult│ ← 返回转换结果
└─────────────────┘
```

## 六、关键设计模式

1. **策略模式**: 每个转换器实现统一的BaseConverter接口
2. **单例模式**: TaskDispatcher确保全局只有一个任务调度器
3. **观察者模式**: 通过信号/回调机制通知UI更新
4. **工厂模式**: DocToPdfConverter根据文件类型自动选择转换器

## 七、扩展新转换器的步骤

1. 在 `converters/` 目录下创建新文件，如 `xxx_to_yyy.py`
2. 继承 `BaseConverter` 类，实现以下内容：
   - `name`: 模块名称
   - `description`: 模块描述
   - `supported_input_formats`: 支持的输入格式列表
   - `supported_output_formats`: 支持的输出格式列表
   - `convert()`: 核心转换逻辑
   - `validate_input()`: 输入验证逻辑
3. 在 `converters/__init__.py` 的 `register_all_converters()` 中注册新转换器
4. 在 `config/constants.py` 的 `MODULE_NAMES` 中添加模块名称映射

## 八、依赖说明

```
# GUI框架
PySide6>=6.6.0

# PDF处理
PyPDF2>=3.0.0          # PDF合并、拆分
pdf2image>=1.16.0      # PDF转图片
pikepdf>=8.0.0         # PDF压缩
pdfplumber>=0.10.0     # PDF表格提取
pdf2docx>=0.5.0        # PDF转Word

# 图片处理
Pillow>=10.0.0

# 文档处理
python-docx>=1.0.0     # Word文档
python-pptx>=0.6.21    # PowerPoint
openpyxl>=3.1.0        # Excel
reportlab>=4.0.0       # PDF生成

# 网页转PDF
playwright>=1.40.0

# 编码检测
chardet>=5.0.0

# 日志
loguru>=0.7.0

# Windows COM支持（可选）
pywin32>=306           # Windows Office自动化
```

## 九、运行环境要求

- Python 3.9+
- poppler（PDF转图片功能，需单独安装）
- Chromium浏览器（网页转PDF功能，运行 `playwright install chromium`）
- Microsoft Office（Windows COM功能，仅Windows可选）

## 十、代码规范

### 10.1 模块文档规范

每个Python文件必须包含以下格式的模块文档字符串：

```python
# -*- coding: utf-8 -*-
"""
模块名称

该模块的功能描述...

功能特点：
- 特点1
- 特点2

使用方式：
    from xxx import yyy
    yyy.function()
"""
```

### 10.2 类文档规范

每个类必须包含详细的文档字符串：

```python
class ClassName:
    """
    类的简短描述

    详细描述...

    Attributes:
        attr1: 属性1描述
        attr2: 属性2描述

    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
```

### 10.3 方法文档规范

每个公共方法必须包含完整的文档字符串：

```python
def method_name(self, param1: Type, param2: Type) -> ReturnType:
    """
    方法的简短描述

    详细描述...

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ExceptionType: 异常描述

    Example:
        >>> obj.method_name(value1, value2)
    """
```

### 10.4 变量命名规范

- 私有成员变量：使用下划线前缀，如 `_private_var`
- 保护成员变量：使用单下划线前缀，如 `_protected_var`
- 类常量：使用全大写和下划线，如 `MAX_SIZE`
- 类属性：使用小写和下划线，如 `default_value`

### 10.5 日志记录规范

所有关键操作必须记录日志：

```python
from utils.logger import get_logger

logger = get_logger(__name__)

def important_function():
    logger.info("开始执行重要操作")
    try:
        # 操作代码
        logger.debug("操作详情: xxx")
    except Exception as e:
        logger.error(f"操作失败: {e}", exc_info=True)
        raise
    logger.info("操作完成")
```

### 10.6 错误处理规范

所有可能失败的操作必须使用try-except：

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"具体错误描述: {e}", exc_info=True)
    # 适当的错误处理
except Exception as e:
    logger.error(f"未知错误: {e}", exc_info=True)
    raise
```

### 10.7 类型注解规范

所有公共方法必须有类型注解：

```python
from typing import List, Optional, Dict, Callable

def process_files(
    files: List[Path],
    output_dir: Path,
    callback: Optional[Callable[[int], None]] = None
) -> Dict[str, any]:
    """..."""
    pass
```

## 十一、已规范化的模块

以下模块已完成代码规范化：

### 11.1 config模块
- `settings.py` - 全局配置类，包含详细文档和使用示例
- `constants.py` - 常量定义，枚举类和工具函数
- `__init__.py` - 模块导出和文档

### 11.2 core模块
- `base_converter.py` - 转换器基类，完整文档和类型注解
- `dispatcher.py` - 任务调度器，详细日志和错误处理
- `__init__.py` - 模块导出和文档

### 11.3 utils模块
- `file_utils.py` - 文件操作工具，完整文档和错误处理
- `logger.py` - 日志工具，详细配置说明
- `__init__.py` - 模块导出和文档

### 11.4 gui模块
- `widgets/drag_drop_area.py` - 拖拽上传组件，完整文档和示例
- `widgets/file_list_widget.py` - 文件列表组件，详细文档
- `widgets/progress_widget.py` - 进度显示组件，完整文档
- `widgets/settings_panel.py` - 设置面板组件，详细文档
- `widgets/__init__.py` - 组件导出
- `styles/stylesheet.py` - QSS样式表，详细注释
- `styles/__init__.py` - 样式导出
- `__init__.py` - 模块导出

### 11.5 converters模块
- `image_to_pdf.py` - 图片转PDF（规范化示例模板）
- `__init__.py` - 转换器注册和导出，详细日志

### 11.6 主程序
- `main.py` - 程序入口，完整文档和异常处理