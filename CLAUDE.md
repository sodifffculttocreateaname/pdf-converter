### 2026-03-05
- **新增**：为所有功能模块添加详细运行日志
  - 修改日志输出路径：从用户目录改为程序根目录下的 `logs/` 文件夹
  - 按日期生成日志文件：`pdf_tools_YYYY-MM-DD.log`（常规日志）和 `error_YYYY-MM-DD.log`（错误日志）
  - 日志格式包含：时间戳、日志级别（INFO/ERROR/DEBUG等）、模块名、函数名、行号、消息
  - 为所有25个转换器模块添加详细日志：
    - 转换开始日志：记录输入文件数、输出目录
    - 转换进度日志：记录每个文件的处理进度
    - 转换成功日志：记录输出文件路径
    - 转换失败日志：记录错误信息和异常堆栈
  - 文件：`config/settings.py`（修改LOG_DIR路径）、所有 `converters/*.py`（增强日志）

### 2026-03-05
- **优化**：统一所有25个功能页面的按钮布局
  - 删除"取消"按钮（功能重复，且用户反馈不需要）
  - 调整按钮顺序："新转换"按钮在左侧，"开始转换"按钮在右侧
  - 所有页面统一布局：左侧（新转换）| 右侧（开始转换）
  - 涉及文件：`gui/pages/` 目录下所有25个页面文件

### 2026-03-05
- **修复**：Excel转PDF文字超出边界问题（彻底解决）
  - 问题：使用openpyxl方法时，长文本仍然超出单元格边界
  - 根本原因：
    1. 中文字符宽度计算不够精确（原1.5单位，实际中文字符更宽）
    2. Table的WORDWRAP对中文支持不完善
    3. 列宽限制过严（最大6cm），导致内容无法完整显示
  - 解决方案：
    1. 将中文字符宽度计算从1.5调整为2.0单位，英文字符保持1.0
    2. 将单元格内容转换为Paragraph对象，利用其`wordWrap='CJK'`特性实现中文自动换行
    3. 增加字符宽度估计值（0.25cm→0.35cm），更精确反映实际渲染宽度
    4. 移除最大列宽限制（6cm），确保内容优先完整显示
    5. 调整单元格对齐方式为TOP（顶部对齐），换行后更美观
    6. 添加足够的单元格内边距（6px上下，4px左右）
  - 文件：`converters/excel_to_pdf.py`

### 2026-03-05
- **修复**：为所有25个功能页面添加"新转换"按钮
  - 添加橙色"新转换"按钮到所有功能页面的操作按钮区域
  - 实现 `_start_new_conversion` 方法，功能包括：
    - 检查是否有正在进行的转换任务，如有则提示确认
    - 清空文件列表并重置进度条、状态标签
    - 重置按钮状态（启用开始按钮，禁用取消按钮）
  - 修复PDF加密页面缺少 `_start_new_conversion` 方法的问题
  - 修复PDF压缩页面重复方法定义的问题（删除10个重复定义）
  - 所有25个功能页面现已全部支持"新转换"功能

### 2026-03-05
- **修复**：Excel转PDF页面错乱和文字挤压问题（完整修复）
  - 问题1：使用COM接口转换时，Excel内容超出PDF页面边界，导致页面错乱
  - 问题2：列宽和行高为默认值，文字多的时候全都挤到一块
  - 问题3：系统安装WPS Office时，COM接口不兼容导致转换失败
  - 解决（COM接口）：
    - 在导出PDF前，先调用 `Columns.AutoFit()` 自动调整列宽
    - 调用 `Rows.AutoFit()` 自动调整行高
    - 根据内容实际宽度计算合适的缩放比例（限制在10%-400%，避免字太小）
    - 内容不宽时按100%显示，内容过宽时自动缩放适应页面
    - 设置页面方向为横向、纸张为A4
  - 解决（openpyxl方法）：
    - 添加WPS Office检测，检测到WPS时自动使用openpyxl方法
    - 根据内容长度计算自适应列宽（区分中英文字符宽度）
    - 如果总宽度超过页面宽度，按比例缩放所有列
    - 启用自动换行（WORDWRAP）避免文字截断
    - 使用左对齐（LEFT）更适合长文本显示
    - 减小页面边距（1cm），增加可用空间
  - 文件：`converters/excel_to_pdf.py`

