# Personal Wiki Agent 优化执行计划

本文档用于把当前项目审核结论转成可连续执行的优化路线。每个阶段都包含目标、范围、建议改动文件、验收命令和 checklist。执行时建议一次只推进一个阶段，完成后更新本文件、[mvp-acceptance-report.md](mvp-acceptance-report.md) 和必要的 README 状态。

## 当前基线

当前项目已达到本地 MVP 可用状态：

- 后端主干能力已覆盖健康检查、配置、数据模型、索引、检索、Chat、Memory、Source / Index API、ModelProvider 和 Agent Tools。
- 前端已提供 Chat、数据源、索引任务和 Memory 管理 UI。
- 真实后端 Playwright E2E 已覆盖 Memory 新增/筛选、source 创建、索引、Chat、引用和来源抽屉。
- 本地质量门禁已通过：后端测试、前端单测、类型检查、生产构建、Playwright E2E 和文档卫生检查。

最近审核验证命令：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm.cmd test
npm.cmd exec tsc -- --noEmit
npm.cmd run build
npm.cmd run test:e2e
```

当前主要短板：

- CI 尚未运行 Playwright E2E。
- Memory 只有创建和查询，缺少归档、删除和更新。
- OpenAI-compatible 与 Ollama provider 的 prompt 构造重复。
- 真实 embedding 与 SQLite 持久化向量库已完成第一版接入，后续可评估 sqlite-vec / Chroma 等更大规模实现。
- 索引后台任务仍使用 FastAPI BackgroundTasks，可靠性有限。

## 执行原则

- 先加固质量门禁，再扩大功能面。
- 每个阶段都要有自动化测试或可重复 smoke test。
- 不把文档知识库和长期记忆混成同一个来源体系。
- 不在前端承诺后端尚未提供的能力。
- 每完成一个阶段，更新验收报告中的结果、风险和后续动作。

## Phase 1: CI 加固 Playwright E2E

优先级：P0

目标：让 GitHub Actions 能自动发现真实后端浏览器主链路回归。

建议范围：

- 修改 `.github/workflows/ci.yml`。
- 在 frontend job 中安装 Playwright Chromium。
- 在构建后运行 `npm run test:e2e`。
- 如 CI 时间过长，可单独增加 `e2e` job，并依赖 backend/frontend 基础 job。

建议改动：

- `.github/workflows/ci.yml`
  - 在 `npm ci` 后增加 `npx playwright install --with-deps chromium`。
  - 在 `npm run build` 后增加 `npm run test:e2e`。
  - 保持 E2E 使用现有 `frontend/playwright.config.ts`，由 webServer 启动 FastAPI E2E 服务和 Vite。

验收命令：

```powershell
cd frontend
npm.cmd run test:e2e
```

远端验收：

- push 后打开 GitHub Actions。
- 确认 `CI` workflow 的 frontend 或 e2e job 通过。
- 如果 Linux 依赖缺失，优先修复 `playwright install --with-deps chromium`。

Checklist:

- [x] CI 安装 Playwright Chromium。
- [x] CI 执行 `npm run test:e2e`。
- [x] E2E job 失败时上传 Playwright trace 或 test-results artifact。
- [x] README 的 CI 说明补充 E2E 覆盖范围。
- [ ] `docs/mvp-acceptance-report.md` 记录远端 CI 首次运行结果。

## Phase 2: Memory 完整管理能力

优先级：P1

目标：让长期记忆可以被修正、归档和删除，避免错误记忆长期污染回答。

建议范围：

- 后端新增 Memory 更新和删除契约。
- 前端 Memory 管理页接入归档、删除和编辑。
- E2E 覆盖归档后不再出现在 active 列表。

建议 API 契约：

- `PATCH /memory/{memory_id}`
  - 请求体：`{content?, source?, confidence?, expires_at?, status?}`
  - `status` 允许值：`active`、`archived`
  - 返回更新后的 memory。
- `DELETE /memory/{memory_id}`
  - 建议第一版做软删除：把 `status` 置为 `deleted`。
  - 返回 `204 No Content` 或 `{ok:true}`，二选一后固定。

建议改动文件：

- `backend/app/memory/store.py`
  - 增加 `update_memory(...)`。
  - 增加 `archive_memory(memory_id)` 或通用 status 更新。
  - 增加 `delete_memory(memory_id)`，第一版软删除。
- `backend/app/api/routes_memory.py`
  - 增加 `PATCH /memory/{memory_id}`。
  - 增加 `DELETE /memory/{memory_id}`。
- `backend/tests/test_memory.py`
  - 覆盖更新、归档、删除、不存在 ID、非法 status。
- `frontend/src/api/client.ts`
  - 增加 `updateMemory` 和 `deleteMemory`。
- `frontend/src/views/MemoryView.tsx`
  - 增加归档/删除按钮。
  - 可选增加简洁编辑表单。
- `frontend/src/views/MemoryView.test.tsx`
  - 覆盖归档/删除交互。
- `frontend/e2e/real-backend.spec.ts`
  - 覆盖创建后归档，确认列表不再展示。

验收命令：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_memory.py -q
cd frontend
npm.cmd test -- MemoryView.test.tsx
npm.cmd run test:e2e
```

