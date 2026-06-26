# Personal Wiki Agent 技术选型与路线

## 1. 项目定位

Personal Wiki Agent 不是一个新的笔记 App，而是一个本地优先的个人知识库 Agent。

它的目标是整合个人电脑上的多个指定知识目录、本地文档、笔记 App 的本地同步目录、云端笔记 App、网页资料和长期对话上下文，形成一个可检索、可追溯、可扩展、可持续学习、可主动协作的个人 second brain。

核心体验参考 Khoj：用户应该能像和一个熟悉自己资料的助理对话一样，完成搜索、总结、关联、生成和提醒。

### 1.1 需求来源

本项目的核心用户是持续学习者和长期知识积累者。

这类用户的知识来源通常不是单一系统，而是分散在多个位置：

- PC 本地硬盘目录：课程资料、PDF、电子书、Markdown、Word、代码说明、项目资料、下载资料、归档文件。
- 笔记 App 本地数据或同步目录：Obsidian vault、有道云笔记本地缓存、语雀或其他笔记工具导出的 Markdown / HTML / PDF、同步到本机的笔记文件。
- 云端笔记知识库：Notion、飞书、语雀、有道云笔记、OneNote、Apple Notes 等。
- 网络知识来源：Internet 网页、公众号文章、网页剪藏、稍后读、书签、复制保存的文章片段。
- Agent 对话和长期记忆：用户偏好、项目背景、学习方向、历史整理结论。

因此，本项目必须从一开始就支持“多来源接入”的架构，而不是只面向单个目录、单个笔记 App 或单个向量库。

### 1.2 核心场景

第一优先级场景：

1. 用户配置一个或多个本地知识目录。
2. 系统持续扫描这些目录中的 PDF、Markdown、txt、docx、HTML 等资料。
3. 用户配置一个或多个笔记 App 的本地同步目录。
4. 系统将本地资料和笔记资料统一解析、索引、检索。
5. 用户通过 Agent 查询、检索、整理、归纳、整合资料。
6. Agent 回答时提供来源引用，确保结果可追溯。
7. 当用户持续向本地目录或笔记 App 中补充新内容时，系统能增量同步和更新知识库。
8. 随着长期使用，Agent 能逐步理解用户的学习方向、常用概念、项目背景和偏好。

后续增强场景：

- 接入云端笔记 API，补齐本地同步目录无法覆盖的内容。
- 对新增资料自动生成摘要、标签和主题关联。
- 对长期积累的资料生成主题地图、学习路线、项目上下文和阶段性 digest。
- 对重复、过期、未整理、缺少引用的资料给出主动提醒。

## 2. 总体技术路线

项目不直接 fork 大型开源项目，先做自己的轻量 MVP。

采用组合式参考路线：

- 产品体验参考 Khoj：个人 second brain、自托管、custom agent、个人资料问答。
- 架构参考 Onyx：connector、后台同步、hybrid search、权限/数据源模型、可扩展任务流。
- RAG 细节参考 Quivr：parser、chunk、retriever、vectorstore 抽象。
- Agent 长期记忆参考 Mem0：用户偏好、项目状态、会话记忆、长期上下文。

这些项目只作为设计参考和局部实现灵感，不作为直接依赖或 fork 基础。

## 3. 架构原则

### 3.0 目标架构先行，MVP 垂直切片

MVP 不是临时 demo 架构，而是在长期目标架构上先实现最小可用的垂直切片。

第一版可以只实现少量数据源、少量解析器、基础 hybrid search 和最小 Agent 工具，但必须保留长期架构边界：

- 数据源通过 Connector 接入。
- 内容通过 Parser 转成标准 Document / Chunk / Source 模型。
- 索引层、检索层、回答层、Agent 工具层分离。
- 文档知识库与长期记忆分离。
- 云端笔记通过 connector 同步，不作为临时外挂搜索。
- UI / CLI 只调用 API 和工具层，不直接绕过底层边界。
- 前端默认以对话式 Agent 为主入口，数据源、索引、模型、隐私和记忆配置收纳到侧栏、设置页或抽屉中，不让配置面板取代主体验。

