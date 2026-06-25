# Project Rules

本文件用于约束后续开发，避免项目在迭代中偏离当前技术路线。

完整技术路线以 [docs/technical-direction.md](docs/technical-direction.md) 为准。本文件只保留执行层面的规则。

## 核心规则

1. 不直接 fork Khoj、Onyx、Quivr、Mem0 等大型项目，先实现自己的轻量 MVP。
2. 产品体验主线参考 Khoj：个人 second brain + custom agent。
3. 架构吸收 Onyx：connector、后台同步、hybrid search、权限/数据源模型。
4. RAG 模块参考 Quivr：parser、chunk、retriever、vectorstore 抽象。
5. 长期记忆参考 Mem0，但必须和文档知识库存储分离。
6. 默认本地优先，用户明确配置后才接入云端服务。
7. 知识库问答必须尽量带来源引用，没有来源时要明确说明。
8. 不只做向量搜索，必须保留关键词检索和元数据过滤的架构位置。
9. MVP 阶段不引入企业级多用户、复杂权限、移动端和大规模部署能力。
10. 新增技术依赖前，应检查是否符合 `docs/technical-direction.md` 中的阶段路线和防跑偏原则。
11. 前端主体验应保持对话式 Agent 工作台形态；数据源、索引、模型、隐私、云端连接和记忆管理等配置应收纳到侧栏、设置页或抽屉中，不能把首页做成复杂后台系统或配置中心。
12. 后续所有 `*.md` 文档的新增和修改默认使用中文；代码标识、项目名、协议名、库名、API 名称等特定名词可以保留英文。
13. 新增或修改 Markdown 文档时必须使用 UTF-8 编码，并在 Windows / PowerShell 环境下注意读取和输出编码，避免中文显示乱码。
14. 修改任意文档时，必须检查是否会影响其他连锁文档；如果会影响，应一并修改，避免 README、路线文档、设计文档、规则文档之间出现口径不一致。
15. 新增或优化代码时，公共 `class`、`method`、`function` 必须补充中文注释或 docstring，说明职责、输入输出或关键边界；代码标识和库名可以保留英文。
16. 测试代码也属于代码约束范围；新增或修改测试文件时，测试函数、测试辅助函数、测试替身类和测试替身方法也必须补充中文 docstring，说明验证目标或替身职责。
17. 代码注释应解释“这段代码用于什么、为什么这样分层、调用方应该注意什么”，避免只重复函数名或变量名的空泛注释。
18. 新增或修改包含中文注释的代码文件时，必须使用 UTF-8 编码，并在 Windows / PowerShell 环境下注意读取和输出编码，避免中文显示乱码。

## 分支与提交规则

项目当前阶段默认以 `main` 作为本地开发主线。开始新任务前，必须先确认：

1. 当前工作区是否干净。
2. 本地 `main` 是否已同步到 `origin/main` 最新状态。
3. 是否存在未提交的 WIP 改动。

默认情况下，范围明确、风险可控的代码和文档改动应在 `main` 上继续开发，并在用户明确同意后提交到 `main`。

以下情况应使用独立分支，例如 `feat/*`、`fix/*` 或 `wip/*`：

- 大范围架构调整。
- 实验性方案。
- 可能破坏已有功能的改动。
- 需要单独 PR 审查的改动。
- 当前工作区已有未完成改动，且不适合混入主线。
- 用户明确要求使用独立分支。

切换分支前，必须先处理未提交改动：完成提交、暂存 stash，或经用户确认后丢弃。除非用户明确要求，不主动提交、push 或合并分支。

## 变更规则

如果后续需要改变技术选型或项目路线：

1. 先更新 [docs/technical-direction.md](docs/technical-direction.md) 的决策记录。
2. 再更新本文件中受影响的规则。
3. 最后更新 [README.md](README.md) 的项目入口说明。

如果修改的是需求、范围、架构、工期、验收标准或开发约束，必须同步检查所有相关文档，避免新增文档被遗漏。

## 文档一致性体检

当出现以下情况时，必须做一次文档一致性体检：

- 修改 [docs/project-design.md](docs/project-design.md) 的章节结构、模块设计、技术选型、工期、验收标准或风险应对。
- 修改 [docs/technical-direction.md](docs/technical-direction.md) 的路线、决策记录、阶段规划或防跑偏原则。
- 新增、删除或重命名专项文档。
- 调整核心优先级，例如云端 connector 顺序、前端体验方向、模型 provider、parser、检索方案或长期记忆边界。

体检时至少检查：

- README、路线文档、完整设计文档、专项文档和本规则文件之间是否口径一致。
- 是否存在旧工具名、旧模块名、旧平台优先级、旧工期描述或旧验收标准残留。
- 推荐项目结构是否包含当前已存在或已决定预留的核心模块和文档。
- 相关 Markdown 链接是否仍能解析到目标文件。
- 所有 Markdown 是否能按 UTF-8 读取，是否存在中文乱码或替换字符。

当前重点检查清单：

- [README.md](README.md)
- [docs/technical-direction.md](docs/technical-direction.md)
- [docs/project-design.md](docs/project-design.md)
- [docs/cloud-note-connectors.md](docs/cloud-note-connectors.md)
- [docs/knowledge-memory-separation.md](docs/knowledge-memory-separation.md)
- [docs/document-parser-adapters.md](docs/document-parser-adapters.md)
- [docs/model-provider-registry.md](docs/model-provider-registry.md)
- [docs/conversational-agent-ui.md](docs/conversational-agent-ui.md)
- [docs/note-import-export-strategy.md](docs/note-import-export-strategy.md)
- [docs/mvp-implementation-plan.md](docs/mvp-implementation-plan.md)
- [rules.md](rules.md)

如果后续新增需求文档、架构文档、API 文档、开发计划、验收标准或运维部署文档，也应自动纳入连锁检查范围，不需要等本文件先列出。
