# 文档知识库与长期记忆分离设计

## 1. 文档目的

本文档描述 Personal Wiki Agent 如何实现文档知识库与长期记忆的分离，以及这种分离在性能、检索、更新、删除、引用和隐私上的处理方式。

核心原则：

**文档知识库负责“我有哪些资料”，长期记忆负责“Agent 对用户和任务的稳定理解”。**

两者必须分开存储、分开索引、分开检索、合并使用。

## 2. 为什么要分离

文档知识库和长期记忆的数据性质不同。

文档知识库：

- 存储事实资料。
- 数据量大。
- 内容长。
- 来源明确。
- 需要分块。
- 需要关键词检索、向量检索和元数据过滤。
- 回答时必须能引用文件、页面、URL 或笔记来源。

长期记忆：

- 存储 Agent 对用户的稳定理解。
- 数据量小。
- 内容短。
- 需要置信度。
- 需要过期和冲突处理。
- 来源可能来自对话、用户确认或项目上下文。
- 回答时应标记为记忆，而不是伪装成文档证据。

如果混在一个向量库里，会导致：

- 事实问题被用户偏好污染。
- 用户偏好被当作文档来源引用。
- 删除文档时误删记忆。
- 修改记忆时影响文档索引。
- 大量文档 chunk 淹没少量高价值记忆。
- 检索排序和性能难以调优。

## 3. 存储设计

### 3.1 文档知识库存储

文档知识库用于存储来自本地目录、笔记 App 本地同步目录、云端笔记和网页资料的事实内容。

建议存储：

```text
documents 表
chunks 表
sources 表
index_jobs 表
SQLite FTS5 关键词索引
向量库 collection: document_chunks
```

核心字段：

```text
document_id
source_id
source_type
uri
title
content_hash
metadata_json
status
created_at
updated_at
indexed_at
```

chunk 字段：

```text
chunk_id
document_id
chunk_index
text
heading_path
page_number
token_count
metadata_json
created_at
updated_at
```

### 3.2 长期记忆存储

长期记忆用于存储用户偏好、项目上下文、工作习惯和稳定事实。

建议存储：

```text
memories 表
可选向量库 collection: memories
```

核心字段：

```text
memory_id
memory_type
content
source
confidence
status
created_at
updated_at
expires_at
```

可选扩展字段：

```text
user_id
project_id
scope
evidence_uri
last_used_at
usage_count
supersedes_memory_id
```

## 4. 索引设计

### 4.1 文档索引

文档知识库使用混合索引。

索引方式：

- SQLite 元数据索引。
- SQLite FTS5 关键词索引。
- 向量索引 `document_chunks`。

适用场景：

- 查找某个术语、人名、文件名、标题。
- 查找语义相关资料。
- 按目录、来源、时间、文件类型过滤。
- 回答需要引用来源的问题。

### 4.2 记忆索引

长期记忆使用轻量索引。

索引方式：

- SQLite 普通索引：`memory_type`、`status`、`confidence`、`updated_at`。
- 可选向量索引 `memories`。

适用场景：

- 查找用户偏好。
- 查找项目背景。
- 查找长期目标。
- 查找对话中沉淀的稳定事实。

MVP 阶段可以先不对记忆建向量索引，只使用类型过滤和关键词匹配。等记忆数量增长后，再加入 memory vector index。

## 5. 检索通道

### 5.1 文档检索通道

文档检索流程：

```text
用户问题
-> 查询理解
-> 元数据过滤
-> 关键词召回
-> 向量召回
-> 结果合并
-> 排序或 rerank
-> 返回带来源的 chunks
```

默认参数建议：

```text
keyword_top_k = 20
vector_top_k = 20
final_top_k = 8
```

后续引入 reranker 后，可以扩大召回数量，再用 reranker 精排。

### 5.2 记忆检索通道

记忆检索流程：

```text
用户问题
-> 判断是否需要个性化上下文
-> 按 memory_type / confidence / status 过滤
-> 关键词或向量召回
-> 按置信度、更新时间、使用频率排序
-> 返回少量高价值记忆
```

默认参数建议：

```text
memory_top_k = 3 到 8
min_confidence = 0.6
status = active
```

记忆召回应保持克制，避免把过多用户偏好塞进上下文，干扰事实回答。

## 6. 查询路由

不同问题应走不同检索组合。

### 6.1 主要查文档知识库

示例：

- “我之前关于 RAG 的资料里有没有提过 hybrid search？”
- “帮我总结这个目录下的 PDF。”
- “这篇 Notion 笔记里讲了什么？”

策略：

- 文档检索为主。
- 记忆只作为轻量偏好上下文。

### 6.2 主要查长期记忆

示例：

- “按照我的偏好，下一步应该怎么做？”
- “我这个项目的长期目标是什么？”
- “我之前说过我喜欢什么样的技术方案？”

策略：

- 记忆检索为主。
- 必要时查项目文档补证据。

### 6.3 同时查两者

示例：

- “结合我的项目路线，解释一下云端笔记 connector 怎么实现。”
- “按照我本地优先的偏好，优化这个 Agent 设计。”

策略：

- 文档检索提供事实依据。
- 记忆检索提供用户偏好和项目上下文。
- 回答时分清“资料来源”和“长期记忆”。

## 7. 上下文合成

回答前应把上下文分区，而不是把文档和记忆混成一段。

