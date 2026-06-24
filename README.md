# Personal Wiki Agent

Personal Wiki Agent 是一个本地优先、可持续学习、可主动协作的个人知识库 Agent 项目。

项目目标不是重做一个笔记 App，而是整合个人电脑上的多个知识目录、本地文档、笔记 App 本地同步目录、云端笔记 App、网页资料和长期对话上下文，让 Agent 帮助完成检索、总结、关联、生成和提醒。

它面向持续学习者和长期知识积累者：资料可能来自 PC 硬盘、Obsidian vault、Notion、有道云笔记、语雀、飞书、网页剪藏、公众号文章和长期对话。系统应能随着用户持续补充资料而增量更新知识库，并逐步沉淀更懂用户的长期记忆。

项目同时考虑换机迁移和长期保存：本地索引、缓存和向量库应可重建；云端笔记、本地备份和导出文件可作为长期知识迁移载体。本地资料写回云端笔记必须由用户显式触发，不默认自动上传。

## 当前路线

项目当前采用轻量 MVP 路线，不直接 fork 大型开源项目。MVP 是长期目标架构上的最小垂直切片，不是临时 demo 架构；后续成熟化应在既有分层内扩展能力，避免推倒重来。

核心参考方向：

- 产品体验参考 [Khoj](https://github.com/khoj-ai/khoj)：个人 second brain + custom agent。
- 架构参考 [Onyx](https://github.com/onyx-dot-app/onyx)：connector、后台同步、hybrid search、权限/数据源模型。
- RAG 细节参考 [Quivr](https://github.com/QuivrHQ/quivr)：parser、chunk、retriever、vectorstore 抽象。
- Agent 长期记忆参考 [Mem0](https://github.com/mem0ai/mem0)，但和文档知识库分开存。

完整技术选型、MVP 范围、阶段路线和防跑偏原则见：

- [docs/technical-direction.md](docs/technical-direction.md)

完整系统设计、模块拆分、技术选型原因、工期排布和验收标准见：

- [docs/project-design.md](docs/project-design.md)

对话式 Agent UI 的信息架构、界面约束、知识 Agent 控件和验收标准见：

- [docs/conversational-agent-ui.md](docs/conversational-agent-ui.md)

云端笔记 API 接入、同步、去重、增量更新和 Agent 边界设计见：

- [docs/cloud-note-connectors.md](docs/cloud-note-connectors.md)

文档知识库与长期记忆的分离、性能、检索和隐私边界设计见：

- [docs/knowledge-memory-separation.md](docs/knowledge-memory-separation.md)

文档解析 adapter、开源解析器选型、解析质量评估和演进触发器见：

- [docs/document-parser-adapters.md](docs/document-parser-adapters.md)

模型 provider、模型注册表、能力识别、密钥配置和任务路由设计见：

- [docs/model-provider-registry.md](docs/model-provider-registry.md)

笔记导入导出、跨平台迁移、标准迁移包、格式边界和 adapter 设计见：

- [docs/note-import-export-strategy.md](docs/note-import-export-strategy.md)

MVP 实施计划、任务拆解、阶段验收门和每周追踪模板见：

- [docs/mvp-implementation-plan.md](docs/mvp-implementation-plan.md)

## 开发约束

开发前先阅读：

- [rules.md](rules.md)

当技术路线、架构原则或 MVP 边界发生变化时，优先更新 `docs/technical-direction.md`，再同步调整 `README.md` 和 `rules.md` 中的引用说明。

## 当前开发入口

当前实现从 MVP Task 1 项目骨架开始推进。后端说明见：

- [backend/README.md](backend/README.md)
