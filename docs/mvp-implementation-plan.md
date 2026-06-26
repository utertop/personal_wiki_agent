# Personal Wiki Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不推翻长期架构的前提下，完成一个本地优先、可检索、可引用、可对话的个人知识库 Agent MVP。

**Architecture:** MVP 是长期九层架构上的最小垂直切片：数据源通过 Connector 接入，内容经 Parser 转为 Document / Chunk / Source，索引层提供关键词与向量接口，检索层做 hybrid search，回答层生成带来源引用的答案，Agent 工具层暴露稳定工具，前端采用对话式 Web UI。第一版功能可以少，但层边界必须稳定。

**Tech Stack:** Python 3.11+、FastAPI、Pydantic、SQLAlchemy、Alembic、SQLite、SQLite FTS5、PyMuPDF、python-docx、BeautifulSoup/readability、OpenAI-compatible API、Ollama、React + Vite + TypeScript。

## Global Constraints

- 项目不直接 fork Khoj、Onyx、Quivr、Mem0，先做自己的轻量 MVP。
- 所有 Markdown 文档新增和修改默认使用中文，代码标识、库名、API 名称、文件名等特定名词可以保留英文。
- Markdown 文件必须使用 UTF-8，并避免 Windows / PowerShell 环境下中文显示乱码。
- 文档知识库与长期记忆必须分开存储、分开索引、分开检索、合并使用。
- 云端笔记 API 只作为同步入口，不作为 Agent 每次问答时的临时搜索外挂。
- 第一批云端 connector 优先有道云笔记，但不进入 MVP 必做闭环。
- 前端主体验必须是对话式 Agent 工作台，配置能力收纳到侧栏、设置页或抽屉。
- 知识库问答必须尽量带来源引用，无法找到来源时必须明确说明。
- 关键词检索必须通过 `LexicalIndex` 接口隔离，不在业务层直接绑定 SQLite FTS5。
- 模型能力必须通过 `ModelProvider`、`ModelRegistry`、`ModelCatalog`、`ModelRouter` 管理，业务代码不写死模型名。
- 文档解析必须通过 `ParserAdapter` 接口接入具体解析器。
- 修改需求、范围、架构、工期、验收标准或开发约束后，必须执行文档一致性体检。

---

## 1. 计划使用方式

本文档是 MVP 执行跟踪文档。后续开发时按任务顺序推进，每个任务完成后更新状态、补充实际结果，并在必要时同步更新设计文档。

推荐状态标记：

- `[ ]` 未开始。
- `[~]` 进行中。
- `[x]` 已完成。
- `[!]` 有风险或被阻塞。

每个任务完成时至少要留下：

- 已修改文件。
- 验证命令和结果。
- 是否影响 README、`docs/technical-direction.md`、`docs/project-design.md`、`rules.md` 或专项文档。
- 下一步任务。

## 2. MVP 完成后的效果

MVP 完成后，用户应该能做到：

1. 在配置文件中声明多个本地知识目录和笔记 App 本地同步目录。
2. 系统能扫描 Markdown、txt、PDF、docx、HTML 文件。
3. 系统能解析文件并生成标准 `Source`、`Document`、`Chunk` 数据。
4. 系统能增量识别新增、修改、删除和移动。
5. 系统能建立 SQLite 元数据索引和 SQLite FTS5 关键词索引。
6. 系统保留向量索引、embedding 和模型 provider 的替换接口。
7. 用户能通过搜索接口检索资料，并看到来源信息。
8. 用户能通过对话接口获得带来源引用的回答。
9. Agent 工具能调用 `search_notes`、`open_source`、`summarize_folder`、`build_topic_map`。
10. 用户能通过对话式 Web UI 提问、查看引用、打开来源详情。
11. 本地索引、缓存和向量库可重建，不被视为唯一知识主副本。
12. 项目文档和代码结构保持一致，后续可以继续接入有道云笔记、长期记忆增强、导入导出和自动化能力。

## 3. 不进入 MVP 的内容

以下内容暂不进入第一版 MVP：

- 企业级多用户、团队权限、RBAC。
- 移动端。
- 大规模云端部署。
- 完整有道云笔记云端 API connector。
- 多云端笔记平台同时接入。
- 自动写回云端笔记。
- 完整 Mem0 接入。
- OCR、图片理解、复杂扫描件 PDF 结构化。
- 高级主题图谱可视化。
- 自动长期任务调度和复杂工作流。

这些能力需要在 MVP 闭环稳定后，按专项文档逐步演进。

## 4. 里程碑总览

| 里程碑 | 目标 | 预计周期 | 完成判定 |
| --- | --- | --- | --- |
| M0 | 项目骨架 | 第 1 周 | 后端可启动，`GET /health` 可用，测试可运行 |
| M1 | 本地数据源接入 | 第 2 周 | 能配置多个本地目录并生成 source/document 记录 |
| M2 | 文档解析闭环 | 第 3 周 | Markdown、txt、PDF、docx、HTML 可解析为标准文本 |
| M3 | 索引闭环 | 第 4 周 | SQLite 元数据、FTS5、chunk、索引任务状态可用 |
| M4 | 检索与引用 | 第 5 周 | `POST /search` 返回带来源的检索结果 |
| M5 | 问答闭环 | 第 6 周 | `POST /chat` 能基于检索结果生成带引用回答 |
| M6 | Agent 工具 | 第 7 周 | 核心工具可通过 API 或内部接口调用 |
| M7 | 对话式 Web UI | 第 8 周 | 用户能在 Web UI 中提问、查看引用和来源详情 |
| M8 | Alpha 准备 | 第 9 到 12 周 | 长期记忆、有道云笔记验证、自动 digest 初版进入下一阶段 |

## 5. 执行任务清单

### Task 1: 项目工程骨架

**目标：** 建立后端项目的最小可运行结构，形成后续所有模块的稳定落点。

**文件：**

- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/logging.py`
- Create: `backend/app/core/errors.py`
- Create: `backend/app/api/routes_health.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/pyproject.toml`
- Create: `backend/README.md`

**产出接口：**

- `create_app() -> FastAPI`
- `GET /health -> {"status": "ok"}`

**步骤：**

- [x] 创建 `backend/` 目录和 Python 包结构。
- [x] 在 `pyproject.toml` 中声明 FastAPI、Pydantic、pytest、httpx 等基础依赖。
- [x] 实现 `create_app()`，只注册 health 路由。
- [x] 编写 `tests/test_health.py`，验证 `/health` 返回 `200` 和 `status=ok`。
- [x] 运行 `pytest`，确认测试通过。
- [x] 更新 README 中的本地启动方式。

执行记录：

- 分支：`feat/project-skeleton`。
- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_health.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app'`。
- 绿灯：同一命令通过，结果为 `1 passed`。
- 环境说明：当前机器只检测到 Python 3.8.8，因此本次本地验证使用临时 `.venv` 跑通；项目目标版本仍为 Python 3.11+，后续正式开发环境需要升级到 Python 3.11 或更高版本。

**验收标准：**

- `python -m pytest` 可以运行。
- `GET /health` 返回成功。
- 项目结构和 `docs/project-design.md` 推荐结构一致。

### Task 2: 配置系统

**目标：** 支持本地目录、忽略规则、模型配置和数据目录配置，为后续 connector 与 model provider 提供统一入口。

**文件：**

- Create: `config/sources.example.yaml`
- Create: `backend/app/core/settings.py`
- Create: `backend/app/core/paths.py`
- Create: `backend/tests/test_settings.py`

**产出接口：**

- `AppSettings`
- `SourceConfig`
- `load_settings(config_path: Path | None) -> AppSettings`

**步骤：**

- [x] 定义 `AppSettings`，包含 `data_dir`、`database_url`、`sources`、`model`、`privacy`。
- [x] 定义 `SourceConfig`，支持 `local_directory`、`local_synced_notes`、`obsidian_vault`。
- [x] 编写 `sources.example.yaml`，包含本地目录、笔记 App 本地同步目录、Obsidian vault 示例和忽略规则示例。
- [x] 实现配置读取和默认值。
- [x] 测试缺省配置、示例配置、非法 source 类型。

执行记录：

- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_settings.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.core.settings'`。
- 绿灯：同一命令通过，结果为 `3 passed`。
- 产出：`config/sources.example.yaml`、`AppSettings`、`SourceConfig`、`ModelConfig`、`PrivacyConfig`、`load_settings()`。

**验收标准：**

- 配置文件能声明多个本地知识目录。
- 忽略规则可以表达目录、扩展名和 glob 模式。
- 配置错误能返回清晰异常。

### Task 3: 数据库与核心模型

**目标：** 建立 SQLite 元数据层，定义 `Source`、`Document`、`Chunk`、`IndexJob`、`Memory` 的初始 schema。

**文件：**

- Create: `backend/app/db/session.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/models/source.py`
- Create: `backend/app/models/document.py`
- Create: `backend/app/models/chunk.py`
- Create: `backend/app/models/index_job.py`
- Create: `backend/app/models/memory.py`
- Create: `backend/app/repositories/sources.py`
- Create: `backend/app/repositories/documents.py`
- Create: `backend/tests/test_models.py`

**产出接口：**

- `Source`
- `Document`
- `Chunk`
- `IndexJob`
- `Memory`
- `SourceRepository`
- `DocumentRepository`

**步骤：**

- [x] 定义 SQLAlchemy base 和 session 工厂。
- [x] 建立 `Source` 模型，包含 `source_type`、`name`、`uri`、`storage_mode`、`sync_direction`、`last_sync_at`。
- [x] 建立 `Document` 模型，包含 `source_id`、`uri`、`title`、`content_hash`、`mime_type`、`remote_id`、`mirror_status`、`metadata_json`。
- [x] 建立 `Chunk` 模型，包含 `document_id`、`chunk_index`、`text`、`heading_path`、`page_number`、`token_count`。
- [x] 建立 `IndexJob` 和 `Memory` 模型。
- [x] 编写 repository 的创建、查询、更新基础方法。
- [x] 编写 SQLite 内存库测试。

执行记录：

- 红灯 1：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_models.py -v` 首次失败于 `ModuleNotFoundError: No module named 'sqlalchemy'`，因此补充 SQLAlchemy 依赖。
- 红灯 2：安装依赖后，同一命令失败于 `ModuleNotFoundError: No module named 'app.db'`，确认数据库模块尚未实现。
- 红灯 3：新增 repository 更新测试后，`.\.venv\Scripts\python.exe -m pytest backend/tests/test_models.py::test_repositories_update_source_and_document_status -v` 失败于 `AttributeError: 'SourceRepository' object has no attribute 'update'`。
- 绿灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_models.py -v` 通过，结果为 `3 passed`。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `7 passed`。
- 一致性：`IndexJob` 实现中保留 `created_at`、`updated_at` 审计字段，并已同步更新 `docs/project-design.md` 的数据模型草案。

**验收标准：**

- 测试能创建 source、document、chunk 并查询。
- 文档知识库模型和 memory 模型物理分离。
- 字段与 `docs/project-design.md` 数据模型草案保持一致。

### Task 4: Alembic 迁移

**目标：** 建立数据库 schema 演进能力，避免后续直接手改数据库。

**文件：**

- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/<revision>_initial_schema.py`
- Create: `backend/tests/test_migrations.py`

**产出接口：**

- `alembic upgrade head`
- `alembic downgrade base`

**步骤：**

- [x] 初始化 Alembic 配置。
- [x] 将 SQLAlchemy metadata 接入 Alembic。
- [x] 创建初始迁移脚本。
- [x] 测试迁移能在临时 SQLite 数据库上 upgrade。
- [x] 测试核心表存在。

执行记录：

- 红灯 1：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_migrations.py -v` 首次失败于 `ModuleNotFoundError: No module named 'alembic'`，因此补充 Alembic 依赖。
- 红灯 2：安装依赖后，同一命令失败于 `Path doesn't exist: 'E:\\Automatic\\personal_wiki_agent\\backend\\alembic'`，确认迁移目录尚未实现。
- 绿灯：同一命令通过，结果为 `2 passed`，覆盖 `upgrade head` 建表和 `downgrade base` 删除核心表。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `9 passed`。

**验收标准：**

- 新环境可以通过迁移创建数据库。
- schema 变更有版本记录。

### Task 5: Connector 基础接口

**目标：** 定义所有数据源统一接入边界，为本地目录、同步目录和后续云端 connector 预留稳定接口。

**文件：**

- Create: `backend/app/connectors/base.py`
- Create: `backend/app/connectors/local_directory.py`
- Create: `backend/app/connectors/local_synced_notes.py`
- Create: `backend/app/connectors/obsidian_vault.py`
- Create: `backend/tests/test_connectors_base.py`

**产出接口：**

- `Connector`
- `DiscoveredItem`
- `SyncResult`
- `LocalDirectoryConnector`
- `LocalSyncedNotesConnector`
- `ObsidianVaultConnector`

**步骤：**

- [x] 定义 `Connector.scan()`，返回发现的文件或远程条目。
- [x] 定义 `DiscoveredItem`，包含 `uri`、`title`、`content_hash`、`mtime`、`mime_type`、`metadata`。
- [x] 实现本地目录递归扫描。
- [x] 支持忽略规则过滤。
- [x] `local_synced_notes` 复用本地目录扫描，但保留 source type 和同步目录元数据。
- [x] `obsidian_vault` 第一版按 Markdown 目录处理，并预留 front matter、标签、双链增强位置。
- [x] 编写临时目录测试。

执行记录：

- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_connectors_base.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.connectors'`，确认 connector 模块尚未实现。
- 绿灯：同一命令通过，结果为 `5 passed`。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `14 passed`。
- 边界：Connector 只负责发现资源并输出统一 `DiscoveredItem`，不调用 parser、不写数据库、不执行索引。

**验收标准：**

- 能扫描多个目录。
- 能排除敏感目录和临时文件。
- 输出不依赖具体 parser。

### Task 6: 增量同步判断

**目标：** 判断新增、更新、删除和移动，避免每次全量重建。

**文件：**

- Create: `backend/app/indexing/sync.py`
- Create: `backend/tests/test_sync_detection.py`

**产出接口：**

- `detect_changes(source_id, discovered_items, existing_documents=None) -> ChangeSet`
- `DocumentSnapshot`
- `ChangeSet.added`
- `ChangeSet.updated`
- `ChangeSet.deleted`
- `ChangeSet.unchanged`
- `ChangeSet.moved_candidates`

**步骤：**

- [x] 根据 `uri`、`content_hash`、`mtime` 判断新增和更新。
- [x] 根据数据库已有记录与扫描结果差异判断删除。
- [x] 对疑似移动文件保留 content hash 识别能力。
- [x] 为删除文档实现 `status=deleted`，第一版不物理删除。
- [x] 编写新增、更新、删除、未变化测试。

执行记录：

- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_sync_detection.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.indexing'`，确认增量同步模块尚未实现。
- 绿灯：同一命令通过，结果为 `5 passed`。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `19 passed`。
- 边界：`detect_changes` 保持纯函数，负责对 `DiscoveredItem` 和 `DocumentSnapshot` 做差异判断；数据库读取、状态落库和后续 parser/indexer 编排留给后续任务。

**验收标准：**

- 同一批文件重复扫描不会重复创建 document。
- 修改文件后只更新对应 document。
- 删除文件后 document 状态可追踪。

### Task 7: ParserAdapter 与基础解析器

**目标：** 把不同文件格式统一解析为 `ParseResult`。

**文件：**

- Create: `backend/app/parsers/base.py`
- Create: `backend/app/parsers/markdown.py`
- Create: `backend/app/parsers/text.py`
- Create: `backend/app/parsers/pdf.py`
- Create: `backend/app/parsers/docx.py`
- Create: `backend/app/parsers/html.py`
- Create: `backend/tests/test_parsers.py`

**产出接口：**

- `ParserAdapter`
- `ParseResult`
- `MarkdownParser`
- `TextParser`
- `PdfParser`
- `DocxParser`
- `HtmlParser`

**步骤：**

- [x] 定义 `ParseResult`，包含 `title`、`text`、`sections`、`page_map`、`links`、`metadata`。
- [x] Markdown / txt 直接读取。
- [x] PDF 使用 PyMuPDF 抽取文本和页码。
- [x] docx 使用 python-docx 抽取标题和段落。
- [x] HTML 使用 BeautifulSoup/readability 抽取正文。
- [x] 为空文件、编码异常、解析失败返回明确错误。
- [x] 编写各格式最小样例测试。

执行记录：

- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_parsers.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.parsers'`，确认 parser 模块尚未实现。
- 依赖：补充 `PyMuPDF`、`python-docx`、`beautifulsoup4`，并在本地验证环境安装。
- 绿灯：同一命令通过，结果为 `6 passed`。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `25 passed`。
- 边界：HTML 第一版使用 BeautifulSoup 做轻量正文抽取；readability 类增强留给后续解析质量优化。解析失败、空文件和编码异常统一通过 `ParseResult.warnings` 表达，避免阻断后续索引任务。

**验收标准：**

- 支持 MVP 五类文件：Markdown、txt、PDF、docx、HTML。
- 解析器通过接口接入，上层不直接依赖具体库。
- 解析失败不会阻断整个索引任务。

### Task 8: Chunker

**目标：** 将解析后的文本切成适合检索和引用的 chunk。

**文件：**