- **修复**：PDF转图片重复输出问题
  - 问题：`convert_from_path` 使用 `output_folder` 参数会自动保存图片，代码又遍历 `images` 再次保存，导致每页输出两张图片
  - 解决：移除 `output_folder` 参数，让转换只在内存中进行，由代码统一保存
  - 文件：`converters/pdf_to_image.py` 第124-137行

### 2026-03-04
- **修复**：完成所有功能模块的验证和修复工作
  - 创建《功能开发进度.md》文档，详细记录25个功能模块的状态
  - 修复PDF去水印功能（converters/pdf_remove_watermark.py）
    - 实现基于颜色的水印检测和移除
    - 实现基于透明度的水印检测
    - 实现页眉页脚区域内容移除
    - 支持常见水印关键词检测（如"SAMPLE", "DRAFT", "机密"等）
    - 提供多种检测模式（颜色/位置/透明度/混合）
  - 修复文档转PDF功能（converters/doc_to_pdf.py）
    - 移除对已删除的html_to_pdf模块的引用
    - 从supported_input_formats中移除html/htm格式
  - 当前状态：25个功能全部完成（100%）
    - 文档转换类：12个功能全部完成
    - PDF处理类：13个功能全部完成

### 2026-02-26
- **新增**：13个新PDF处理模块框架文件（第一批开发）
  - 新增转换器（converters/）：
    1. pdf_extract_images.py - PDF提取图片
    2. pdf_add_remove_pages.py - PDF增删页
    3. pdf_rotate.py - PDF旋转页面
    4. pdf_organize.py - PDF编排页面
    5. pdf_to_long_image.py - PDF转长图
    6. pdf_to_grayscale.py - PDF转黑白
    7. pdf_add_page_numbers.py - PDF添加页码
    8. pdf_crop_split.py - PDF分割裁剪
    9. pdf_page_merge.py - PDF页面合并
    10. pdf_remove_watermark.py - PDF去水印
    11. pdf_add_watermark.py - PDF加水印
    12. pdf_encrypt.py - PDF加密
    13. invoice_merge.py - 发票合并
  - 新增页面（gui/pages/）：
    - 对应13个独立功能页面文件
  - 更新config/constants.py添加模块名称映射
  - 更新converters/__init__.py注册新转换器
  - 更新gui/pages/__init__.py导出新页面类
  - 更新gui/main_window.py集成新页面
  - 更新requirements.txt添加PyMuPDF依赖

## 行为准则！！！开发必须遵守

1.每次回复我的时候，都需要先以 muying 来称呼我

2.遇到不确定是否需要如此设计的代码时，需要向我先确认后进行

3.当对文件，系统等进行修改时，如果涉及到安全，包括可能导致生产事故，删除数据等行为时，需要先向我确认

4.**模块独立性原则**：每个功能模块的页面必须独立编写，使用独立的代码文件，而不是共用同一个界面。修改一个模块时，必须确保不影响其他模块的功能。各模块之间保持松耦合，界面UI可以相似，但代码实现必须分离。

5.每一次项目进度更新，或者产生了更改了项目结构等操作时，要将变更的内容更新到这个文件中，并提炼精简本文件内容