Checklist:

- [x] Memory store 支持更新。
- [x] Memory store 支持归档。
- [x] Memory store 支持软删除。
- [x] API 对不存在 memory 返回 404。
- [x] API 对非法 status 返回 422。
- [x] `GET /memory` 默认只返回 active 且未过期记录。
- [x] 前端可以归档一条 memory。
- [x] 前端可以删除一条 memory。
- [x] E2E 验证归档或删除后列表刷新。
- [x] 文档明确 Memory 不作为 citation 来源。

## Phase 3: Provider Prompt Builder 去重

优先级：P1

目标：把 OpenAI-compatible 与 Ollama provider 共用的 prompt 构造逻辑抽成单一模块，避免后续提示词、引用格式和 Memory 注入规则分叉。

当前问题：

- `backend/app/llm/openai_provider.py` 和 `backend/app/llm/ollama_provider.py` 都有 `_build_messages` 与 `_format_context_item`。
- 两个 provider 只应该保留协议差异：URL、payload 外壳、鉴权、response parsing。

建议改动文件：

- 新增 `backend/app/llm/prompt_builder.py`
  - `build_chat_messages(question: str, context: AnswerContext) -> list[dict[str, str]]`
  - `format_context_item(index: int, item: AnswerContextItem) -> str`
- 修改 `backend/app/llm/openai_provider.py`
  - 删除本地 `_build_messages` 和 `_format_context_item`。
  - 使用 `build_chat_messages(...)`。
- 修改 `backend/app/llm/ollama_provider.py`
  - 删除本地 `_build_messages` 和 `_format_context_item`。
  - 使用 `build_chat_messages(...)`。
- 修改或新增 `backend/tests/test_model_registry.py`
  - 确认两个 provider 发出的 messages 一致。

验收命令：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_model_registry.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\test_chat_api.py -q
```

Checklist:

- [x] prompt builder 单测覆盖 citations 和 personalization memory。
- [x] OpenAI-compatible provider 使用共享 prompt builder。
- [x] Ollama provider 使用共享 prompt builder。
- [x] provider 专属 response parsing 保持独立。
- [x] Chat API 回归测试通过。
- [ ] 真实模型 smoke test 的 prompt 行为没有破坏。

## Phase 4: 真实 Embedding 与持久化向量库

优先级：P2

目标：提升语义召回质量，让 hybrid search 不只依赖 SQLite FTS 和测试用 HashingEmbedder。

建议先做选择：

- 本地轻量优先：`sqlite-vec`
  - 优点：SQLite 体系内，部署简单。
  - 风险：Windows 和 CI 安装验证需要先试。
- 快速验证优先：Chroma local
  - 优点：生态成熟，容易验证语义检索。
  - 风险：依赖稍重，数据目录管理要清楚。

建议执行顺序：

1. 先保留现有 `VectorStore` 接口不变。
2. 新增一个持久化实现，不替换已有 `InMemoryVectorStore`。
3. 新增 embedding provider client，用配置选择真实 embedding 模型。
4. 建立一个小型检索评测集，验证中文和英文查询召回。
5. 再把 indexing pipeline 接入真实向量写入。

建议改动文件：

- `backend/app/indexing/embedding.py`
  - 增加真实 embedding client adapter 或桥接 LLM provider embedding client。
- `backend/app/indexing/vector_store.py`
  - 增加持久化 vector store 实现，或新建专门文件。
- `backend/app/indexing/pipeline.py`
  - 索引时写入持久化向量库。
- `backend/app/retrieval/hybrid.py`
  - 保持 hybrid 合并逻辑，增加真实向量命中的回归测试。
- `backend/tests/test_vector_store_contract.py`
  - 复用 contract 覆盖新 vector store。
- `backend/tests/test_hybrid_retriever.py`
  - 增加真实向量命中参与排序的测试。

验收命令：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_vector_store_contract.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\test_hybrid_retriever.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\test_indexing_pipeline.py -q
```

Checklist:

- [x] 选定第一版持久化向量库。
- [x] 新增 vector store 实现，不破坏现有接口。
- [x] 新增真实 embedding 调用路径。
- [x] 配置中能声明 embedding provider/model。
- [x] 索引 pipeline 能写入向量。
- [x] HybridRetriever 能读真实向量命中。
- [x] 没配置向量库时仍能只用 FTS 工作。
- [x] 增加小型检索评测 fixture。
- [x] README 说明如何开启真实 embedding。

## Phase 5: 索引任务可靠性升级

优先级：P2

目标：从本地 MVP 后台任务升级到可恢复、可重试、可取消的索引任务系统。

