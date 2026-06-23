# 笔记导入导出与跨平台迁移策略

## 1. 文档目的

本文档描述 Personal Wiki Agent 如何处理有道云笔记、语雀、飞书、Notion、Obsidian 等笔记系统之间的导入、导出、镜像和迁移。

核心结论：

- 可以把 Markdown、HTML、DOCX、PDF、CSV、JSON 等格式作为跨笔记 App 的迁移桥梁。
- Markdown 适合作为个人知识库的主要中间格式。
- 富文本、附件、评论、权限、历史版本、数据库字段和平台特有 block 通常无法无损迁移。
- 系统应设计统一的导入导出 adapter，而不是为每个平台写一套散乱逻辑。

## 2. 与 Connector 的关系

Connector 负责把外部数据源同步到本地知识库。

Export / Import 负责把本地资料、Agent 整理结果、摘要、主题地图或用户确认的知识条目导出为可迁移格式，或者写入目标笔记 App。

两者边界如下：

```text
外部笔记 App -> Connector -> Document / Chunk / Source -> 本地索引

本地资料 / Agent 整理结果 -> Export Adapter -> Markdown / HTML / DOCX / 目标平台 block -> 目标笔记 App
```

云端笔记 API 是同步入口，不是 Agent 每次问答时的临时搜索外挂。导出和写回也必须由用户显式触发，不默认自动上传本地资料。

## 3. 格式优先级

### 3.1 Markdown + assets

默认推荐格式：

```text
content.md
assets/
metadata.json
```

优势：

- 可读、可编辑、可长期保存。
- 适合 Obsidian、Git、全文检索、RAG 和版本管理。
- 大多数标题、段落、列表、代码块、链接和图片引用都可以表达。
- 便于后续导入 Notion、Obsidian、语雀、飞书等工具。

限制：

- 复杂表格、嵌入式数据库、评论、权限、历史版本和某些富文本样式可能丢失。
- 不同平台的 Markdown 方言不同，需要转换和校验。

### 3.2 HTML + assets

适合保留更多富文本结构：

- 更容易保留颜色、部分布局、内联样式和复杂网页剪藏。
- 适合从网页、富文本笔记或部分云端笔记导出。

限制：

- 解析和清洗成本更高。
- 不适合作为长期主格式。
- 导入不同平台后样式可能被重写。

### 3.3 DOCX

适合作为富文本桥接格式：

- 很多笔记 App 和在线文档工具支持 Word 文档导入。
- 对标题、段落、列表、图片、普通表格支持较好。

限制：

- 不适合做本地知识库长期主格式。
- 版本管理和差异比较不友好。
- 复杂样式导入后可能变形。

### 3.4 PDF

适合归档和视觉保真：

- 适合保留最终版资料、合同、论文、报告、课程讲义。
- 适合作为不可编辑归档。

限制：

- 不适合作为可编辑迁移格式。
- 文本抽取、结构还原和引用定位需要额外解析。

### 3.5 CSV / JSON

适合结构化数据：

- 表格、数据库条目、标签、目录、属性字段、任务状态。
- `metadata.json` 可保留平台特有信息。

限制：

- 不适合承载长文正文。
- 需要和 Markdown / HTML 正文一起组成迁移包。

## 4. 标准迁移包

Personal Wiki Agent 应定义一个平台无关的标准迁移包：

```text
note-package/
  content.md
  assets/
    image-001.png
    attachment-001.pdf
  metadata.json
  original/
    source.html
    source.docx
```

`content.md` 保存主正文。

`assets/` 保存图片、附件、PDF、音视频或其他资源。

`metadata.json` 保存平台特有信息：

```json
{
  "source_platform": "youdao",
  "target_platform": "obsidian",
  "remote_id": "remote-note-id",
  "title": "笔记标题",
  "created_at": "2026-06-23T10:00:00+08:00",
  "updated_at": "2026-06-23T10:00:00+08:00",
  "tags": ["RAG", "个人知识库"],
  "folder_path": ["学习", "AI", "RAG"],
  "source_url": "https://example.com/original-note",
  "attachments": [
    {
      "name": "image-001.png",
      "path": "assets/image-001.png",
      "mime_type": "image/png"
    }
  ],
  "original_format": "html",
  "export_format": "markdown",
  "content_hash": "sha256-value",
  "conversion_warnings": []
}
```