6.**自适应布局原则**：所有功能页面的设置面板必须使用自适应布局，确保在不同窗口大小下都能正常显示：
   - 使用 `QScrollArea` 包裹设置面板，允许内容滚动
   - 使用 `QGridLayout` 组织表单式设置，标签和控件分列对齐
   - 设置 `setSpacing()` 和 `setContentsMargins()` 控制间距
   - 避免将过多控件挤在同一行，合理分行分组
   - 控件设置合理的最小宽度（`setMinimumWidth`），避免过小
   - 设置面板分组使用 `QGroupBox`，每组内保持适当间距（10-12px）
   - 示例结构：
     ```python
     # 设置面板 - 使用滚动区域
     settings_scroll = QScrollArea()
     settings_scroll.setWidgetResizable(True)
     settings_scroll.setFrameShape(QFrame.Shape.NoFrame)

     settings_widget = QWidget()
     settings_layout = QVBoxLayout(settings_widget)
     settings_layout.setSpacing(12)

     # 基本设置组
     basic_group = QGroupBox("基本设置")
     basic_layout = QGridLayout(basic_group)
     basic_layout.setSpacing(10)
     basic_layout.setVerticalSpacing(8)

     # 第1行: 标签在第0列，控件在第1-2列
     basic_layout.addWidget(QLabel("输出目录:"), 0, 0)
     basic_layout.addWidget(self._output_dir_edit, 0, 1)
     basic_layout.addWidget(self._browse_btn, 0, 2)

     settings_layout.addWidget(basic_group)
     settings_scroll.setWidget(settings_widget)
     ```
---

    7.你的修改权限仅限于当前文件夹，默认情况下不允许对非此路径下的文件进行修改，如果在运行中需要修改别的路径的文件，需要征求我的意见，并获取我的授权
## 项目进展

### 当前状态：已完成 PyInstaller 打包，可独立运行

### 已完成的工作

#### 1. 项目基础框架
- [x] 项目目录结构创建
- [x] 配置模块（config/）
- [x] 转换器基类和任务调度器（core/）
- [x] 工具模块（utils/）
- [x] 依赖清单（requirements.txt）

#### 2. GUI界面框架
- [x] 主窗口（gui/main_window.py）- 支持页面切换
- [x] 公共UI组件（gui/widgets/）
- [x] QSS样式表（gui/styles/）
- [x] **独立功能页面目录（gui/pages/）**

#### 3. 独立功能页面（各模块代码完全分离）
- [x] **图片转PDF页面（gui/pages/image_to_pdf_page.py）** - 已完成
  - 独立拖拽上传组件
  - 独立文件列表管理
  - DPI和质量设置
  - 多图合并选项
  - 进度显示和取消功能
  - 后台线程转换
- [x] **PDF转图片页面（gui/pages/pdf_to_image_page.py）** - 已完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - DPI、输出格式、质量设置
  - 支持PNG/JPEG/BMP/TIFF格式输出
  - 进度显示和取消功能
  - 后台线程转换
- [x] **PDF转Excel页面（gui/pages/pdf_to_excel_page.py）** - 已完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 页码选择设置（支持范围和单页）
  - 表格提取和统计
  - 进度显示和取消功能
  - 后台线程转换
- [x] **PDF转Word页面（gui/pages/pdf_to_word_page.py）** - 已完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 页码范围设置（起始页/结束页）
  - 进度显示和取消功能
  - 后台线程转换
- [x] **Word转PDF页面（gui/pages/word_to_pdf_page.py）** - 已完成
  - 独立Word文件拖拽上传组件
  - 独立文件列表管理
  - 进度显示和取消功能
  - 后台线程转换
- [x] **Excel转PDF页面（gui/pages/excel_to_pdf_page.py）** - 已完成
  - 独立Excel文件拖拽上传组件
  - 独立文件列表管理
  - 页面方向设置（横向/纵向/自动）
  - 进度显示和取消功能
  - 后台线程转换
- [x] **通用文档转PDF页面（gui/pages/doc_to_pdf_page.py）** - 已完成
  - 独立文档拖拽上传组件（支持多文件和文件夹）
  - 自动识别文档类型（TXT、Word、Excel、PPT、HTML、图片、PDF）
  - 独立文件列表管理（添加、移除、清空）
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程转换
- [x] **PDF合并页面（gui/pages/pdf_merge_page.py）** - 已完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 文件排序功能（上移/下移按钮）
  - 输出文件名设置
  - 进度显示和取消功能
  - 后台线程合并
