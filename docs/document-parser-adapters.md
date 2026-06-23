# 文档解析 Adapter 设计

## 1. 文档目的

本文档描述 Personal Wiki Agent 的文档解析层如何支持不同文件类型，以及如何复用成熟开源项目，避免重复造轮子。

核心原则：

**项目自己定义 Parser 接口和统一 ParseResult，但具体文件格式解析优先接入成熟开源库。**

外部解析器负责把文件内容提取出来；本项目负责来源追踪、标准文档模型、分块、索引、权限、缓存和 Agent 使用方式。

## 2. 为什么不能全部自研解析器

个人知识库会遇到大量文件类型：

- Markdown
- txt
- PDF
- docx
- HTML
- PPTX
- XLSX
- EPUB
- 邮件
- 图片
- 扫描件
- 表格
- 手写笔记
- 公众号文章保存件

其中 PDF、Office、扫描件、图片 OCR、表格、公式和复杂版面都很难从零做好。

如果全部自研，会带来：

- 解析质量差。
- 格式覆盖慢。
- 维护成本高。
- 很难处理 OCR、表格、公式、版面顺序。
- 后续替换困难。

因此解析层必须从一开始设计成 adapter 模式。

## 3. 总体架构

```text
文件路径 / 远程附件
-> 文件类型识别
-> ParserRouter
-> ParserAdapter
-> ParseResult
-> Document / Chunk
-> Indexing
```

Parser 层只做解析，不直接写索引。

索引层只消费标准化后的 `ParseResult` 或 `Document`，不关心底层使用的是 PyMuPDF、MarkItDown、Docling、unstructured 还是 marker。

## 4. ParserAdapter 接口

建议定义统一接口：

```text
ParserAdapter
  can_parse(file_path, mime_type, metadata) -> bool
  parse(file_path, options) -> ParseResult
  supported_extensions() -> list[str]
  supported_mime_types() -> list[str]
  cost_level() -> low | medium | high
  quality_level() -> basic | structured | advanced
```

建议实现：

```text
MarkdownParser
TextParser
PyMuPdfParser
PythonDocxParser
HtmlReadabilityParser
MarkItDownParser
DoclingParser
UnstructuredParser
MarkerParser
OcrParser
ImageVisionParser
```

MVP 只实现前几个轻量 parser，但保留 adapter 接口。

## 5. ParseResult 模型

所有 parser 必须输出统一结果。

建议字段：

```text
title
text
markdown
sections
page_map
tables
images
links
metadata
warnings
parser_name
parser_version
quality_score
```

字段说明：

- `text`：纯文本内容，保证可索引。
- `markdown`：带结构的 Markdown 内容，适合 LLM 和 chunk。
- `sections`：标题层级和段落结构。
- `page_map`：PDF 页码或文档位置映射。
- `tables`：结构化表格。
- `images`：图片路径、描述、OCR 结果。
- `warnings`：解析失败、OCR 跳过、附件缺失等信息。
- `quality_score`：用于后续判断是否需要更强 parser 重新解析。

## 6. 开源解析器候选

### 6.1 MarkItDown

仓库：

