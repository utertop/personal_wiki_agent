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

- [ ] 定义 `ParseResult`，包含 `title`、`text`、`sections`、`page_map`、`links`、`metadata`。
- [ ] Markdown / txt 直接读取。
- [ ] PDF 使用 PyMuPDF 抽取文本和页码。
- [ ] docx 使用 python-docx 抽取标题和段落。
- [ ] HTML 使用 BeautifulSoup/readability 抽取正文。
- [ ] 为空文件、编码异常、解析失败返回明确错误。
- [ ] 编写各格式最小样例测试。

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

- [ ] Markdown 优先按标题层级切分。
- [ ] PDF 保留页码。
- [ ] txt / docx / HTML 按段落和长度切分。
- [ ] 每个 chunk 保留 `heading_path`、`page_number`、`token_count`、`chunk_index`。
- [ ] 测试标题切分、长度切分、页码保留。

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

- [ ] 创建 `IndexJob` 记录。
- [ ] 扫描 source。
- [ ] 判断变更。
- [ ] 对新增和更新文档执行解析和分块。
- [ ] 写入 document 和 chunk。
- [ ] 记录处理数量、失败数量和错误消息。
- [ ] 支持失败重试。

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

- [ ] 定义 `LexicalIndex` 抽象接口。
- [ ] 创建 SQLite FTS5 表。
- [ ] 将 chunk 写入 FTS5。
- [ ] 实现关键词搜索。
- [ ] 返回 chunk_id、document_id、score、snippet。
- [ ] 测试中文和英文关键词基础命中。

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

- [ ] 定义 `Embedder.embed_texts(texts) -> list[EmbeddingResult]`。
- [ ] 定义 `VectorStore.upsert()`、`VectorStore.search()`、`VectorStore.delete_document()`。
- [ ] 第一版实现内存型或 SQLite 文件型测试 adapter。
- [ ] 将真实 Chroma / LanceDB / Qdrant / sqlite-vec 留在后续选择中。
- [ ] 测试接口契约。

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

- [ ] 定义 provider 抽象。
- [ ] 支持 OpenAI-compatible provider 的配置形态。
- [ ] 支持 Ollama provider 的配置形态。
- [ ] 实现模型 catalog 缓存结构。
- [ ] 实现按 `chat`、`embedding`、`summary` 任务选择模型。
- [ ] 测试未配置 key、配置错误、默认模型选择。

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

- [ ] 定义检索请求模型，支持 query、source_id、file_type、time_range、top_k。
- [ ] 调用 `LexicalIndex` 做关键词召回。
- [ ] 在可用时调用 `VectorStore` 做语义召回。
- [ ] 合并、去重、排序。
- [ ] 返回 document、chunk、score、引用定位。
- [ ] 测试关键词命中、过滤、空结果。

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

- [ ] 实现 `POST /search`。
- [ ] 实现 document 详情接口。
- [ ] 实现 chunk 详情接口。
- [ ] 返回 citations、metadata、source 信息。
- [ ] 测试正常搜索、空搜索、非法过滤条件。

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

- [ ] 定义回答输出结构：`answer`、`citations`、`confidence`、`retrieval_summary`。
- [ ] 构造上下文时保留 chunk 来源和文档元数据。
- [ ] 当检索结果不足时返回“没有找到可靠来源”的明确说明。
- [ ] 接入 `ModelRouter` 调用 chat 模型。
- [ ] 使用 fake model client 编写稳定测试。

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

- [ ] `search_notes` 调用 `HybridRetriever`。
- [ ] `open_source` 调用 document / chunk repository。
- [ ] `summarize_folder` 基于 source 下的检索结果和 Answer 模块生成摘要。
- [ ] `build_topic_map` 第一版生成主题列表、相关文档和引用，不做复杂图谱。
- [ ] 编写工具层测试。

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

- [ ] 实现 memory CRUD。
- [ ] 支持 `user_preference`、`project_context`、`workflow_habit`、`stable_fact`。
- [ ] 支持 confidence、source、created_at、updated_at、expires_at。
- [ ] Chat API 中只把 memory 作为个性化上下文，不作为文档来源引用。
- [ ] 编写 memory 与 document 分离测试。

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

- [ ] 初始化 React + Vite + TypeScript。
- [ ] 建立 API client。
- [ ] 实现对话输入和回答展示。
- [ ] 展示 citations。
- [ ] 点击 citation 打开来源详情抽屉。
- [ ] 展示工具活动流。
- [ ] 数据源和索引状态先做只读视图。
- [ ] 用 Playwright 或浏览器手动验证主要流程。

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

- [ ] 更新 README 的本地启动、配置、索引、搜索、问答说明。
- [ ] 记录已完成能力和未完成能力。
- [ ] 执行文档一致性体检。
- [ ] 形成 MVP 验收报告。
- [ ] 确认测试、格式检查、基础手动验证结果。

**验收标准：**

- 新用户能按 README 启动项目。
- MVP 验收标准逐项有结果。
- 文档与实际代码不冲突。

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

## 9. 第一阶段建议开工顺序

下一步优先开工 Task 1 到 Task 4：

1. Task 1：项目工程骨架。
2. Task 2：配置系统。
3. Task 3：数据库与核心模型。
4. Task 4：Alembic 迁移。

这四个任务完成后，项目就具备稳定地基：能启动、能测试、能配置、能建库、能演进 schema。随后再进入本地 connector、parser 和索引闭环。

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