- [x] **TXT转PDF页面（gui/pages/txt_to_pdf_page.py）** - 已完成
  - 独立TXT文件拖拽上传组件
  - 独立文件列表管理
  - 字体大小和行高设置
  - 编码自动检测支持
  - 进度显示和取消功能
  - 后台线程转换
- [x] **PPT转PDF页面（gui/pages/ppt_to_pdf_page.py）** - 已完成
  - 独立PPT文件拖拽上传组件
  - 独立文件列表管理
  - 支持PPT/PPTX格式
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程转换
- [x] **PDF压缩页面（gui/pages/pdf_compress_page.py）** - 已完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 压缩级别选择（低/中/高）
  - 图片质量设置（30-100%）
  - 压缩前后大小对比显示
  - 进度显示和取消功能
  - 后台线程压缩
- [x] **PDF拆分页面（gui/pages/pdf_split_page.py）** - 已完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 三种拆分模式：单页拆分、页码范围拆分、奇偶页拆分
  - 进度显示和取消功能
  - 后台线程转换
- [x] **网页转PDF页面（gui/pages/web_to_pdf_page.py）** - 已完成
  - URL直接输入框（支持 http:// 和 https://）
  - HTML文件/URL文件拖拽上传（支持 .html, .htm, .url, .txt）
  - 独立URL/文件列表管理
  - 页面大小设置（A4、Letter、A3、A5、Legal）
  - 页面加载超时设置（10-300秒）
  - 进度显示和取消功能
  - 后台线程转换

#### 4. 转换器模块（converters/）
- [x] 原有13个转换器全部完成
- [x] 新增13个PDF处理转换器（框架已创建）

#### 5. 新增功能页面（gui/pages/）
- [x] **PDF提取图片页面** - 已完成
  - PDF文件拖拽上传，最小尺寸过滤，输出格式选择
- [x] **PDF增删页页面** - 已完成
  - 删除页面/插入空白页，页码范围设置
- [x] **PDF旋转页面** - 已完成
  - 90°/180°/270°旋转，页码范围设置
- [x] **PDF编排页面** - 已完成
  - 页面缩略图预览，拖拽排序
- [x] **PDF转长图页面** - 已完成
  - DPI设置，页面间隔，输出格式选择
- [x] **PDF转黑白页面** - 已完成
  - 灰度/二值化模式，阈值设置
- [x] **PDF添加页码页面** - 已完成
  - 位置/格式/起始页码/字体大小设置
- [x] **PDF分割裁剪页面** - 已完成
  - 裁剪边距设置，水平/垂直分割
- [x] **PDF页面合并页面** - 已完成
  - 2合1/4合1/6合1布局，间距和边框设置
- [x] **PDF去水印页面** - 已完成
  - 透明度阈值设置
- [x] **PDF加水印页面** - 已完成
  - 文字/图片水印，位置/透明度/旋转设置
- [x] **PDF加密页面** - 已完成
  - 打开密码/权限密码，权限设置
- [x] **发票合并页面** - 已完成
  - 文件排序，合并为单个PDF

### 待完成的工作

- [ ] 新增模块的功能测试
- [ ] 测试用例编写
- [ ] 错误处理优化
- [ ] 配置持久化功能

---

## 代码规范要求

所有代码文件必须遵循以下规范：

1. **模块文档字符串**：每个文件开头必须有详细的模块说明
2. **类文档字符串**：每个类必须有详细的属性说明和使用示例
3. **方法文档字符串**：每个方法必须有Args、Returns、Example说明
4. **变量命名**：使用下划线前缀表示私有成员（如 `_private_var`）
5. **日志记录**：关键操作必须有日志记录，错误必须记录详细信息
6. **类型注解**：所有公共方法必须有类型注解
7. **错误处理**：所有可能失败的操作必须有try-except，并提供有意义的错误信息

---

## PySide6/Qt UI开发注意事项

### 1. 布局问题：控件被挤出可视区域

**问题现象**：按钮或其他控件明明存在且visible=True，但界面上看不到。

**原因**：`QLineEdit`、`QTextEdit`等输入控件默认会无限扩展填充可用空间，将同一布局中的其他控件挤出可视区域。