当前边界：

- `POST /index/run` 创建 queued job。
- FastAPI BackgroundTasks 调用 `run_queued_index_jobs(...)` 执行。
- 适合本地 MVP，但进程崩溃、重试、并发控制和取消能力有限。

建议能力：

- job 状态：`queued`、`running`、`completed`、`failed`、`cancelled`。
- job 字段：`attempt_count`、`max_attempts`、`last_heartbeat_at`、`cancel_requested_at`。
- 后台 runner：启动时扫描 queued / stale running job。
- UI：支持重试 failed job、取消 queued/running job。

建议改动文件：

- `backend/app/models/index_job.py`
- `backend/alembic/versions/...`
- `backend/app/repositories/index_jobs.py`
- `backend/app/api/routes_index.py`
- `backend/app/indexing/pipeline.py`
- `frontend/src/views/IndexJobsView.tsx`
- `backend/tests/test_source_index_api.py`
- `frontend/src/views/IndexJobsView.test.tsx`

验收命令：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_source_index_api.py -q
cd frontend
npm.cmd test -- IndexJobsView.test.tsx
npm.cmd run test:e2e
```

Checklist:

- [ ] 数据库迁移增加任务可靠性字段。
- [ ] 后端支持取消任务。
- [ ] 后端支持重试 failed job。
- [ ] runner 能处理 stale running job。
- [ ] 单个 source 失败不阻断其他 source。
- [ ] UI 展示 failed reason 和重试入口。
- [ ] E2E 覆盖一次索引任务成功路径。
- [ ] 文档明确 BackgroundTasks 与后续 runner 的边界变化。

## Phase 6: 更长链路真实资料夹回归

优先级：P2

目标：用更接近真实使用的数据规模验证索引、检索、问答和 UI 的稳定性。

建议方式：

- 准备一个本地测试资料夹，包含 Markdown、txt、PDF、docx、HTML。
- 文件数量先控制在 20 到 50。
- 建立 5 到 10 个固定问题和期望命中文档。
- 不把用户私密资料提交到仓库，只提交匿名 fixture 或生成脚本。

建议改动文件：

- `backend/tests/fixtures/` 或 `.codex_tmp/` 生成脚本。
- `backend/tests/test_indexing_pipeline.py`
- `frontend/e2e/real-backend.spec.ts`
- `docs/mvp-acceptance-report.md`

验收命令：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\test_indexing_pipeline.py -q
cd frontend
npm.cmd run test:e2e
```

Checklist:

- [x] 准备多格式测试资料夹。
- [x] 覆盖至少 5 个固定查询。
- [x] 验证索引后 source/document/chunk 数量合理。
- [x] 验证 Chat citations 指向正确 document/chunk。
- [x] 验证 UI 不因长路径、长标题、长引用片段布局破裂。
- [x] 文档记录真实资料夹回归结果。

## 总体验收清单

每完成一个阶段，至少执行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm.cmd test
npm.cmd exec tsc -- --noEmit
npm.cmd run build
npm.cmd run test:e2e
```

文档卫生检查：

```powershell
@'
import re
import subprocess
from pathlib import Path

text_suffixes = {
    ".css",
    ".html",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".yml",
    ".yaml",
}
tracked_files = [
    filename
    for filename in subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    if Path(filename).exists()
]

hygiene_errors = []
for filename in tracked_files:
    path = Path(filename)
    if path.suffix.lower() not in text_suffixes:
        continue
    text = path.read_text(encoding="utf-8")
    if "\ufffd" in text:
        hygiene_errors.append(f"{filename}: contains replacement character")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
            hygiene_errors.append(f"{filename}:{line_number}: merge conflict marker")

link_errors = []
markdown_files = [Path(filename) for filename in tracked_files if filename.endswith(".md")]
link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
for path in markdown_files:
    text = path.read_text(encoding="utf-8")
    for match in link_pattern.finditer(text):
        target = match.group(1).strip().strip("<>")
        if not target or "://" in target or target.startswith("#") or target.startswith("mailto:"):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        if not resolved.exists():
            link_errors.append(f"{path}:{target} -> {resolved}")

errors = hygiene_errors + link_errors
if errors:
    raise SystemExit("\n".join(errors))
print("OK: docs and tracked text files passed hygiene checks")
'@ | .\.venv\Scripts\python.exe -
```

## 推荐执行顺序

1. Phase 1: CI 加固 Playwright E2E。
2. Phase 3: Provider Prompt Builder 去重。
3. Phase 2: Memory 完整管理能力。
4. Phase 6: 更长链路真实资料夹回归。
5. Phase 4: 真实 embedding 与持久化向量库。
6. Phase 5: 索引任务可靠性升级。

如果只安排一轮短期优化，建议先做 Phase 1 和 Phase 3。它们范围清晰、收益高、风险低，能让后续功能迭代更稳。