后续成熟化应优先在既有层内扩展能力，而不是推翻整体分层。

### 3.1 本地优先

默认数据落在本机，用户明确配置后才接入云端服务。

敏感资料、索引数据、向量数据、长期记忆需要有清晰的本地存储边界。

本地优先不等于只支持本地文件。它表示系统的默认控制权、索引、缓存和记忆应尽量保留在用户自己的 PC 上；云端笔记和在线资料作为可选数据源，通过 connector 接入。

本地索引、FTS、向量库和缓存应被视为可重建的本地工作层，不应被视为唯一知识主副本。对于长期有价值的个人知识，系统应支持通过云端笔记、本地备份或导出文件形成可迁移路径。

### 3.2 文档知识库与长期记忆分离

文档知识库负责事实资料：

- 文件内容
- 笔记正文
- PDF / Word / Markdown / HTML 等文档
- 来源、路径、时间、标签等元数据
- 检索和引用

长期记忆负责 Agent 对用户和任务的理解：

- 用户偏好
- 项目背景
- 常用表达和工作习惯
- 当前长期目标
- 对话中沉淀的稳定事实

两者不能混在一个“万能向量库”里。回答问题时可以同时检索，但存储、更新、删除、权限和引用方式必须区分。

实现上应坚持：文档知识库与长期记忆分开存储、分开索引、分开检索、合并使用。文档知识库负责事实证据和来源引用，长期记忆负责用户偏好、项目上下文和个性化理解。

### 3.3 Hybrid Search 优先

中文和个人资料场景不能只依赖向量检索。

MVP 阶段就应保留 hybrid search 的架构位置：

- 关键词检索：适合精确标题、术语、人名、文件名、原文定位。
- 向量检索：适合语义相近、模糊问题、跨表达方式召回。
- 元数据过滤：适合按目录、来源、时间、标签、文档类型缩小范围。
- rerank：在后续阶段提升结果排序质量。

关键词检索的 MVP 默认实现可以是 SQLite FTS5，但必须通过 `LexicalIndex` 接口隔离，不能在业务层直接绑定 FTS5。后续当 chunk 数量、中文命中质量、字段权重、模糊搜索或复杂查询能力达到瓶颈时，应评估 Tantivy、Meilisearch 或 OpenSearch。

### 3.4 Connector 可插拔

所有数据源都通过 connector 接入。

MVP 先支持多个本地目录和笔记 App 的本地同步目录，后续逐步加入云端笔记 App。

云端笔记 API 应作为 connector 同步入口，而不是 Agent 每次问答时的临时外挂搜索。云端内容同步到本地知识库后，再进入统一解析、索引、检索和引用流程。

每个 connector 应统一输出标准文档对象：

- source_id
- source_type
- uri
- title
- content
- metadata
- updated_at
- permissions

### 3.5 持续学习与可进化

系统必须支持随用户持续补充资料而不断更新知识库。

持续学习不是指直接训练大模型，而是指：

- 持续扫描本地知识目录和笔记同步目录。
- 增量发现新增、修改、删除、移动的资料。
- 重新解析和索引变化内容。
- 为新增资料生成摘要、标签和主题关联。
- 将用户长期偏好和项目上下文沉淀到长期记忆。
- 通过检索质量反馈、常用查询和手动修正逐步优化排序与回答。

早期先实现增量索引和长期记忆表；后续再考虑更复杂的自动摘要、主题聚类、主动提醒和记忆冲突合并。

### 3.6 引用优先

Agent 的知识库回答必须尽量带来源引用。

没有可靠来源时，应明确说明是推断、记忆或模型常识，而不是伪装成知识库事实。

### 3.7 可迁移与云端同步互补

个人知识库必须考虑换电脑、重装系统、硬盘损坏和长期备份。

本地 PC 适合作为高性能索引、隐私资料、离线处理和临时工作空间；云端笔记 App 更适合作为跨设备同步、长期保存和换机恢复的稳定载体。

系统应区分：

- `local_only`：只存在于本地 PC 的资料。
- `local_synced`：由笔记 App 同步到本机的资料。
- `cloud_backed`：云端笔记是主副本，本地只保存索引和缓存。
- `cloud_mirror`：本地资料被用户显式归档或镜像到云端笔记。

