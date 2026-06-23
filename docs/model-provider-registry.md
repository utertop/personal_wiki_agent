# 模型 Provider 与模型注册表设计

## 1. 文档目的

本文档描述 Personal Wiki Agent 如何管理不同 LLM、embedding、rerank、vision 等模型供应商。

核心原则：

**用户只负责配置 provider、API key、base URL 和偏好；系统负责发现模型、识别能力、选择模型和统一调用。**

上层业务不应直接绑定 OpenAI、Ollama、Claude、Gemini、DeepSeek、Qwen、Mistral 或 vLLM 等具体 SDK。

## 2. 参考思路

### 2.1 opencode

参考：

- [anomalyco/opencode](https://github.com/anomalyco/opencode)
- [OpenCode Providers](https://opencode.ai/docs/providers)
- [OpenCode Models](https://opencode.ai/docs/models)

opencode 的关键思路：

- 通过统一 provider 配置支持大量 LLM provider。
- 用户通过连接流程配置 API key。
- provider 可以配置 `baseURL`。
- 模型通过统一模型列表选择。
- 模型 ID 使用 `provider_id/model_id` 形式。
- 自定义 provider 可以指定兼容协议、endpoint 和模型列表。
- 模型配置与模型调用分离。

本项目可以借鉴这种方式，但不直接依赖 opencode。

### 2.2 Models.dev

参考：

- [Models.dev](https://models.dev/)

Models.dev 是一个开放模型数据库，记录模型、provider、上下文长度、输入输出、工具调用、结构化输出、价格、更新时间等信息。

本项目可以参考它的数据结构，后续可选择：

- 使用本地内置模型 catalog。
- 从 Models.dev 或类似 registry 拉取模型元数据。
- 允许用户手动补充私有模型元数据。

### 2.3 LiteLLM

参考：

- [BerriAI/litellm](https://github.com/BerriAI/litellm)

LiteLLM 是 Python 生态中常见的统一 LLM gateway / SDK，提供 OpenAI 格式调用多家模型供应商的能力。

本项目可以把 LiteLLM 作为可选实现方案之一：

- MVP 可先自建轻量 provider adapter。
- 如果 provider 数量快速增加，再评估接入 LiteLLM SDK 或 LiteLLM proxy。

## 3. 设计目标

模型接入层需要满足：

- 用户配置简单。
- 模型名称不写死在代码里。
- 支持 OpenAI 兼容 API。
- 支持 Ollama / LM Studio / vLLM 等本地模型服务。
- 支持不同任务使用不同模型。
- 支持模型能力发现。
- 支持模型列表缓存。
- 支持私有 provider 和私有模型。
- 支持后续接入 LiteLLM 或其他统一网关。

## 4. 模块划分

建议拆成以下组件：

```text
CredentialStore
ProviderConfig
ModelProvider
ModelRegistry
ModelCatalog
ModelCapabilityResolver
ModelRouter
ModelClient
```

职责：

- `CredentialStore`：保存 API key、token、base URL 等敏感信息。
- `ProviderConfig`：保存 provider 的非敏感配置。
- `ModelProvider`：封装具体 provider 的认证、模型拉取和调用。
- `ModelRegistry`：统一管理 provider 和模型元数据。
- `ModelCatalog`：缓存可用模型列表和能力信息。
- `ModelCapabilityResolver`：判断模型支持 chat、embedding、vision、tool call、structured output、rerank 等能力。
- `ModelRouter`：根据任务选择合适模型。
- `ModelClient`：向上层提供统一调用接口。

## 5. ModelProvider 接口

建议接口：

```text
ModelProvider
  provider_id
  display_name
  protocol
  list_models() -> list[ModelInfo]
  get_model(model_id) -> ModelInfo
  chat(model_id, messages, options) -> ChatResult
  embed(model_id, texts, options) -> EmbeddingResult
  rerank(model_id, query, documents, options) -> RerankResult
  vision(model_id, messages, images, options) -> ChatResult
  validate_credentials() -> CredentialStatus
```

`protocol` 可以是：

```text
openai_compatible
anthropic
google_genai
ollama
azure_openai
bedrock
litellm
custom_http
```

MVP 不需要一次实现所有协议，但接口要预留。

## 6. ModelInfo 模型

建议字段：

```text
provider_id
model_id
display_name
capabilities
context_window
max_output_tokens
input_modalities
output_modalities
supports_tools
supports_structured_output
supports_streaming
supports_json_mode
embedding_dimensions
pricing
local
deprecated
updated_at
metadata
```

能力类型建议：

```text
chat
embedding
rerank
vision
audio
image_generation
tool_call
structured_output
long_context
local
```

## 7. 用户配置方式

用户不应该手动维护复杂模型清单。

MVP 配置示例：

```yaml
models:
  providers:
    openai:
      type: openai_compatible
      base_url: https://api.openai.com/v1
      api_key_env: OPENAI_API_KEY
      enabled: true
    ollama:
      type: ollama
      base_url: http://localhost:11434
      enabled: true

  defaults:
    chat: openai/gpt-5.4
    embedding: openai/text-embedding-3-large
    local_chat: ollama/qwen3
```

配置原则：

- API key 优先放在 `.env`、系统 keychain 或 CredentialStore。
- `sources.yaml` 或模型配置文件只保存非敏感配置。
- 用户可以手动指定默认模型。
- 如果用户不指定模型，系统根据 provider 和任务自动推荐。

## 8. 模型发现流程

模型发现顺序：

1. 读取本地配置中的 provider。
2. 校验 provider 凭证。
3. 调用 provider 的模型列表接口，例如 OpenAI 兼容 `/v1/models` 或 Ollama 模型列表。
4. 合并内置 catalog、远程 catalog 和用户自定义模型。
5. 识别模型能力。
6. 写入本地 ModelCatalog 缓存。
7. 给 UI / CLI 提供可选模型列表。

如果 provider 不支持模型列表接口：

- 使用内置 catalog。
- 允许用户手动声明模型。
- 标记该 provider 为 `manual_models_required`。

## 9. 模型能力识别

能力识别来源：

- provider 返回的模型元数据。
- 内置模型 catalog。
- Models.dev 类模型数据库。
- 用户手动配置。
- 探测请求。

模型能力不能只靠模型名称猜测。

示例：

```yaml
models:
  overrides:
    openai/custom-embedding:
      capabilities: [embedding]
      embedding_dimensions: 3072
    local/qwen:
      capabilities: [chat, tool_call]
      context_window: 32768
```

## 10. ModelRouter 任务路由

不同任务应使用不同模型。

任务类型：

- `chat_answer`：知识库问答。
- `summarize`：文档或目录总结。
- `embedding`：向量生成。
- `rerank`：检索结果重排。
- `vision_parse`：图片理解。
- `memory_extract`：长期记忆抽取。
- `topic_map`：主题地图生成。

路由规则示例：

```text
embedding -> 优先 embedding 能力模型
rerank -> 优先 rerank 能力模型
vision_parse -> 必须支持 vision
local_private -> 优先本地模型
high_quality_answer -> 优先高质量云端模型
low_cost_batch -> 优先低成本模型
```

MVP 可以先通过配置指定默认模型；后续再加入自动路由。

## 11. 本地模型支持

本地模型是隐私优先的重要能力。

优先支持：

- Ollama。
- LM Studio。
- vLLM。
- llama.cpp server。
- 其他 OpenAI-compatible local server。

本地模型处理原则：

- 通过 `base_url` 接入。
- 优先使用 OpenAI-compatible 协议。
- 模型列表可通过本地服务接口发现。
- 如果本地模型不支持 tool call 或 structured output，应在 capability 中标记。

## 12. CredentialStore 和安全

密钥管理必须和普通配置分离。

MVP：

- `.env` 保存 API key。
- 配置文件只保存 `api_key_env`。
- 日志禁止输出 API key。

后续增强：

- Windows Credential Manager。
- macOS Keychain。
- Linux Secret Service。
- 数据库加密字段。
- UI 中支持添加、测试和删除 provider key。

## 13. 缓存与更新

模型列表可能经常变化。

缓存策略：

- 本地缓存 provider model list。
- 记录 `fetched_at`。
- 支持手动刷新。
- 支持启动时后台刷新。
- provider 不可用时使用上次缓存。

缓存字段：

```text
provider_id
model_id
capabilities
context_window
pricing
updated_at
fetched_at
source
```

## 14. MVP 实现范围

MVP 应实现：

1. `ModelProvider` 接口。
2. OpenAI-compatible provider。
3. Ollama provider。
4. `ModelCatalog` 本地缓存。
5. 默认 chat model 和 embedding model 配置。
6. 简单 `ModelRouter`，按任务读取配置。
7. `.env` + `api_key_env` 的密钥读取方式。
8. UI / CLI 中显示当前可用 provider 和模型。

MVP 不做：

- 自动接入几十家 provider。
- 复杂模型 benchmark。
- 成本优化路由。
- 多 provider fallback。
- 统一计费。
- 团队级 key 管理。

## 15. 后续演进

Phase 2：

- 增加 Anthropic、Google、DeepSeek、OpenRouter 等 provider adapter。
- 支持模型能力覆盖配置。
- 支持手动刷新模型列表。
- 支持不同 Agent 工具选择不同模型。

Phase 3：

- 评估 LiteLLM SDK 或 LiteLLM proxy。
- 支持多 provider fallback。
- 支持成本、速度、质量路由。
- 支持模型调用统计。
- 支持 provider 健康检查。

Phase 4：

- 支持 Models.dev 或类似模型 registry 同步。
- 支持自动推荐模型。
- 支持模型评测集。
- 支持本地模型和云端模型混合策略。

## 16. 验收标准

第一版模型接入完成时应满足：

1. 用户可以只配置 provider、API key 和 base URL。
2. 系统可以列出可用模型或读取用户手动配置模型。
3. chat 和 embedding 调用都通过统一 `ModelProvider` 接口。
4. 业务层不直接依赖具体 provider SDK。
5. 模型名称不写死在代码中。
6. 不同任务可以选择不同默认模型。
7. API key 不出现在日志和普通文档中。
8. 后续新增 provider 不需要改动 RAG、Agent、UI 主流程。

## 17. 关键结论

模型层应采用：

```text
Provider 配置简单
ModelProvider 统一调用
ModelRegistry 管理模型
ModelCatalog 缓存能力
ModelRouter 按任务选择
CredentialStore 保护密钥
```

这样用户只需要管理 provider key 和 endpoint，系统负责模型发现、能力识别和调用路由。