- [microsoft/markitdown](https://github.com/microsoft/markitdown)

定位：

- 轻量 Python 工具。
- 将多种文件转成 Markdown，面向 LLM 和文本分析管线。

适合：

- 作为通用 fallback parser。
- 快速支持 PDF、Word、PowerPoint、Excel、HTML、CSV、JSON、XML、EPUB、ZIP 等。
- 输出 Markdown，方便后续 chunk 和 LLM 使用。

注意：

- 不是高保真文档转换工具。
- 复杂 PDF、扫描件、表格和版面质量可能不如专业文档智能工具。
- 引入前需要按文件类型选择 extras，避免依赖过重。

### 6.2 Docling

仓库：

- [docling-project/docling](https://github.com/docling-project/docling)

定位：

- 文档智能解析工具包。
- 支持多种格式和高级 PDF 理解。

适合：

- 复杂 PDF。
- 表格结构。
- 版面分析。
- OCR。
- Office、HTML、EPUB、邮件、图片等更多格式。
- 需要本地执行和较高解析质量的场景。

注意：

- 能力强于轻量 parser，但依赖和资源成本也更高。
- 适合作为增强 parser，不建议 MVP 一开始强制依赖。

### 6.3 unstructured

仓库：

- [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured)

定位：

- 非结构化数据 ingestion 和 pre-processing 工具。
- 面向 LLM 数据处理工作流。

适合：

- 多格式 ingestion。
- 需要统一 partition 管线。
- 后续处理更多企业文档、邮件、复杂附件时。

注意：

- 依赖较多。
- Windows 环境可能需要额外系统依赖。
- 适合作为后续增强 adapter，而不是 MVP 默认必装。

### 6.4 marker

仓库：

- [datalab-to/marker](https://github.com/datalab-to/marker)

定位：

- 将 PDF、图片、PPTX、DOCX、XLSX、HTML、EPUB 等转换为 Markdown、JSON、chunks、HTML。
- 强调 PDF、OCR、表格、公式、图片提取和结构化输出。

适合：

- 高质量 PDF 到 Markdown。
- 扫描件 OCR。
- 复杂表格、公式、论文资料。
- 需要输出 chunks 或结构化 JSON 的场景。

注意：

- 依赖 PyTorch，资源成本更高。
- 代码许可证和模型许可证需要谨慎评估。
- 适合作为高质量增强 parser，不建议默认作为 MVP 必装。

## 7. MVP 推荐策略

MVP 不需要一开始引入所有解析器。

默认实现：

- Markdown / txt：项目内轻量 parser。
- PDF：PyMuPDF。
- docx：python-docx。
- HTML：BeautifulSoup + readability 类解析器。

可选 fallback：

- MarkItDownParser。

MVP 目标：

- 先覆盖最常见个人资料。
- 解析结果稳定可索引。
- 保留来源和页码信息。
- 保留 adapter 接口，后续无痛接入 Docling / unstructured / marker。

## 8. 后续增强策略

### 8.1 多格式扩展

当用户需要更多文件类型时，优先接入 MarkItDown 或 unstructured。

适合扩展：

- pptx
- xlsx
- csv
- json
- xml
- epub
- eml / msg
- zip

### 8.2 复杂 PDF 增强

当 PDF 解析质量不足时，优先评估 Docling 或 marker。

触发场景：

- 多栏论文阅读顺序错误。
- 表格被解析成乱序文本。
- 扫描件无文本。
- 数学公式、代码块、脚注大量丢失。
- 图片说明和图表内容对理解很重要。

### 8.3 OCR 和图片理解

OCR 和图片理解不应在 MVP 默认开启。

触发场景：

- 扫描 PDF 占比较高。
- 图片中包含重要文字。
- 手写笔记需要纳入知识库。
- 图表、流程图、截图需要被检索。

可选方案：

- Docling OCR。
- marker OCR。
- Tesseract。
- PaddleOCR。
- LLM Vision。

## 9. Parser 路由策略

ParserRouter 应根据文件类型、质量要求和资源成本选择 parser。

建议策略：

```text
md/txt -> MarkdownParser / TextParser
pdf -> PyMuPdfParser
docx -> PythonDocxParser
html -> HtmlReadabilityParser
unknown/common office -> MarkItDownParser
complex pdf/scanned pdf -> DoclingParser or MarkerParser
large mixed corpus -> UnstructuredParser
```

如果基础 parser 输出质量差，可以标记 `quality_score` 较低，后续由用户或后台任务触发高质量重解析。

## 10. 缓存与重解析

解析结果应缓存，避免每次索引都重复解析。

缓存键建议：

```text
source_id
document_id
content_hash
parser_name
parser_version
parser_options_hash
```

当以下内容变化时需要重新解析：

- 文件内容变化。
- parser 版本变化。
- parser 配置变化。
- 用户手动选择更高质量解析。
- OCR / 图片理解开关变化。

## 11. 依赖和安装策略

解析器依赖分层安装。

MVP 基础依赖：

- PyMuPDF
- python-docx
- beautifulsoup4
- readability 类库

可选依赖：

- markitdown
- docling
- unstructured
- marker-pdf
- OCR 相关库

原则：

- 不默认安装所有重依赖。
- 用 extras 或可选 dependency group 管理。
- UI / CLI 应能提示某类文件需要安装哪个 parser extra。
- Windows 环境要特别注意系统依赖、OCR 依赖和二进制包。

## 12. 许可证与隐私

引入外部解析器前必须检查：

- 开源许可证。
- 模型许可证。
- 是否允许商业使用。
- 是否需要联网。
- 是否会上传文档内容。
- 是否支持完全本地运行。

隐私原则：

- 默认使用本地 parser。
- 云端 OCR、云端文档理解、LLM Vision 必须用户显式启用。
- 对敏感目录和私密文件，禁止自动调用云端解析服务。

特别注意：

- marker 的代码和模型许可证需要单独评估。
- 云端文档智能服务不应作为默认解析路径。

## 13. 解析质量评估

后续应建立小型解析评测集。

样本类型：

- 普通 PDF。
- 扫描 PDF。
- 多栏论文。
- 带表格的 PDF。
- Word 文档。
- 网页文章。
- 公众号保存件。
- Obsidian Markdown。

评估指标：

- 文本完整度。
- 标题层级是否正确。
- 页码映射是否可用。
- 表格是否可读。
- 链接是否保留。
- 图片和 OCR 是否合理。
- chunk 后是否适合检索。

## 14. 演进触发器

当出现以下情况时，应评估引入增强 parser：

- 某类文件解析失败率明显偏高。
- PDF 中表格、公式、脚注或多栏内容经常丢失。
- 用户频繁上传扫描件或图片型资料。
- 检索结果经常命中文档但答案缺少关键上下文。
- 需要支持 pptx、xlsx、epub、eml、msg 等更多格式。
- 用户希望把解析结果导出为高质量 Markdown。

升级时先增加新的 `ParserAdapter`，不要替换上层 Document / Chunk / Indexing 流程。

## 15. 验收标准

解析层第一版完成时应满足：

1. 每种文件格式通过 ParserAdapter 接入。
2. Parser 输出统一 ParseResult。
3. 基础 parser 可以覆盖 Markdown、txt、PDF、docx、HTML。
4. 解析结果可以保留来源、标题、页码或位置映射。
5. parser 失败不会阻断整个索引任务。
6. 系统能记录 parser 名称、版本、警告和质量信息。
7. 后续新增 MarkItDown、Docling、unstructured、marker 不需要改动索引层和 Agent 层。

## 16. 关键结论

文档解析层应采用：

```text
统一接口
多 parser adapter
轻量 MVP
增强 parser 可插拔
解析结果标准化
```

这样既能快速完成 MVP，也能在后续面对复杂文件类型时复用成熟开源项目，而不需要推翻整体架构。