本地资料可以被整理、摘要或归档到云端笔记，但必须由用户显式触发或确认，不能默认自动上传。

## 4. MVP 范围

第一版只做最小闭环：

1. 配置一个或多个本地知识目录。
2. 配置一个或多个笔记 App 本地同步目录。
3. 扫描 Markdown、txt、PDF、docx、HTML 文件。
4. 解析文本并生成标准文档对象。
5. chunk 分块并建立索引。
6. 支持关键词检索 + 向量检索的接口边界。
7. 提供问答接口，回答中包含来源引用。
8. 提供基础 Agent 工具：
   - search_notes
   - open_source
   - summarize_folder
   - build_topic_map
9. 提供对话式 Web UI 用于验证端到端流程，CLI 作为调试和自动化入口保留。
10. 支持忽略规则，排除敏感目录、临时文件和不应索引的个人内容。
11. 为后续云端笔记 connector 保留标准接口。

MVP 不做：

- 多用户协作
- 完整权限系统
- 大规模企业部署
- 复杂自动化工作流
- 完整移动端
- 直接复制 Khoj / Onyx / Quivr / Mem0 的代码结构

### 4.1 当前实现状态（Task 18 / Task 19 体检）

截至 Task 18 / Task 19 文档体检，当前仓库已经落地 MVP 后端主干能力、Memory API 和对话式 Web UI。后端测试、前端单元测试、前端 TypeScript 类型检查和 Playwright UI 主流程验收均已有通过结果；生产构建命令在当前沙箱中受 Node 写文件权限限制，需要在普通本地环境或 GitHub Actions 中复验。

已实现并有测试覆盖的能力包括：

- FastAPI 应用骨架与 `GET /health`。
- `config/sources.example.yaml` 配置契约与 `AppSettings` 读取。
- SQLite 元数据模型、Alembic 初始迁移和 repository 基础能力。
- 本地目录、笔记本地同步目录、Obsidian vault connector。
- 增量同步判断、Markdown / txt / PDF / docx / HTML parser、chunker、索引流水线。
- SQLite FTS5 关键词索引、`VectorStore` 接口、`ModelProvider` / `ModelRegistry` / `ModelRouter` 契约。
- `HybridRetriever`、`POST /search`、`GET /documents/{document_id}`、`GET /chunks/{chunk_id}`。
- `GET /sources`、`POST /sources`、`POST /index/run`、`GET /index/jobs`。
- `POST /chat` 的检索上下文、来源引用、无可靠来源保护和模型配置错误处理。
- `GET /memory`、`POST /memory`，以及 Chat 响应中的 `memories_used`。
- `search_notes`、`open_source`、`summarize_folder`、`build_topic_map` 四个 Agent Tools。
- `frontend/` React + Vite + TypeScript 对话式 Agent 工作台，包括对话页、引用抽屉、工具活动流、数据源管理入口和索引任务入口。
- `.github/workflows/ci.yml` GitHub Actions CI，用于后端、前端和文档基础质量门禁。

仍需后续补齐或增强的能力包括：

- Web UI 与真实后端、真实本地资料目录的浏览器端到端流程验收。
- 真实模型 provider HTTP 调用、真实 embedding 和持久化向量库。

## 5. 初始技术选型

### 5.1 后端

优先选择 Python + FastAPI。

原因：

- 文档解析、RAG、向量库、LLM SDK 生态成熟。
- 适合快速迭代本地 Agent。
- 后续可通过 API 给 Web UI、桌面端或 CLI 调用。

### 5.2 存储

MVP 推荐：

- SQLite：存文档元数据、任务状态、connector 状态、chunk 元数据。
- 本地文件缓存：存解析后的中间文本和必要缓存。
- 向量库先保持可替换接口，可先用 Chroma、LanceDB、Qdrant local 或 sqlite-vec。

早期不把系统绑定死在某个向量数据库上。

### 5.3 文档解析

MVP 支持：

