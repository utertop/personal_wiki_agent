# Personal Wiki Agent

[![CI](https://github.com/utertop/personal_wiki_agent/actions/workflows/ci.yml/badge.svg)](https://github.com/utertop/personal_wiki_agent/actions/workflows/ci.yml)

Personal Wiki Agent 是一个本地优先、可持续学习、可主动协作的个人知识库 Agent 项目。

项目目标不是重做一个笔记 App，而是整合个人电脑上的多个知识目录、本地文档、笔记 App 本地同步目录、云端笔记 App、网页资料和长期对话上下文，让 Agent 帮助完成检索、总结、关联、生成和提醒。

## 当前状态

当前仓库已经完成 MVP 的主干能力：项目骨架、配置模型、SQLite 元数据模型、Alembic 迁移、本地目录 connector、增量同步判断、Markdown / txt / PDF / docx / HTML parser、chunk、SQLite FTS5、VectorStore 接口、ModelProvider 注册表、Hybrid Retriever、Search API、Chat API、基础 Agent Tools、Memory API 和对话式 Web UI。

Task 17 Memory API 已按最终契约集成并通过后端测试。Task 18 Web UI 已落地到 `frontend/`，并通过前端单元测试、TypeScript 类型检查和 Playwright UI 主流程验收；后端已补充本地 Vite Web UI 跨端口访问 FastAPI 的 CORS 配置。生产构建命令在当前沙箱中受 Node 写文件权限限制，需要在普通本地环境或 GitHub Actions 中复验。

### 已完成能力

- 后端 FastAPI 应用与 `GET /health` 健康检查。
- 配置契约：`config/sources.example.yaml` 可描述本地目录、笔记本地同步目录、Obsidian vault、模型 provider 和忽略规则。
- SQLite 模型：`Source`、`Document`、`Chunk`、`IndexJob`、`Memory` 已有基础 schema，其中 Memory 已通过 API 暴露最小创建和查询能力。
- 本地目录索引流水线：`IndexingPipeline` 可扫描本地 source、增量判断、解析文件、分块、写入元数据，并在配置 `SQLiteFtsIndex` 时写入关键词索引。
- 检索 API：`POST /search` 返回命中 chunk、分数、文档摘要、数据源摘要和 citation。
- 来源详情 API：`GET /documents/{document_id}` 与 `GET /chunks/{chunk_id}` 可打开来源。
- 问答 API：`POST /chat` 基于检索结果构造上下文，返回 `answer`、`citations`、`memories_used`、`confidence`、`retrieval_summary` 和 `model`。
- Chat 检索：英文自然问句会过滤 `can`、`help` 等弱问句词，避免因为非核心词导致可靠来源漏召回。
- Memory API：`POST /memory` 可创建长期记忆，`GET /memory` 可按 query、memory_type 和 limit 查询 active 且未过期的记忆。
- Agent Tools：`search_notes`、`open_source`、`summarize_folder`、`build_topic_map` 已作为后端工具函数实现。
- Source API：`GET /sources` 可列出数据源，`POST /sources` 可创建本地优先数据源。
- Index API：`POST /index/run` 返回 `202 Accepted` 并创建 `queued` 后台索引任务，`GET /index/jobs` 可查看最近索引任务状态。
- Web UI：`frontend/` 提供 React + Vite + TypeScript 对话式 Agent 工作台，包含对话页、引用抽屉、工具活动流、数据源管理入口和索引任务入口。

### 未完成或待后续增强

- 真实模型 HTTP 调用仍依赖后续 provider 客户端接入；当前测试使用 fake model client 验证 Chat API 契约。
- Web UI 真实后端浏览器 E2E 和生产构建输出写入仍需在普通本地环境或 GitHub Actions 中继续补充；本次执行环境拦截了长时间本地浏览器 E2E 命令，因此未把该项标为完成。
- 云端笔记 connector、自动写回云端笔记、OCR、复杂自动化工作流、企业级多用户和移动端不属于当前 MVP 已完成范围。

## 本地运行

以下命令以 Windows PowerShell 和仓库根目录为基准。

### 创建后端虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
Push-Location backend
..\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Pop-Location
```

项目目标 Python 版本为 3.11 或更高版本。

### 启动后端 API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

默认服务地址为 `http://127.0.0.1:8000`。健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

期望响应：

```json
{"status":"ok"}
```

### 后端测试

后端全量测试：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```

截至本次复验，后端全量测试为 `83 passed`。

如需只验证某个模块，可运行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_search_api.py -v
.\.venv\Scripts\python.exe -m pytest backend/tests/test_chat_api.py -v
.\.venv\Scripts\python.exe -m pytest backend/tests/test_agent_tools.py -v
```

## CI

仓库已配置 GitHub Actions 工作流 [.github/workflows/ci.yml](.github/workflows/ci.yml)，在 push、pull request 和手动触发时运行。

CI 当前包含三类检查：

- Backend：Python 3.11，安装 `backend[dev]`，运行 `python -m pytest backend/tests -q`。
- Frontend：Node 22，运行 `npm ci`、`npm test`、`npm exec tsc -- --noEmit` 和 `npm run build`。
- Docs：检查已跟踪文本文件中的乱码替换字符、合并冲突标记，以及 Markdown 本地相对链接。

当前项目本地仍以手动运行和本地优先开发为主，CI 只做质量门禁；暂不做自动部署。

## 配置

配置样例位于 [config/sources.example.yaml](config/sources.example.yaml)。它展示了三类本地优先数据源：

- `local_directory`：普通本地知识目录。
- `local_synced_notes`：笔记 App 同步到本机的目录。
- `obsidian_vault`：Obsidian vault，本质上仍按本地 Markdown 笔记库处理。

样例还包含：

- `data_dir`：本地数据目录。
- `database_url`：SQLite 数据库连接串。
- `model`：聊天模型、embedding 模型和本地模型 provider 偏好。
- `privacy.ignore_patterns`：全局忽略规则，用于排除临时文件、缓存目录和敏感路径。

当前 FastAPI 默认启动时使用安全默认配置；配置文件读取能力已经在 `backend/app/core/settings.py` 中实现。MVP 现在提供 `GET /sources` 和 `POST /sources` 管理数据库 source。将 YAML 配置自动导入数据库 source 仍是后续增强能力。

## 本地目录索引

当前可用的索引入口包括后端内部 `IndexingPipeline` 和 HTTP API：

- 扫描 `Source` 表中启用的数据源。
- 通过 connector 发现文件。
- 使用增量判断识别新增、更新、删除和未变化文件。
- 调用 parser 解析 Markdown / txt / PDF / docx / HTML。
- 调用 chunker 分块并写入 `Document`、`Chunk` 和 `IndexJob`。
- 可选写入 `SQLiteFtsIndex`，供 `POST /search` 使用。

开发验证可参考 [backend/tests/test_indexing_pipeline.py](backend/tests/test_indexing_pipeline.py) 和 [backend/tests/test_source_index_api.py](backend/tests/test_source_index_api.py)。

创建本地目录数据源：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/sources `
  -ContentType "application/json" `
  -Body '{"source_type":"local_directory","name":"本地资料","uri":"E:/Knowledge"}'
```

触发后台索引并查看任务：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/index/run `
  -ContentType "application/json" `
  -Body '{"source_id":1}'

Invoke-RestMethod http://127.0.0.1:8000/index/jobs
```

`POST /index/run` 不在请求内长时间阻塞索引；它会先返回排队任务，实际扫描和写入由后台任务继续执行。前端或 CLI 可轮询 `GET /index/jobs` 查看 `queued`、`running`、`completed`、`completed_with_errors` 或 `failed` 状态。

## 搜索

启动后端并准备好数据库中的文档和 FTS 索引后，可调用：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/search `
  -ContentType "application/json" `
  -Body '{"query":"RAG","top_k":5}'
```

响应包含：

- `query`：原始查询。
- `top_k`：返回数量上限。
- `results`：命中列表。
- `citation`：可追溯到 `document_id`、`chunk_id`、`source_id`、标题路径、页码和片段。
- `document` 与 `source`：前端或 Agent 打开来源所需的摘要信息。

支持的过滤条件包括 `source_id`、`document_id`、`file_type` 和 `top_k`。

## 问答

`POST /chat` 会先检索知识库，再基于检索结果构造回答上下文：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/chat `
  -ContentType "application/json" `
  -Body '{"message":"RAG 怎么帮助个人知识库？","top_k":5}'
```

响应字段：

- `answer`：回答正文。
- `citations`：来自文档知识库的来源引用。
- `memories_used`：来自长期记忆的个性化上下文，不作为文档来源引用。
- `confidence`：当前回答可信度估计。
- `retrieval_summary`：检索命中、使用数量、来源数量和是否有可靠来源。
- `model`：实际使用的模型名；没有可靠来源时可以为 `null`。

如果没有可靠来源，接口会返回明确说明，不会伪造引用。如果有来源但没有配置可用 chat model，会返回结构化 `503` 配置错误。

## Agent Tools

当前后端提供四个基础 Agent 工具函数，供后续 custom agent 或 Web UI 编排：

- `search_notes`：调用 Hybrid Retriever 和 FTS 索引，返回可追溯检索结果。
- `open_source`：按 `document_id` 或 `chunk_id` 打开来源详情。
- `summarize_folder`：按数据源或路径收集 chunk，生成带引用摘要；没有外部模型时提供本地抽取式 fallback。
- `build_topic_map`：按 heading 或文档标题聚合轻量主题地图。

开发验证可参考 [backend/tests/test_agent_tools.py](backend/tests/test_agent_tools.py)。这些工具目前是后端函数，不是独立 HTTP 路由。

## Memory

长期记忆的设计原则是与文档知识库分离：文档 chunk 不写入 memory 表，长期记忆不混入 document chunk 索引。

当前 Memory API 已按 Task 17 最终契约集成：

- `POST /memory`：请求体为 `{memory_type, content, source, confidence?, expires_at?}`，返回创建后的单条 memory。
- `GET /memory?query=&memory_type=&limit=`：返回 `{items:[...]}`，只包含 active 且未过期的 memory。
- 支持的 `memory_type` 为 `user_preference`、`project_context`、`workflow_habit`、`stable_fact`。
- `POST /chat` 响应包含 `memories_used: []`，用于和文档来源 `citations` 区分。

Memory 验收已通过 `backend/tests/test_memory.py` 和 `backend/tests/test_chat_api.py` 覆盖。

## Web UI

`frontend/` 已提供 React + Vite + TypeScript 对话式 Agent 工作台，主入口是对话，不是复杂后台配置页。

本地前端命令如下：

```powershell
cd frontend
npm install
npm run dev
npm test
npm run build
```

当前已验证：

- `npm.cmd test` 通过，覆盖 API client、工具活动流、对话视图、数据源视图和索引任务视图。
- `npm.cmd exec tsc -- --noEmit` 通过，前端 TypeScript 类型检查通过。
- Python Playwright UI 主流程脚本通过，覆盖默认 Chat 页、发送问题、展示引用、打开来源抽屉、创建数据源和触发索引任务；本次 API 使用浏览器路由 mock。
- `npm.cmd run build` 在当前沙箱中进入 Vite 构建输出阶段后，被 Node 写文件权限限制拦截；该命令需要在普通本地环境或 GitHub Actions 中复验。

真实后端浏览器 E2E 后续还需要确认：

- 默认进入对话式 Agent 主界面。
- 能发送问题并展示回答。
- 能展示 citations。
- 点击 citation 可以打开来源详情抽屉。
- 工具活动流可见且不干扰主对话。

## 打包与运行说明

后端当前按本地虚拟环境运行和测试，不提供独立安装包。后端打包或交付前至少执行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```

前端打包命令为：

```powershell
Push-Location frontend
npm run build
Pop-Location
```

## 文档入口

- [docs/technical-direction.md](docs/technical-direction.md)：技术路线、范围边界和防跑偏原则。
- [docs/project-design.md](docs/project-design.md)：系统设计、模块划分、API 和验收标准。
- [docs/mvp-implementation-plan.md](docs/mvp-implementation-plan.md)：MVP 任务拆解和阶段记录。
- [docs/mvp-acceptance-report.md](docs/mvp-acceptance-report.md)：当前 MVP 验收报告。
- [docs/conversational-agent-ui.md](docs/conversational-agent-ui.md)：对话式 Web UI 设计。
- [docs/knowledge-memory-separation.md](docs/knowledge-memory-separation.md)：文档知识库与长期记忆边界。
- [rules.md](rules.md)：开发与文档约束。