- Create: `backend/app/indexing/chunker.py`
- Create: `backend/tests/test_chunker.py`

**产出接口：**

- `Chunker`
- `ChunkInput`
- `ChunkOutput`
- `chunk_document(parse_result) -> list[ChunkOutput]`

**步骤：**

- [x] Markdown 优先按标题层级切分。
- [x] PDF 保留页码。
- [x] txt / docx / HTML 按段落和长度切分。
- [x] 每个 chunk 保留 `heading_path`、`page_number`、`token_count`、`chunk_index`。
- [x] 测试标题切分、长度切分、页码保留。

执行记录：

- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_chunker.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.indexing.chunker'`，确认 chunker 模块尚未实现。
- 绿灯：同一命令通过，结果为 `4 passed`。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `29 passed`。
- 边界：Task 8 只负责把 `ParseResult` 切成内存中的 `ChunkOutput`；写入 `Document` / `Chunk` 表、记录索引任务和失败重试留给 Task 9。

**验收标准：**

- chunk 可以追溯到原始文档位置。
- 不产生大量过短或过长 chunk。

### Task 9: Indexing Pipeline

**目标：** 串联扫描、变更判断、解析、分块、写入数据库。

**文件：**

- Create: `backend/app/indexing/pipeline.py`
- Create: `backend/app/repositories/index_jobs.py`
- Create: `backend/tests/test_indexing_pipeline.py`

**产出接口：**

- `IndexingPipeline`
- `run_source_index(source_id) -> IndexJob`
- `run_all_sources() -> list[IndexJob]`

**步骤：**

- [x] 创建 `IndexJob` 记录。
- [x] 扫描 source。
- [x] 判断变更。
- [x] 对新增和更新文档执行解析和分块。
- [x] 写入 document 和 chunk。
- [x] 记录处理数量、失败数量和错误消息。
- [x] 支持失败重试。

执行记录：

- 分支：`main`。
- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_indexing_pipeline.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.indexing.pipeline'`。
- 绿灯：同一命令通过，结果为 `5 passed`。
- 回归：`.\.venv\Scripts\python.exe -m pytest backend/tests -v` 通过，结果为 `34 passed`。
- 产出：新增 `IndexingPipeline`、`IndexJobRepository` 和 `test_indexing_pipeline.py`，补充 `DocumentRepository` / `SourceRepository` 所需查询与更新方法。
- 边界：Task 9 只写入 SQLite 元数据和 chunk，不直接写入 FTS5 或向量索引；失败重试在 MVP 阶段通过重新运行 source 索引实现，单文件失败会记录到 `IndexJob.failed_items` 和 `error_message`。

**验收标准：**

- 对一个本地目录执行索引后，数据库中有 source、document、chunk。
- 单个文件失败不阻断整个 source。
- 索引任务状态可查询。

### Task 10: LexicalIndex 与 SQLite FTS5

**目标：** 建立关键词检索能力，同时保留后续替换搜索引擎的接口。

**文件：**

- Create: `backend/app/indexing/lexical.py`
- Create: `backend/app/indexing/sqlite_fts.py`
- Create: `backend/tests/test_sqlite_fts.py`

**产出接口：**

- `LexicalIndex`
- `SQLiteFtsIndex`
- `index_chunks(chunks)`
- `search(query, filters) -> list[SearchHit]`

**步骤：**

- [x] 定义 `LexicalIndex` 抽象接口。
- [x] 创建 SQLite FTS5 表。
- [x] 将 chunk 写入 FTS5。
- [x] 实现关键词搜索。
- [x] 返回 chunk_id、document_id、score、snippet。
- [x] 测试中文和英文关键词基础命中。

执行记录：

- 分支：`main`。
- 红灯 1：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_sqlite_fts.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.indexing.lexical'`。
- 红灯 2：新增 Pipeline 集成测试后，`.\.venv\Scripts\python.exe -m pytest backend/tests/test_indexing_pipeline.py -v` 失败于 `IndexingPipeline.__init__()` 不支持 `lexical_index` 参数。
- 绿灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_sqlite_fts.py -v` 通过，结果为 `4 passed`；`.\.venv\Scripts\python.exe -m pytest backend/tests/test_indexing_pipeline.py -v` 通过，结果为 `7 passed`。
- 产出：新增 `LexicalIndex`、`SearchFilters`、`SearchHit`、`SQLiteFtsIndex` 和 `test_sqlite_fts.py`。
- 集成：`IndexingPipeline` 支持可选注入 `LexicalIndex`，配置后新增 / 更新 chunk 会写入关键词索引，文档删除会清理对应 FTS 命中。
- 边界：SQLite FTS5 表由 `SQLiteFtsIndex.ensure_schema()` 创建；MVP 阶段使用 SQLite `unicode61` tokenizer，中文基础命中依赖文本中存在可分隔词，后续中文分词和更强搜索引擎仍按演进路线处理。

**验收标准：**

- 业务层只依赖 `LexicalIndex`。
- SQLite FTS5 能检索已索引 chunk。
- 后续可增加 Tantivy / Meilisearch adapter。

### Task 11: Embedding 与 VectorStore 接口

**目标：** 保留向量检索能力的架构位置，第一版可先实现可替换接口和最小本地 adapter。

**文件：**

- Create: `backend/app/indexing/embedding.py`
- Create: `backend/app/indexing/vector_store.py`
- Create: `backend/tests/test_vector_store_contract.py`

**产出接口：**

- `Embedder`
- `VectorStore`
- `EmbeddingResult`
- `VectorSearchHit`

**步骤：**

- [x] 定义 `Embedder.embed_texts(texts) -> list[EmbeddingResult]`。
- [x] 定义 `VectorStore.upsert()`、`VectorStore.search()`、`VectorStore.delete_document()`。
- [x] 第一版实现内存型或 SQLite 文件型测试 adapter。
- [x] 将真实 Chroma / LanceDB / Qdrant / sqlite-vec 留在后续选择中。
- [x] 测试接口契约。

执行记录：

- 分支：`main`。
- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_vector_store_contract.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.indexing.embedding'`。
- 绿灯：同一命令通过，结果为 `5 passed`。
- 产出：新增 `Embedder`、`EmbeddingResult`、`HashingEmbedder`、`VectorStore`、`VectorRecord`、`VectorSearchFilters`、`VectorSearchHit`、`InMemoryVectorStore` 和 `test_vector_store_contract.py`。
- 边界：`HashingEmbedder` 只是用于本地测试和接口闭环的确定性向量实现，不代表真实语义 embedding；真实 Chroma、LanceDB、Qdrant、sqlite-vec 和模型 embedding 接入留给后续任务。