- Markdown / txt：直接解析。
- PDF：优先 PyMuPDF。
- docx：python-docx。
- HTML：BeautifulSoup 或 readability 类解析器。

后续再考虑 unstructured、marker、OCR、图片内容理解等能力。

文档解析层必须通过 `ParserAdapter` 接口接入具体解析器。MVP 使用轻量 parser，后续可按文件类型和解析质量需要接入 MarkItDown、Docling、unstructured、marker 等成熟开源项目，避免重复造轮子。

### 5.4 RAG 组件

保持薄封装：

- parser
- chunker
- embedder
- lexical index
- vector index
- retriever
- reranker
- answer synthesizer

可以参考 LlamaIndex / LangChain / Quivr 的概念，但不要一开始把核心流程完全交给大型框架。

### 5.4.1 模型 Provider 与模型注册表

Embedding、LLM、rerank、vision 等模型能力必须通过 `ModelProvider`、`ModelRegistry`、`ModelCatalog` 和 `ModelRouter` 管理。

用户只需要配置 provider、API key、base URL 和偏好；系统负责发现模型、识别能力、缓存模型列表，并按 chat、embedding、rerank、vision、summary 等任务选择模型。

模型名称不应写死在业务代码中。MVP 支持 OpenAI-compatible provider 和 Ollama，本地模型与云端模型都走统一接口。

### 5.5 Agent 层

Agent 层负责把用户目标拆成工具调用。

初始工具：

- search_notes
- open_source
- summarize_folder
- build_topic_map
- remember_preference
- search_memory

后续再加：

- create_note
- update_note
- create_task
- schedule_digest
- web_research
- compare_sources

### 5.6 长期记忆

长期记忆设计参考 Mem0，但 MVP 可先自建简单 memory 表。

必要字段：

- memory_id
- memory_type
- user_id
- content
- source
- confidence
- created_at
- updated_at
- expires_at

后续如果需要更强的记忆抽取、冲突合并、多层记忆和评估，再考虑接入 Mem0 或实现兼容接口。

## 6. 阶段路线

### Phase 0: 项目骨架

- 建立后端项目结构。
- 建立配置文件。
- 建立 SQLite schema。
- 定义 Document、Chunk、Source、Memory 等核心模型。

### Phase 1: 本地目录知识库

- 多本地目录 connector。
- 笔记 App 本地同步目录 connector。
- 文档解析。
- chunk 和索引。
- 检索接口。
- 带引用的问答接口。
- 忽略规则和增量更新。

### Phase 2: Agent 工具化

- 把检索、总结、关联封装为工具。
- 支持 custom agent 配置。
- 引入长期记忆基础能力。

### Phase 3: 云端笔记接入

优先接入用户真实历史笔记最多、最常用的云端笔记源。

当前第一优先级：

- 有道云笔记：用户历史笔记主要沉淀在有道云笔记中，应作为第一批云端 connector。

如果有道云笔记官方 API 权限、开放范围或稳定性无法满足第一版需求，应先通过本地同步目录、导出文件或本地缓存接入有道云笔记资料，再把云端 API 作为增强能力逐步补齐。

后续候选：

- Notion
- 飞书文档
- 语雀
- OneNote
- Apple Notes

Notion 的 API 相对清晰，可以作为后续云端 connector 的参考样板，但不作为当前默认第一优先级。Obsidian vault 仍优先按本地 Markdown 笔记库或本地同步目录处理。

### Phase 4: 自动化与主动能力

- 每日/每周 digest。
- 新增资料自动总结。
- 重复主题发现。
- 待整理资料提醒。
- 项目上下文自动维护。
- 学习主题变化追踪。

### Phase 5: 高级检索与权限

- rerank。
- 多索引融合。
- 更细粒度的数据源权限。
- 敏感内容过滤。
- 可视化知识图谱或主题图。

## 7. 防跑偏原则