`original/` 可选保存原始导出文件，便于后续重新转换或人工核对。

## 5. 平台策略

### 5.1 Obsidian

Obsidian 是最适合作为本地长期知识库载体的平台之一。

策略：

- 直接把 Markdown 文件和 assets 放入 vault。
- 保留 `front matter`、标签、双链、附件关系。
- 使用 Obsidian 风格 Markdown 时，需要注意 wikilink、embed、callout、tag 等方言。

适合场景：

- 本地优先。
- 长期保存。
- 换机迁移。
- Git 版本管理。
- Agent 直接扫描和索引。

参考依据：

- Obsidian 官方说明其主要笔记格式是本地 Markdown 文件。
- Obsidian 支持导入 Markdown 文件到 vault。

## 5.2 Notion

Notion 适合作为云端协作和跨设备知识库载体。

策略：

- 导入方向：优先使用 Markdown、HTML、DOCX 或 ZIP。
- 导出方向：优先导出 Markdown & CSV 或 HTML。
- 对 database、表格和属性字段，需要用 CSV / JSON 保存结构化信息。

适合场景：

- 跨设备云端查看。
- 协作和分享。
- 将 Agent 整理结果发布为可读页面。

注意事项：

- Notion database、评论、权限、页面历史和复杂 block 无法完全用 Markdown 表达。
- 大量文件导入导出需要分批处理。

参考依据：

- Notion 官方文档说明可导入 `.txt`、`.md/.markdown`、`.docx`、`.csv`、`.html`、`.pdf`、`.zip` 等文件。
- Notion 官方文档说明可导出 HTML、Markdown & CSV、PDF。

## 5.3 有道云笔记

有道云笔记是本项目第一批云端 connector 的优先目标，因为用户历史笔记主要沉淀在有道云笔记中。

策略：

- 优先验证本地同步目录、导出文件、本地缓存和官方 API 是否能稳定获得笔记正文。
- 如果能导出 Markdown / HTML / DOCX，应优先转成标准迁移包。
- 如果只能获得富文本或 HTML，应先转成 HTML + assets，再转换为 Markdown。
- 附件、图片、网页剪藏和笔记本层级必须作为第一批验证重点。

适合场景：

- 历史笔记迁移。
- 从有道云笔记同步到本地知识库。
- 将重要笔记逐步镜像到 Obsidian、Notion、语雀或飞书。

待验证事项：

- 官方 API 当前可用范围。
- 是否支持批量导出。
- 导出格式是否包含 Markdown、HTML、DOCX 或专有格式。
- 附件和图片是否能完整导出。
- 导出内容是否保留创建时间、更新时间、标签和目录。

## 5.4 语雀

语雀适合作为结构化知识库和在线文档载体。

策略：

- 优先验证 Markdown、HTML、DOCX 导入导出能力。
- 语雀知识库目录结构应映射到 `folder_path` 或 `collection_path`。
- 文档 slug、知识库 ID、标签和更新时间应写入 `metadata.json`。

适合场景：

- 知识库文章。
- 学习资料整理。
- Agent 生成的主题文章或知识条目发布。

待验证事项：

- 当前导入导出格式。
- API 是否能获取 Markdown 或 HTML 正文。
- 附件、图片、目录、评论是否可迁移。

## 5.5 飞书

飞书适合作为工作协作型文档平台。

策略：

- 优先验证飞书文档的导入、导出和 OpenAPI 能力。
- 对飞书文档、知识库、多维表格应区分处理。
- 普通文档优先转 Markdown / HTML / DOCX；表格和多维表格优先转 CSV / JSON。

适合场景：

- 工作资料。
- 团队文档。
- Agent 生成的项目总结、周报、任务清单。

待验证事项：

- 是否支持稳定导入 Markdown、HTML、DOCX。
- 是否支持导出 Markdown、HTML、DOCX 或 PDF。
- OpenAPI 是否支持创建文档、写入 block、上传附件和读取文档结构。

## 6. Adapter 抽象

系统应预留以下接口：