**验收标准：**

- Retrieval 层能依赖 `VectorStore` 接口。
- 未配置真实 embedding 时，系统仍能用关键词检索工作。

### Task 12: ModelProvider 与模型注册表

**目标：** 让用户只配置 provider、API key、base URL 和偏好，系统负责模型发现、能力识别和任务路由。

**文件：**

- Create: `backend/app/llm/provider.py`
- Create: `backend/app/llm/registry.py`
- Create: `backend/app/llm/catalog.py`
- Create: `backend/app/llm/router.py`
- Create: `backend/app/llm/openai_provider.py`
- Create: `backend/app/llm/ollama_provider.py`
- Create: `backend/tests/test_model_registry.py`

**产出接口：**

- `ModelProvider`
- `ModelRegistry`
- `ModelCatalog`
- `ModelRouter`
- `ChatModelClient`
- `EmbeddingModelClient`

**步骤：**

- [x] 定义 provider 抽象。
- [x] 支持 OpenAI-compatible provider 的配置形态。
- [x] 支持 Ollama provider 的配置形态。
- [x] 实现模型 catalog 缓存结构。
- [x] 实现按 `chat`、`embedding`、`summary` 任务选择模型。
- [x] 测试未配置 key、配置错误、默认模型选择。

执行记录：

- 分支：`main`。
- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_model_registry.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.llm'`。
- 绿灯：同一命令通过，结果为 `6 passed`。
- 产出：新增 `ModelProvider`、`ProviderConfig`、`ModelInfo`、`CredentialStatus`、`ChatModelClient`、`EmbeddingModelClient`、`ModelCatalog`、`ModelRegistry`、`ModelRouter`、`OpenAICompatibleProvider`、`OllamaProvider` 和 `test_model_registry.py`。
- 边界：Task 12 只完成 provider 配置、模型 catalog 和任务路由闭环；暂不进行真实 OpenAI-compatible 或 Ollama HTTP 调用，真实模型调用留给后续 API / Answer 模块接入。

**验收标准：**

- 模型名称不写死在业务代码中。
- 后续接入 Claude、Gemini、DeepSeek、Qwen、vLLM 不影响 RAG 主流程。

### Task 13: Hybrid Retriever

**目标：** 合并关键词召回、向量召回和元数据过滤，返回统一检索结果。

**文件：**

- Create: `backend/app/retrieval/hybrid.py`
- Create: `backend/app/retrieval/filters.py`
- Create: `backend/app/retrieval/ranking.py`
- Create: `backend/tests/test_hybrid_retriever.py`

**产出接口：**

- `HybridRetriever`
- `SearchQuery`
- `SearchResult`
- `SourceCitation`

**步骤：**

- [x] 定义检索请求模型，支持 query、source_id、file_type、time_range、top_k。
- [x] 调用 `LexicalIndex` 做关键词召回。
- [x] 在可用时调用 `VectorStore` 做语义召回。
- [x] 合并、去重、排序。
- [x] 返回 document、chunk、score、引用定位。
- [x] 测试关键词命中、过滤、空结果。

执行记录：

- 分支：`main`。
- 红灯：`.\.venv\Scripts\python.exe -m pytest backend/tests/test_hybrid_retriever.py -v` 首次失败于 `ModuleNotFoundError: No module named 'app.retrieval'`。
- 绿灯：同一命令通过，结果为 `4 passed`。
- 产出：新增 `SearchQuery`、`HybridRetriever`、`SearchResult`、`SourceCitation`、`combine_scores` 和 `test_hybrid_retriever.py`。
- 边界：Task 13 只实现检索层内部契约，不暴露 HTTP API；文件类型和时间范围先保留在 `SearchQuery` 中，底层过滤能力在后续 Search API / repository 查询增强时继续接入。

**验收标准：**

- `POST /search` 可以返回可追溯来源。
- 没有向量库时，关键词检索仍可工作。

### Task 14: Search API 与文档详情 API

**目标：** 对外暴露检索和来源打开能力。

**文件：**

- Create: `backend/app/api/routes_search.py`
- Create: `backend/app/api/routes_documents.py`
- Create: `backend/tests/test_search_api.py`

**产出接口：**

- `POST /search`
- `GET /documents/{document_id}`
- `GET /chunks/{chunk_id}`

**步骤：**

- [x] 实现 `POST /search`。
- [x] 实现 document 详情接口。
- [x] 实现 chunk 详情接口。
- [x] 返回 citations、metadata、source 信息。
- [x] 测试正常搜索、空搜索、非法过滤条件。

**完成记录：**

- 产出：新增 `routes_search.py`、`routes_documents.py` 和 `test_search_api.py`。
- 搜索接口通过 `HybridRetriever` + `SQLiteFtsIndex` 暴露关键词优先的检索能力；暂未接入持久化向量库，因此没有向量库时仍可工作。
- 详情接口返回 document、chunk、source 和 metadata，供前端、Chat API 和后续 Agent 工具打开来源。
- 边界：Task 14 只提供检索和来源详情 API，不生成自然语言回答；回答合成、上下文构造和 memory 注入留给 Task 15。

**验收标准：**

- 前端和 Agent 工具可以通过 API 获取检索结果和来源详情。