**解决方案**：使用`stretch`参数控制空间分配，并为需要固定大小的控件设置固定尺寸。

```python
# 错误写法 - 按钮会被挤出
layout.addWidget(line_edit)
layout.addWidget(button)

# 正确写法 - 输入框填充剩余空间，按钮固定宽度
layout.addWidget(line_edit, 1)  # stretch=1，填充剩余空间
button.setFixedWidth(80)        # 固定按钮宽度
layout.addWidget(button)
```

### 2. 样式继承问题：控件样式未正确应用

**问题现象**：按钮文字颜色正确（白色），但背景颜色错误（白色），导致白字白底看不见。

**原因**：全局样式表设置了`QPushButton { color: white; background-color: #2196F3; }`，但某些情况下子控件可能无法正确继承父级样式，导致只继承了文字颜色而未继承背景颜色。

**解决方案**：对于关键按钮，显式设置完整的样式，确保样式正确应用。

```python
# 为按钮显式设置完整样式
self._browse_btn.setStyleSheet("""
    QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #1976D2;
    }
    QPushButton:pressed {
        background-color: #0D47A1;
    }
""")
```

### 3. 最佳实践总结

- **布局分配**：使用`addWidget(widget, stretch)`控制控件在布局中的空间占比
- **固定尺寸**：对于按钮等需要固定大小的控件，使用`setFixedWidth()`或`setFixedSize()`
- **显式样式**：关键控件应显式设置样式，避免依赖样式继承
- **调试技巧**：使用`widget.geometry()`检查控件位置和大小，使用`widget.palette().color()`检查颜色

---

## 重要提示

**当对项目架构模糊不清时，请查阅同路径下的 `planMode.md` 文件，其中包含完整的项目架构文档。**

---

## 运行方式

**正确的启动命令**（必须在项目根目录执行）：
```bash
cd C:\Users\muying\Desktop\pdfTools
python main.py
```

**注意**：不要直接运行 `converters/` 目录下的单个转换器文件，它们是模块组件而非入口文件。

---

## 更新日志

### 2026-02-27
- **打包**：完成 PyInstaller 打包配置
  - 移除 Playwright 依赖（网页转PDF功能）
  - 删除 `converters/html_to_pdf.py` 和 `gui/pages/web_to_pdf_page.py`
  - 创建 `pdf_tools.spec` 打包配置文件
  - 创建 `setup.iss` Inno Setup 安装程序配置
  - 打包体积：约 418MB
  - 输出目录：`dist/PDF工具箱/`
  - 可执行文件：`PDF工具箱.exe`

### 2026-02-27
- **优化**：为7个页面模块添加"打开输出目录"功能按钮
  - txt_to_pdf_page.py - 添加橙色"打开"按钮和 `_open_output_folder` 方法
  - ppt_to_pdf_page.py - 添加橙色"打开"按钮和 `_open_output_folder` 方法
  - pdf_merge_page.py - 添加橙色"打开"按钮和 `_open_output_folder` 方法
  - pdf_compress_page.py - 添加橙色"打开"按钮和 `_open_output_folder` 方法
  - pdf_split_page.py - 添加蓝色"打开"按钮和 `_open_output_folder` 方法
  - web_to_pdf_page.py - 添加橙色"打开"按钮和 `_open_output_folder` 方法
  - pdf_extract_images_page.py - 添加蓝色"打开"按钮和 `_open_output_folder` 方法
  - 功能：点击"打开"按钮可在系统文件管理器中打开输出目录
  - 支持跨平台：Windows(explorer)、macOS(open)、Linux(xdg-open)

