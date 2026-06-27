# MVP 验收报告

## 验收口径

本报告记录 MVP 文档、验收、打包和 CI 体检结果。验收日期为 2026-06-26，工作区为 `E:\Automatic\personal_wiki_agent`。

当前结论：

- Task 1 到 Task 17 的后端主干能力已有实现和测试覆盖。
- Task 17 Memory API 已按最终契约完成：`POST /memory` 创建记忆，`GET /memory` 查询 active 且未过期记忆，`POST /chat` 响应包含 `memories_used`。
- Task 18 Web UI 已落地到 `frontend/`：提供 React + Vite + TypeScript 对话式 Agent 工作台，并通过前端测试、TypeScript 类型检查和 Playwright UI 主流程验收；后端已补充本地 Vite Web UI 跨端口访问 FastAPI 的 CORS 配置，生产构建输出写入需要在普通本地环境或 GitHub Actions 中复验。
- Task 21 CI 已落地到 `.github/workflows/ci.yml`：push、pull request 和手动触发时运行后端、前端和文档基础检查。
- 本报告不把目标 API、设计文档中的长期能力或并行任务预期写成已完成能力。

## 已执行验证

| 验证命令 | 当前结果 | 说明 |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m pytest backend/tests -q` | 通过；`83 passed` | 用于验证 Task 1 到 Task 20 的后端能力，以及本地 Web UI CORS 和 Chat 英文自然问句检索回归。 |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/test_memory.py -q` | 通过；`6 passed` | 用于验证 Task 17 Memory API、过滤规则、过期规则和 Chat `memories_used`。 |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/test_chat_api.py -q` | 通过；`5 passed` | 用于回归验证 Chat API 引用、无来源保护、模型配置错误和英文自然问句弱词过滤。 |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/test_cors.py -q` | 通过；`1 passed` | 用于验证本地 Vite Web UI 可以跨端口访问 FastAPI API。 |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/test_source_index_api.py -q` | 通过；`5 passed` | 用于验证 Source / Index API、后台索引排队和索引后搜索闭环。 |
| `npm.cmd test` | 通过；5 个测试文件、8 个测试通过 | 用于验证前端 API client、工具活动流、对话视图、数据源视图和索引任务视图。 |
| `npm.cmd exec tsc -- --noEmit` | 通过 | 用于验证 Task 18 前端 TypeScript 类型检查。 |
| Python Playwright UI 主流程脚本 | 通过；`OK: Playwright UI main flow passed` | 使用 Vite dev server、Chrome 和浏览器路由 mock API，验证默认 Chat 页、发送问题、展示引用、打开来源抽屉、创建数据源和触发索引任务。 |
| `npm.cmd run build` | 未完成当前沙箱验证；Vite 已进入输出阶段，但 Node 写文件被 `EPERM` 拦截 | 失败点是当前沙箱禁止 Node 写入构建文件；需在普通本地环境复验生产构建输出。 |
| `.\.venv\Scripts\python.exe -c "import yaml; ..."` | 通过 | 用于验证 GitHub Actions workflow YAML 可解析。 |
| `rg -n "<替换字符>" README.md docs rules.md` | 通过；无匹配 | 实际执行时使用 Unicode 替换字符，用于确认 Markdown 中没有乱码替换字符。 |
| 本地文档与文本卫生脚本 | 通过；`OK: docs and tracked text files passed hygiene checks` | 用于检查已跟踪文本文件中的乱码替换字符、合并冲突标记，以及 Markdown 本地相对链接目标存在。 |

## 模块验收清单

| 任务 / 模块 | 验收项 | 验证方式 | 当前结果 | 风险和后续动作 |
| --- | --- | --- | --- | --- |
| Task 1 工程骨架 | FastAPI 应用可创建，`GET /health` 可用。 | `backend/tests/test_health.py`；后端主干测试。 | 通过。 | 后端 README 曾停留在“只提供健康检查”口径，顶层 README 已改为当前能力口径。 |
| Task 2 配置系统 | 可读取 YAML 配置，支持本地目录、同步笔记目录、Obsidian vault、模型和忽略规则。 | `backend/tests/test_settings.py`；检查 `config/sources.example.yaml`。 | 通过。 | YAML 自动导入数据库 source 仍是后续增强；当前已可通过 Source API 创建数据库 source。 |
| Task 3 数据库与核心模型 | `Source`、`Document`、`Chunk`、`IndexJob`、`Memory` 模型可建表并基础读写。 | `backend/tests/test_models.py`。 | 通过。 | Memory API 已在 Task 17 完成，仍需在后续迁移中维护 schema 演进。 |
| Task 4 Alembic 迁移 | 初始 schema 可 upgrade / downgrade。 | `backend/tests/test_migrations.py`。 | 通过。 | 后续新增 Memory API 字段或前端所需字段时需追加迁移。 |
| Task 5 Connector | 本地目录、笔记本地同步目录、Obsidian vault 可扫描并保留来源元数据。 | `backend/tests/test_connectors_base.py`。 | 通过。 | 云端 connector 不属于当前已完成范围。 |
| Task 6 增量同步 | 可识别新增、更新、删除、未变化和疑似移动。 | `backend/tests/test_sync_detection.py`。 | 通过。 | 移动识别当前是候选能力，真实合并策略后续仍需增强。 |
| Task 7 ParserAdapter | Markdown / txt / PDF / docx / HTML 可解析为统一结果。 | `backend/tests/test_parsers.py`。 | 通过。 | OCR、扫描版 PDF、复杂版式解析不属于当前 MVP 已完成范围。 |
| Task 8 Chunker | 可按标题、段落和页码生成 chunk。 | `backend/tests/test_chunker.py`。 | 通过。 | 后续需按真实资料规模评估 chunk 大小和中文质量。 |
| Task 9 索引流水线 | 可扫描 source、解析文件、写入 document/chunk/job，并可接入 FTS。 | `backend/tests/test_indexing_pipeline.py`。 | 通过。 | 流水线仍可被内部同步调用；HTTP 层已通过后台任务避免请求长时间阻塞。 |
| Task 10 LexicalIndex / FTS5 | SQLite FTS5 可索引、检索、替换、删除 chunk。 | `backend/tests/test_sqlite_fts.py`。 | 通过。 | 中文检索质量仍需真实语料评估，后续可接 Tantivy / Meilisearch adapter。 |
| Task 11 VectorStore 接口 | Hashing embedder 与内存型向量库满足接口契约。 | `backend/tests/test_vector_store_contract.py`。 | 通过。 | 当前不代表真实语义 embedding 质量，真实向量库接入需后续验证。 |
| Task 12 ModelProvider | OpenAI-compatible / Ollama provider 配置、catalog 和 router 契约可用。 | `backend/tests/test_model_registry.py`。 | 通过。 | 真实 OpenAI-compatible 或 Ollama HTTP 调用仍待 provider client 实现验证。 |
| Task 13 Hybrid Retriever | 可合并关键词和向量命中，支持过滤和空查询。 | `backend/tests/test_hybrid_retriever.py`。 | 通过。 | 当前主路径依赖 FTS；真实向量召回质量待后续接入验证。 |
| Task 14 Search API 与来源详情 | `POST /search`、`GET /documents/{document_id}`、`GET /chunks/{chunk_id}` 返回可追溯结果。 | `backend/tests/test_search_api.py`。 | 通过。 | Source / Index 管理 API 已在 Task 20 补齐。 |
| Task 15 Chat API | `POST /chat` 返回 `answer`、`citations`、`memories_used`、`confidence`、`retrieval_summary`；无可靠来源时不伪造引用；英文自然问句会过滤弱问句词以减少漏召回。 | `backend/tests/test_chat_api.py`、`backend/tests/test_memory.py`。 | 通过。 | 真实模型 provider HTTP 调用仍需后续验证。 |
| Task 16 Agent Tools | `search_notes`、`open_source`、`summarize_folder`、`build_topic_map` 可作为后端工具函数使用。 | `backend/tests/test_agent_tools.py`。 | 通过。 | 当前是函数级工具，不是独立 HTTP API；后续如果需要从 Web UI 直接调用，需补稳定 HTTP 或 Agent 编排入口。 |
| Task 17 Memory API | `POST /memory` 创建记忆；`GET /memory` 按 query、memory_type、limit 查询 active 且未过期记忆；Chat 响应区分 `citations` 和 `memories_used`。 | `backend/tests/test_memory.py`；后端全量测试。 | 通过；`test_memory.py` 6 passed，全量后端测试 83 passed。 | 后续需在 Web UI 中提供记忆管理入口，并继续保持文档引用与记忆上下文分离。 |
| Task 18 Web UI | `frontend/` React + Vite + TypeScript 对话式 Agent 工作台，包含对话页、引用抽屉、工具活动流、数据源管理入口和索引任务入口；后端允许本地 Vite 开发源跨端口访问 API。 | `npm.cmd test`；`npm.cmd exec tsc -- --noEmit`；Python Playwright UI 主流程脚本；`backend/tests/test_cors.py`；`npm.cmd run build`。 | 主流程通过；5 个测试文件、8 个测试通过，TypeScript 类型检查通过，Playwright UI 主流程通过，CORS 回归通过；生产构建输出写入被当前沙箱 Node 权限拦截。 | Playwright 当前验证的是前端 UI 主流程，API 为浏览器路由 mock；真实后端浏览器 E2E 本次被当前执行环境拦截，仍需在普通本地环境或 GitHub Actions 中复验；`npm.cmd run build` 也需复验。 |
| Task 19 文档与打包 | README、路线文档、设计文档、实施计划和验收报告口径一致。 | 文档体检、替换字符检查、本地 Markdown 链接解析、后端和前端验证命令。 | 通过。 | 后续路线、需求或 API 状态变化时继续执行文档一致性体检。 |
| Task 20 Source / Index API 与 Web UI 接入 | `GET /sources`、`POST /sources`、`POST /index/run`、`GET /index/jobs` 可用，Web UI 数据源页和索引页接入真实 API。 | `backend/tests/test_source_index_api.py`；`frontend/src/api/client.test.ts`；`SourcesView.test.tsx`；`IndexJobsView.test.tsx`。 | 通过；`POST /index/run` 已返回 `202 Accepted` 和 `queued` job，并由后台任务执行实际索引。 | 当前后台执行使用 FastAPI BackgroundTasks，适合本地 MVP；后续如需更强可靠性可演进为持久化任务队列和独立 worker。 |
| Task 21 GitHub Actions CI | push、pull request 和手动触发时自动检查后端、前端和文档基础质量。 | `.github/workflows/ci.yml`；YAML 解析检查；本地同等命令验证。 | 已配置。 | GitHub 远端首次运行结果需要 push 后在 Actions 页面确认；CI 暂不做自动部署。 |

## 已完成能力

- 后端可启动并暴露健康检查、搜索、问答和来源详情 API。
- Memory API 可创建和查询长期记忆，Chat API 可返回 `memories_used`。
- 本地目录索引主干可通过 `IndexingPipeline` 验证。
- Source / Index API 可创建数据源、触发后台索引并查看任务状态。
- 关键词检索、来源引用、回答上下文和 Agent Tools 已形成后端闭环。
- 文档知识库与长期记忆在模型层保持分离。
- Web UI 已形成对话式工作台，数据源页和索引任务页已接入真实 API，并通过前端测试、TypeScript 类型检查和 Playwright UI 主流程验收。
- GitHub Actions CI 已配置后端、前端和文档基础检查。
- 项目文档已补充当前状态、待集成边界、运行命令和验收报告。

## 未完成能力

- Web UI 生产构建输出写入和真实后端浏览器 E2E；本次执行环境拦截了长时间本地浏览器 E2E 命令，因此该项仍未标为完成。
- 真实模型 provider HTTP 调用、真实 embedding 和持久化向量库。
- 云端笔记 connector、自动写回、OCR、复杂自动化和企业级能力。

## 文档一致性体检

| 文档 | 体检结果 | 后续动作 |
| --- | --- | --- |
| [../README.md](../README.md) | 已更新为当前入口文档，区分已完成能力、待后续增强能力、后端测试、本地索引、搜索、问答、Agent Tools、Memory 和 Web UI。 | Source / Index API 或真实模型接入后继续更新。 |
| [technical-direction.md](technical-direction.md) | 已补充 Task 20 当前实现状态，并把下一步修正为真实本地目录端到端验证和真实模型 provider。 | 后续路线变化时继续作为 source of truth。 |
| [project-design.md](project-design.md) | 已区分 MVP 目标 API 和当前已注册 API，补充 Memory、Source / Index 最终契约和 Web UI 已验证状态，并链接本报告。 | 后续新增 API 后更新当前实现状态。 |
| [mvp-implementation-plan.md](mvp-implementation-plan.md) | 已修正过期推进顺序，补充 Task 17、Task 18、Task 20 和 Task 21 完成记录。 | 后续端到端验收后更新对应任务状态。 |
| [../rules.md](../rules.md) | 规则口径仍与当前路线一致：中文 Markdown、UTF-8、本地优先、文档知识库与记忆分离、对话式前端。 | 暂无必须修改项。 |

## 打包与运行说明

后端推荐本地虚拟环境运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
Push-Location backend
..\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Pop-Location
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

后端全量测试：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

前端本地运行与打包命令：

```powershell
cd frontend
npm install
npm run dev
npm run build
```

本次已验证 `npm.cmd test`、`npm.cmd exec tsc -- --noEmit` 和 Python Playwright UI 主流程脚本。`npm.cmd run build` 在当前沙箱中被 Node 写文件权限拦截，需要在普通本地环境或 GitHub Actions 中复验。`npm run dev` 用于本地手动浏览器验收，本报告不保留常驻开发服务器。

## 后续动作

1. 补充真实后端浏览器 E2E，验证真实本地目录索引、搜索、问答、来源抽屉和记忆使用结果。
2. 在普通本地 PowerShell 环境或 GitHub Actions 复验 `npm run build`。
3. 接入真实模型 provider HTTP client，验证 Chat API 的真实模型调用。
4. 后续如本地 MVP 索引耗时继续增加，再把 FastAPI BackgroundTasks 演进为持久化任务队列和独立 worker。
5. push 后查看 GitHub Actions `CI` workflow 首次远端运行结果，并把结果回写到本报告。