### Task 15: Answer 模块与 Chat API

**目标：** 基于检索结果构造上下文，生成带来源引用的回答。

**文件：**

- Create: `backend/app/answer/context_builder.py`
- Create: `backend/app/answer/synthesizer.py`
- Create: `backend/app/api/routes_chat.py`
- Create: `backend/tests/test_chat_api.py`

**产出接口：**

- `build_answer_context(search_results) -> AnswerContext`
- `AnswerSynthesizer.generate(question, context) -> Answer`
- `POST /chat`

**步骤：**

- [x] 定义回答输出结构：`answer`、`citations`、`confidence`、`retrieval_summary`。
- [x] 构造上下文时保留 chunk 来源和文档元数据。
- [x] 当检索结果不足时返回“没有找到可靠来源”的明确说明。
- [x] 接入 `ModelRouter` 调用 chat 模型。
- [x] 使用 fake model client 编写稳定测试。

**完成记录：**

- 产出：新增 `answer/context_builder.py`、`answer/synthesizer.py`、`routes_chat.py` 和 `test_chat_api.py`。
- Chat API 通过检索层获取可追溯来源，再构造 `AnswerContext`，最后由 `AnswerSynthesizer` 调用 chat model client 生成回答。
- 回答引用只来自检索上下文中的 citations，不从模型输出里反向猜测，避免伪造来源。
- 没有可靠来源时直接返回“没有找到可靠来源”，不会调用模型，也不会生成空引用。
- 有可靠来源但未配置 `ModelRouter` 或模型客户端不可用时，返回结构化 503 错误，便于前端提示用户配置模型。
- 边界：Task 15 只完成回答合成和 Chat API 闭环；memory 个性化上下文仍留给 Task 17，Agent 工具封装留给 Task 16。

**验收标准：**

- 回答不会伪造来源。
- 引用能定位到 document / chunk。
- 没有模型配置时，错误信息可理解。

### Task 16: Agent Tools

**目标：** 把检索、打开来源、总结目录和主题地图封装为 Agent 可调用工具。

**文件：**

- Create: `backend/app/agent_tools/search_notes.py`
- Create: `backend/app/agent_tools/open_source.py`
- Create: `backend/app/agent_tools/summarize_folder.py`
- Create: `backend/app/agent_tools/build_topic_map.py`
- Create: `backend/tests/test_agent_tools.py`

**产出接口：**

- `search_notes(query, filters)`
- `open_source(document_id | chunk_id)`
- `summarize_folder(source_id | path)`
- `build_topic_map(query | source_id)`

**步骤：**

- [x] `search_notes` 调用 `HybridRetriever`。
- [x] `open_source` 调用 document / chunk repository。
- [x] `summarize_folder` 基于 source 下的检索结果和 Answer 模块生成摘要。
- [x] `build_topic_map` 第一版生成主题列表、相关文档和引用，不做复杂图谱。
- [x] 编写工具层测试。

**完成记录：**

- 产出：新增 `agent_tools/search_notes.py`、`agent_tools/open_source.py`、`agent_tools/summarize_folder.py`、`agent_tools/build_topic_map.py` 和 `test_agent_tools.py`。
- `search_notes` 复用 `HybridRetriever` 与 `SQLiteFtsIndex`，返回和 Search API 一致的可追溯检索结果。
- `open_source` 支持按 `document_id` 或 `chunk_id` 打开来源详情，工具调用方不需要直接访问 repository。
- `summarize_folder` 基于数据源下的 chunk 构造 `AnswerContext`，再复用 `AnswerSynthesizer` 生成带引用摘要；没有外部模型时提供本地抽取式 fallback，保证 MVP 可运行。
- `build_topic_map` 第一版按 heading 或文档标题聚合主题、相关文档和引用，不做复杂图谱计算。
- 边界：Task 16 只完成 Agent 可调用工具层，不新增 HTTP API，不引入长期记忆；memory 个性化仍留给 Task 17。

**验收标准：**

- 工具层屏蔽底层数据库和索引细节。
- 后续 custom agent 可以组合这些工具。

### Task 17: Memory 最小能力

**目标：** 建立长期记忆的最小表和接口，但不把文档 chunk 混入 memory。

**文件：**

- Create: `backend/app/memory/store.py`
- Create: `backend/app/memory/extractor.py`
- Create: `backend/app/api/routes_memory.py`
- Create: `backend/tests/test_memory.py`

**产出接口：**

- `remember_preference(content, source)`
- `search_memory(query)`
- `GET /memory`
- `POST /memory`

**步骤：**

- [x] 实现 memory CRUD。
- [x] 支持 `user_preference`、`project_context`、`workflow_habit`、`stable_fact`。
- [x] 支持 confidence、source、created_at、updated_at、expires_at。
- [x] Chat API 中只把 memory 作为个性化上下文，不作为文档来源引用。
- [x] 编写 memory 与 document 分离测试。

**完成记录：**

- 最终契约无变更：`POST /memory` 请求体为 `{memory_type, content, source, confidence?, expires_at?}`，返回单条 memory。
- `GET /memory?query=&memory_type=&limit=` 返回 `{items:[...]}`，只包含 active 且未过期的 memory。
- `POST /chat` 响应新增 `memories_used: []`，明确区分文档来源 `citations` 和长期记忆。
- 支持的 `memory_type` 为 `user_preference`、`project_context`、`workflow_habit`、`stable_fact`。
- 验证结果：`backend/tests/test_memory.py` 6 passed，`backend/tests/test_chat_api.py` 5 passed；本次复验全量 `backend/tests` 为 83 passed。

**验收标准：**

- 文档 chunk 不写入 memory 表。
- 长期记忆不混入 document chunk 索引。
- Chat 输出能区分 `citations` 和 `memories_used`。

### Task 18: 对话式 Web UI

**目标：** 提供一个能验证端到端闭环的简约对话式 Agent 工作台。

**文件：**