```text
NoteExportAdapter
  export_document(document_id, target_format)
  export_collection(source_id, target_format)
  export_agent_result(result_id, target_format)

NoteImportAdapter
  import_package(package_path, target_source_id)
  import_markdown(markdown_path, target_source_id)
  import_html(html_path, target_source_id)

FormatConverter
  html_to_markdown(html, assets)
  docx_to_markdown(docx_path)
  markdown_to_html(markdown)
  markdown_to_platform_blocks(markdown, target_platform)
```

平台实现示例：

```text
YoudaoExportAdapter
NotionImportAdapter
ObsidianVaultImportAdapter
YuqueImportAdapter
FeishuImportAdapter
```

业务层只依赖统一接口，不直接写平台特定逻辑。

## 7. 典型流程

### 7.1 从有道云笔记迁移到 Obsidian

```text
有道云笔记导出 / 同步 / API
-> 解析为 Document
-> 转为 Markdown + assets + metadata.json
-> 写入 Obsidian vault
-> 建立 source / document / mirror 映射
-> 触发本地索引
```

### 7.2 从本地资料整理到 Notion

```text
用户选择本地资料或 Agent 整理结果
-> Agent 生成摘要 / 主题地图 / 知识条目
-> 导出为 Markdown package
-> NotionImportAdapter 写入 Notion 页面
-> 记录 mirror_uri 和 remote_id
```

### 7.3 从飞书或语雀导入知识库

```text
用户配置导出目录或 API token
-> Connector 拉取正文和元数据
-> 转成标准 Document
-> 生成可选迁移包
-> 写入本地索引
```

## 8. 迁移质量分级

迁移结果应记录质量等级：

- `lossless`：几乎无损，正文、标题、图片、附件和元数据都保留。
- `minor_loss`：轻微损失，例如颜色、字体、部分样式丢失。
- `structure_loss`：结构损失，例如复杂表格、数据库字段、目录层级部分丢失。
- `content_loss`：正文、图片或附件缺失，需要人工处理。
- `unsupported`：当前平台或格式暂不支持。

每次迁移应保存 `conversion_warnings`，让用户知道哪些内容可能丢失。

## 9. 安全与隐私边界

导出和写回必须遵守以下边界：

- 默认不自动上传本地资料。
- 上传前必须由用户显式选择目标平台和目标位置。
- 敏感目录、忽略规则和私密文件必须继续生效。
- 导出前应支持预览。
- 大批量迁移前应支持 dry-run。
- 写入目标平台后要记录 `remote_id`、`mirror_uri` 和 `mirror_status`。
- 失败时不能影响本地知识库。

## 10. MVP 建议

MVP 不需要一开始实现所有平台互导。

建议顺序：

1. 定义标准迁移包格式。
2. 支持从 Document 导出 Markdown + assets + metadata.json。
3. 支持把 Agent 整理结果导出为 Markdown。
4. 支持写入 Obsidian vault 或普通本地目录。
5. 验证有道云笔记导出 / 同步 / API 能力。
6. 后续再做 Notion、语雀、飞书的 import adapter。

这样既能先服务真实历史资料，又不会把项目绑死在某个平台上。

## 11. 验收标准

第一版导入导出能力完成时，应满足：

1. 任意已索引 Document 可以导出为 Markdown + assets + metadata.json。
2. Agent 生成的摘要、主题地图和知识条目可以导出为 Markdown。
3. 导出包能保留标题、正文、来源、标签、目录、附件映射和时间信息。
4. 用户能看到迁移质量和可能丢失的内容。
5. 导出和写回默认不自动上传，必须用户确认。
6. Obsidian vault 可以作为第一批本地导入目标。
7. 有道云笔记的导出、同步目录或 API 能力完成验证记录。
8. 后续新增 Notion、语雀、飞书时，只新增 adapter，不改核心导出流程。

## 12. 参考来源

- Notion 导入文档：https://www.notion.com/help/import-data-into-notion
- Notion 导出文档：https://www.notion.com/help/export-your-content
- Obsidian Markdown 导入文档：https://help.obsidian.md/import/markdown
- Obsidian 导入总览：https://help.obsidian.md/import