1. 不为了“像某个高星项目”而引入复杂度。
2. 不在 MVP 阶段追求企业级多用户能力。
3. 不把文档知识库和长期记忆混成一个不可解释的黑箱。
4. 不只做聊天 UI，必须保证 ingest、index、retrieve、cite 的闭环可靠。
5. 不只做向量搜索，必须保留关键词和元数据检索能力。
6. 不生成没有来源的知识库答案。
7. 不提前绑定某个云端笔记平台。
8. 不让框架决定产品形态，框架只服务核心体验。
9. 不为了快速 MVP 把扫描、解析、索引、检索、回答和 UI 混成一团。
10. 不把前端做成复杂后台系统或配置中心首页；主体验应保持对话式 Agent 工作台。

## 8. 当前决策记录

| 决策 | 结论 |
| --- | --- |
| 是否 fork 大项目 | 否，先做轻量 MVP |
| MVP 架构定位 | 长期目标架构上的最小垂直切片，不是临时 demo 架构 |
| 主产品方向 | Khoj 风格个人 second brain + custom agent |
| 扩展架构参考 | Onyx connector、后台同步、hybrid search、权限/数据源模型 |
| RAG 参考 | Quivr parser、chunk、retriever、vectorstore 抽象 |
| 长期记忆参考 | Mem0 风格 memory layer |
| 知识库与记忆边界 | 分开存储、分开索引、分开检索、合并使用 |
| 默认部署 | 本地优先，自托管 |
| 可迁移策略 | 本地索引可重建，云端笔记和导出备份作为长期迁移载体 |
| 初始后端 | Python + FastAPI |
| 初始元数据存储 | SQLite |
| 初始索引策略 | hybrid search 架构，关键词索引和向量库都必须可替换 |
| 初始关键词索引 | SQLite FTS5 + `LexicalIndex` 接口隔离 |
| 初始数据源 | 多个本地知识目录 + 笔记 App 本地同步目录 |
| 云端笔记策略 | 先保留 connector 接口，MVP 后第一批云端 connector 优先接入有道云笔记；云端 API 只作为同步入口 |
| 持续学习策略 | 增量索引 + 长期记忆 + 后续自动摘要和主题关联 |
| 初始前端体验 | 对话式 Agent 工作台为主入口，配置和管理能力收纳到侧栏、设置页或抽屉 |

## 9. 下一步

当前下一步不是重新创建项目骨架，也不是继续扩大前端页面，而是用真实后端和真实本地目录做端到端联调，并把真实模型 provider 接入排上日程。

建议优先处理：

1. 用真实后端和真实本地目录执行一次端到端验证：创建 source、运行索引、搜索、问答、打开来源、使用记忆。
2. push 到 GitHub 后查看 Actions 页面，确认 `CI` workflow 首次远端运行结果，并补齐生产构建输出验证。
3. 按 [mvp-acceptance-report.md](mvp-acceptance-report.md) 更新真实后端浏览器 E2E 和生产构建复验记录。
4. 推进真实模型 provider HTTP client，让 Chat API 从 fake client 验证进入真实模型调用验证。

## 10. 相关文档

- [project-design.md](project-design.md)：完整系统设计、模块拆分、技术选型原因、工期排布和验收标准。
- [cloud-note-connectors.md](cloud-note-connectors.md)：云端笔记 API 接入、同步、去重、增量更新和 Agent 边界设计。
- [knowledge-memory-separation.md](knowledge-memory-separation.md)：文档知识库与长期记忆的存储、索引、检索、性能和隐私边界设计。
- [document-parser-adapters.md](document-parser-adapters.md)：文档解析 adapter、开源解析器选型、解析质量评估和演进触发器。
- [model-provider-registry.md](model-provider-registry.md)：模型 provider、模型注册表、能力识别、密钥配置和任务路由设计。
- [conversational-agent-ui.md](conversational-agent-ui.md)：对话式 Agent UI 的信息架构、界面约束、知识 Agent 控件和验收标准。
- [note-import-export-strategy.md](note-import-export-strategy.md)：笔记导入导出、跨平台迁移、标准迁移包、格式边界和 adapter 设计。
- [mvp-implementation-plan.md](mvp-implementation-plan.md)：MVP 实施计划、任务拆解、阶段验收门和每周追踪模板。
- [mvp-acceptance-report.md](mvp-acceptance-report.md)：MVP 当前验收结果、风险和后续动作。