- Create: `frontend/package.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/views/ChatView.tsx`
- Create: `frontend/src/views/SourcesView.tsx`
- Create: `frontend/src/views/IndexJobsView.tsx`
- Create: `frontend/src/components/SourceDrawer.tsx`
- Create: `frontend/src/components/ToolActivity.tsx`

**产出界面：**

- 对话问答页。
- 数据源入口。
- 索引状态入口。
- 来源详情抽屉。
- 基础设置入口。

**步骤：**

- [x] 初始化 React + Vite + TypeScript。
- [x] 建立 API client。
- [x] 实现对话输入和回答展示。
- [x] 展示 citations。
- [x] 点击 citation 打开来源详情抽屉。
- [x] 展示工具活动流。
- [x] 数据源和索引状态先做只读视图。
- [x] 数据源页接入 `GET /sources` 和 `POST /sources`。
- [x] 索引页接入 `GET /index/jobs` 和 `POST /index/run`。
- [x] 用 Playwright 或浏览器手动验证主要流程。

**当前记录：**

- `frontend/` 已提供对话式 Agent 工作台。
- 前端测试已覆盖 API client、工具活动流、对话视图、数据源视图和索引任务视图。
- 前端 TypeScript 类型检查已通过。
- Playwright UI 主流程验收已通过，覆盖默认 Chat 页面、发送问题、展示引用、打开来源抽屉、创建数据源和触发索引任务。
- 本次 Playwright 验收使用浏览器路由 mock API 响应，用于验证前端主流程；真实后端浏览器 E2E 仍需在普通本地环境或后续 CI 环境补充。
- 后端已补充本地 Vite Web UI 跨端口访问 FastAPI 的 CORS 配置，并通过 `backend/tests/test_cors.py` 回归验证；真实后端浏览器 E2E 本次被当前执行环境拦截，仍未标为完成。
- 前端生产构建命令在当前沙箱中受 Node 写文件权限限制，需要在普通本地环境或 GitHub Actions 中复验。

**验收标准：**

- 打开 Web UI 后默认进入对话式 Agent 主界面。
- 配置和管理能力不抢占主体验。
- 来源引用能展开查看。

### Task 19: 文档、验收和打包

**目标：** 整理 MVP 使用说明、开发说明、验收清单，确保后续能继续迭代。

**文件：**

- Modify: `README.md`
- Modify: `docs/project-design.md`
- Modify: `docs/technical-direction.md`
- Create: `docs/mvp-acceptance-report.md`

**步骤：**

- [x] 更新 README 的本地启动、配置、索引、搜索、问答说明。
- [x] 记录已完成能力和未完成能力。
- [x] 执行文档一致性体检。
- [x] 形成 MVP 验收报告。
- [!] 确认测试、格式检查、基础手动验证结果；自动化测试、类型检查、文档检查和 Playwright UI 主流程验收已完成，前端生产构建输出与真实后端浏览器 E2E 仍需在普通本地环境或 GitHub Actions 中补充确认。

**当前记录：**

- README 已覆盖本地运行、配置、索引、搜索、问答、Agent Tools、Memory、Web UI、CI 和打包说明。
- [mvp-acceptance-report.md](mvp-acceptance-report.md) 已记录已完成能力、未完成能力、验证命令和 Task 18 到 Task 21 的当前状态。
- 文档与文本卫生检查已通过：未发现乱码替换字符、合并冲突标记或失效的 Markdown 本地相对链接。
- Task 19 的文档与验收整理已基本完成；剩余风险来自真实后端浏览器 E2E 和前端生产构建输出复验，不是文档本身缺失。

**验收标准：**

- 新用户能按 README 启动项目。
- MVP 验收标准逐项有结果。
- 文档与实际代码不冲突。

### Task 20: Source / Index API 与 Web UI 接入

**目标：** 让数据源配置和索引任务从内部能力变成可被前端调用的 MVP 闭环。

**文件：**

- Create: `backend/app/api/routes_sources.py`
- Create: `backend/app/api/routes_index.py`
- Create: `backend/tests/test_source_index_api.py`
- Modify: `backend/app/repositories/sources.py`
- Modify: `backend/app/repositories/index_jobs.py`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/views/SourcesView.tsx`
- Modify: `frontend/src/views/IndexJobsView.tsx`
- Create: `frontend/src/views/SourcesView.test.tsx`
- Create: `frontend/src/views/IndexJobsView.test.tsx`

**产出接口：**

- `GET /sources`
- `POST /sources`
- `POST /index/run`
- `GET /index/jobs`

**步骤：**

- [x] 为 Source / Index API 写失败测试。
- [x] 实现 Source 创建和列表 API。
- [x] 实现同步索引触发和最近任务列表 API。
- [x] 索引触发时接入 `SQLiteFtsIndex`，保证 `/search` 能命中刚索引的内容。
- [x] 前端 API client 增加 Source / Index 方法。
- [x] 数据源页从占位表切换为真实列表和创建表单。
- [x] 索引页从占位表切换为真实任务列表和运行按钮。

**完成记录：**

- 后端新增测试 `backend/tests/test_source_index_api.py`，覆盖数据源创建、source_type 校验、单 source 索引、全部启用 source 索引、缺失 source 404。
- 前端新增 `SourcesView.test.tsx` 和 `IndexJobsView.test.tsx`，验证页面通过 API 加载数据并触发创建或索引。
- 边界：`POST /index/run` 当前是请求内同步执行，适合 MVP；后续如果索引耗时变长，应演进为后台任务队列。
- 边界：`POST /sources` 只开放已有 connector 的三类本地优先 source；云端笔记 connector 仍按后续路线推进。

**验收标准：**

- 用户可以通过 API 或 Web UI 创建本地数据源。
- 用户可以通过 API 或 Web UI 触发索引任务。
- 索引完成后，`POST /search` 可以检索到新内容。

### Task 21: GitHub Actions CI

**目标：** 给 GitHub 仓库增加最小但有效的质量门禁，避免提交后才发现后端、前端或文档基础检查失败。

**文件：**

- Create: `.github/workflows/ci.yml`
- Delete: `.github/workflows/pylint.yml`
- Modify: `README.md`
- Modify: `docs/mvp-acceptance-report.md`

**CI 范围：**

- Backend：Python 3.11，安装 `backend[dev]`，运行 `python -m pytest backend/tests -q`。
- Frontend：Node 22，运行 `npm ci`、`npm test`、`npm exec tsc -- --noEmit`、`npm run build`。
- Docs：检查已跟踪文本文件中的乱码替换字符、合并冲突标记，以及 Markdown 本地相对链接。

**步骤：**

- [x] 删除过期的 Python 3.8 / 3.9 / 3.10 Pylint workflow。
- [x] 新增统一 `CI` workflow。
- [x] README 增加 CI badge 和 CI 说明。
- [x] 验收报告记录 CI 范围、边界和后续远端验证动作。

**完成记录：**

- CI 触发条件为 push、pull request 和 workflow_dispatch。
- CI 只做质量门禁，不做自动部署；自动部署留到项目有稳定部署目标后再设计。
- 本地可验证后端、前端测试、类型检查和文档检查；GitHub Actions 远端首次运行需要 push 后在 Actions 页面确认。

**验收标准：**

- 提交到 GitHub 后，Actions 页面能看到 `CI` workflow。
- 后端、前端和文档基础检查分别独立失败或通过，便于快速定位问题。

## 6. 每周追踪模板

每周结束时更新一次：

```markdown
## 第 N 周复盘