### 2026-02-26
- **新增**：PDF拆分页面（gui/pages/pdf_split_page.py）开发完成
  - 独立PDF拖拽上传组件，支持单文件和文件夹批量添加
  - 独立文件列表管理（添加、移除、清空、右键菜单）
  - 三种拆分模式：
    1. 单页拆分：每页拆分为一个独立PDF文件
    2. 页码范围拆分：按指定范围拆分（如 1-3,5-10,15）
    3. 奇偶页拆分：拆分为奇数页和偶数页两个文件
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程拆分（不阻塞UI）
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：PDF压缩页面（gui/pages/pdf_compress_page.py）开发完成
  - 独立PDF拖拽上传组件，支持单文件和文件夹批量添加
  - 独立文件列表管理（添加、移除、清空、右键菜单）
  - 压缩级别选择：低压缩（保持质量）、中等压缩（推荐）、高压缩（减小体积）
  - 图片质量设置（30-100%）
  - 压缩前后大小对比显示
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程压缩（不阻塞UI）
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：网页转PDF页面（gui/pages/web_to_pdf_page.py）开发完成
  - URL直接输入框，支持 http:// 和 https:// 开头的网址
  - HTML文件/URL文件拖拽上传，支持 .html、.htm、.url、.txt 格式
  - 独立URL/文件列表管理（添加、移除、清空、右键菜单）
  - 页面大小设置（A4、Letter、A3、A5、Legal）
  - 页面加载超时设置（10-300秒）
  - 进度显示和取消功能
  - 后台线程转换（不阻塞UI），基于 Playwright 实现网页渲染
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：PPT转PDF页面（gui/pages/ppt_to_pdf_page.py）开发完成
  - 独立PPT文件拖拽上传组件，支持 PPT、PPTX 格式
  - 独立文件列表管理（添加、移除、清空、右键菜单）
  - 支持文件夹批量添加
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程转换（不阻塞UI）
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：TXT转PDF页面（gui/pages/txt_to_pdf_page.py）开发完成
  - 独立TXT文件拖拽上传组件，支持 UTF-8、GBK、GB2312 等常见编码格式
  - 独立文件列表管理（添加、移除、清空、右键菜单）
  - 字体大小设置（8-72pt）
  - 行高倍数设置（1.0-3.0）
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程转换（不阻塞UI）
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：PDF合并页面（gui/pages/pdf_merge_page.py）开发完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 文件排序功能（上移/下移按钮），可调整合并顺序
  - 输出文件名设置
  - 进度显示和取消功能
  - 后台线程合并
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：通用文档转PDF页面（gui/pages/doc_to_pdf_page.py）开发完成
  - 独立文档拖拽上传组件，支持多文件和文件夹
  - 自动识别多种文档类型：TXT、Word（DOC/DOCX）、Excel（XLS/XLSX）、PowerPoint（PPT/PPTX）、HTML、图片（JPG/PNG等）、PDF
  - 独立文件列表管理（添加、移除、清空、右键菜单）
  - 输出目录设置
  - 进度显示和取消功能
  - 后台线程转换（不阻塞UI）
  - 集成到主窗口和pages包

### 2026-02-26
- **新增**：Excel转PDF页面（gui/pages/excel_to_pdf_page.py）开发完成
  - 独立Excel文件拖拽上传组件
  - 独立文件列表管理
  - 页面方向设置（横向/纵向/自动）
  - 进度显示和取消功能
  - 后台线程转换
  - 配置中新增EXCEL_EXTENSIONS常量

### 2026-02-26
- **新增**：Word转PDF页面（gui/pages/word_to_pdf_page.py）开发完成
  - 独立Word文件拖拽上传组件
  - 独立文件列表管理
  - 进度显示和取消功能
  - 后台线程转换

### 2026-02-26
- **新增**：PDF转Word页面（gui/pages/pdf_to_word_page.py）开发完成
  - 独立PDF拖拽上传组件
  - 独立文件列表管理
  - 页码范围设置（起始页/结束页）
  - 进度显示和取消功能
  - 后台线程转换

### 2026-02-26
- **修复**：图片转PDF页面"浏览..."按钮不可见问题
  - 原因1：QLineEdit默认扩展填充所有空间，将按钮挤出可视区域
  - 原因2：按钮文字为白色，但背景也是白色（样式表未正确继承）
  - 解决：
    1. 为QLineEdit设置stretch=1，为浏览按钮设置固定宽度80px
    2. 为浏览按钮显式设置样式（蓝色背景+白色文字）