建议结构：

```text
[Document Evidence]
1. source: docs/technical-direction.md
   chunk: ...
2. source: docs/project-design.md
   chunk: ...

[Long-term Memory]
1. type: user_preference
   content: 用户偏好中文文档和本地优先方案
   confidence: 0.9
2. type: project_context
   content: 当前项目是 Personal Wiki Agent
   confidence: 0.95
```

生成回答时：

- 文档证据用于事实结论。
- 长期记忆用于语气、偏好、上下文和个性化建议。
- 如果文档证据不足，应说明没有找到直接来源。
- 如果使用长期记忆，应明确这是记忆或偏好，不当作资料引用。

## 8. 性能策略

### 8.1 数据规模分离

文档库通常很大，可能有成千上万 chunk。

记忆库通常较小，应该控制为高价值、低噪声的条目。

分离后可以分别优化：

- 文档库优化召回和 rerank。
- 记忆库优化精确、稳定和置信度。

### 8.2 索引写入分离

文档索引更新频率取决于文件和云端笔记变化。

记忆更新频率取决于用户确认、对话总结和 Agent 主动沉淀。

两者分开后：

- 重建某个目录索引不会影响长期记忆。
- 清理过期记忆不会影响文档检索。
- 文档批量导入不会拖慢记忆读取。

### 8.3 查询参数分离

文档检索：

```text
召回数量较大
需要 hybrid search
需要来源引用
需要 chunk 级别定位
```

记忆检索：

```text
召回数量较小
优先高置信度和近期使用
可按 memory_type 过滤
不需要大规模 rerank
```

### 8.4 缓存策略

可缓存内容：

- 最近查询的文档检索结果。
- 常用主题的 top chunks。
- 当前会话的相关长期记忆。
- 用户当前项目的 project_context。

不应缓存：

- 已删除或已禁用 source 的内容。
- 低置信度或过期记忆。
- token、API key 等敏感信息。

## 9. 更新策略

### 9.1 文档知识库更新

触发来源：

- 本地文件新增、修改、删除。
- 笔记 App 本地同步目录变化。
- 云端 connector 增量同步。

处理方式：

- 按 source 增量扫描。
- 按 document 判断变化。
- 重新解析变化文档。
- 删除旧 chunk。
- 写入新 chunk。
- 更新 FTS 和向量索引。

### 9.2 长期记忆更新

触发来源：

- 用户明确要求记住。
- 用户确认某个偏好。
- 项目长期目标发生变化。
- 对话总结中提取到稳定事实。

处理方式：

- 新增记忆前检查是否已有相似记忆。
- 相似记忆应更新或合并，而不是重复插入。
- 冲突记忆应标记 superseded 或 inactive。
- 低置信度记忆需要用户确认。

MVP 阶段可以只支持手动记忆和简单更新，后续再做自动抽取和冲突合并。

## 10. 删除与隐私

文档删除：

- 删除文档 source 时，应删除相关 document、chunk、FTS 和向量索引。
- 删除本地文件时，应标记 document deleted 或移除索引。
- 删除文档不应自动删除用户长期偏好。

记忆删除：

- 用户可以单独禁用或删除某条记忆。
- 删除记忆不应影响文档索引。
- 过期记忆应被过滤，不进入回答上下文。

隐私边界：

- 文档证据和长期记忆都默认存储在本地。
- 长期记忆可能更敏感，应支持查看、编辑、禁用和删除。
- 回答中使用长期记忆时，应避免暴露不必要的敏感细节。

## 11. API 边界

建议 API 分离：

```text
POST /search
POST /chat
GET /documents/{document_id}
GET /chunks/{chunk_id}
GET /memory
POST /memory
PATCH /memory/{memory_id}
DELETE /memory/{memory_id}
```

`/search` 默认只搜索文档知识库。

`/memory` 只管理长期记忆。

`/chat` 可以根据查询意图同时使用文档和记忆，但返回结构中必须区分：

```text
citations: 文档来源
memories_used: 使用到的长期记忆
retrieval_summary: 检索摘要
```

## 12. MVP 实现建议

MVP 阶段建议实现：

1. 文档表、chunk 表、memory 表分开。
2. 文档使用 FTS5 + 可替换向量库接口。
3. 记忆先使用 SQLite 表和简单关键词检索。
4. chat API 中预留 `memories_used` 字段。
5. 回答模板明确区分文档来源和长期记忆。
6. 支持手动新增、查看、禁用、删除记忆。
7. 不做自动记忆抽取，除非用户明确确认。

## 13. 验收标准

完成第一版分离设计时应满足：

1. 文档和记忆存储在不同表中。
2. 文档 chunk 和记忆不混用同一个向量 collection。
3. 文档检索可以返回来源引用。
4. 记忆检索可以返回 memory_type、confidence 和 updated_at。
5. chat API 返回中可以区分 `citations` 和 `memories_used`。
6. 删除文档不会删除长期记忆。
7. 删除记忆不会影响文档索引。
8. 无文档证据时，系统不会把长期记忆伪装成资料来源。

## 14. 关键结论

文档知识库和长期记忆不是两个彼此隔离的孤岛，而是两个不同职责的上下文来源。

正确方式是：

```text
分开存储
分开索引
分开检索
合并使用
明确标注来源
```

这样既能保证性能，也能保证回答可信、可追溯、可删除、可进化。