- 本周目标：
- 已完成：
- 未完成：
- 验证结果：
- 风险：
- 下周目标：
- 需要同步的文档：
```

## 7. 每个任务的完成定义

任务只有同时满足以下条件，才算完成：

1. 功能按任务描述实现。
2. 有对应测试或可重复验证步骤。
3. 相关文档已更新。
4. 没有破坏既有文档路线。
5. 本地工作区没有无关变更混入。
6. 如果改变需求、架构、工期、验收或约束，已执行文档一致性体检。

## 8. 风险追踪

| 风险 | 触发信号 | 应对 |
| --- | --- | --- |
| 文档解析质量不足 | PDF、docx、HTML 正文抽取不完整 | 保留原文预览，后续接入 MarkItDown、Docling、unstructured、marker |
| 中文检索质量不足 | FTS5 对中文短词、人名、术语命中差 | 保留 hybrid search，后续加入中文分词、rerank、Tantivy / Meilisearch adapter |
| 模型 provider 配置复杂 | 用户不知道填哪个模型名或 endpoint | 使用 ModelRegistry / ModelCatalog 发现和缓存模型 |
| 有道云笔记 API 受限 | 官方 API 权限、稳定性或导出能力不足 | 先用本地同步目录、导出文件或本地缓存接入 |
| UI 变成后台系统 | 首页被配置页、索引状态和表格占满 | 遵守对话式 Agent UI 文档，配置收纳到侧栏、设置页或抽屉 |
| 记忆和文档混淆 | memory 被当作知识库来源引用 | 区分 `citations` 和 `memories_used`，存储和检索分离 |
| 本地资料误上传 | Export / Mirror 默认写回云端 | 默认不上传，写回前必须用户显式确认 |

## 9. 当前阶段建议推进顺序

截至本次复验，Task 1 到 Task 17 的后端主干能力已经有实现和测试覆盖；Task 18 Web UI 已完成代码集成，并通过 Playwright UI 主流程验收；Task 20 已补齐 Source / Index API 并接入 Web UI；Task 21 已新增 GitHub Actions CI。后端已补充本地 Vite Web UI CORS 和 Chat 英文自然问句弱词过滤回归。生产构建输出写入和真实后端浏览器 E2E 需要在普通本地环境或 GitHub Actions 中复验。

下一步优先推进：

1. 端到端验收：以 [mvp-acceptance-report.md](mvp-acceptance-report.md) 为验收清单，补充真实后端浏览器 E2E、真实本地目录索引和生产构建复验结果。
2. push 到 GitHub 后查看 Actions 页面，确认 `CI` workflow 首次远端运行结果。
3. 将 `POST /index/run` 从同步执行演进为后台任务，避免大目录索引阻塞请求。
4. 推进真实模型 provider HTTP client，验证 Chat API 的真实模型调用。

## 10. 阶段验收门

### M0 验收门

- [ ] `backend` 可安装依赖。
- [ ] `GET /health` 可用。
- [ ] 测试命令可运行。
- [ ] SQLite schema 可创建。

### M1 验收门

- [ ] 可以配置多个本地目录。
- [ ] 可以扫描本地目录。
- [ ] 可以识别新增、更新、删除。
- [ ] 可以排除敏感目录。

### M2 验收门

- [ ] Markdown、txt、PDF、docx、HTML 可解析。
- [ ] Parser 通过 `ParserAdapter` 接入。
- [ ] 解析失败可记录，不阻断整个任务。

### M3 验收门

- [ ] 文档可分块。
- [ ] 元数据写入 SQLite。
- [ ] chunk 写入 FTS5。
- [ ] 索引任务状态可查询。

### M4 验收门

- [ ] `POST /search` 可用。
- [ ] 检索结果带来源。
- [ ] 来源详情可打开。

### M5 验收门

- [ ] `POST /chat` 可用。
- [ ] 回答带 citations。
- [ ] 没有来源时明确说明。

### M6 验收门

- [ ] `search_notes` 可用。
- [ ] `open_source` 可用。
- [ ] `summarize_folder` 可用。
- [ ] `build_topic_map` 可用。

### M7 验收门

- [ ] Web UI 默认进入对话界面。
- [ ] 用户能提问并查看回答。
- [ ] 用户能展开来源详情。
- [ ] 工具活动流可见且可折叠。
