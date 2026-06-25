export interface Citation {
  document_id: number;
  chunk_id: number;
  source_id?: number | null;
  heading_path?: string | null;
  page_number?: number | null;
  snippet?: string | null;
}

export interface RetrievalSummary {
  total_results: number;
  used_results: number;
  source_count: number;
  has_reliable_sources: boolean;
}

export type MemoryType = "user_preference" | "project_context" | "workflow_habit" | "stable_fact";

export interface MemoryUsed {
  memory_id?: number;
  memory_type?: MemoryType | string;
  content: string;
  source?: string | null;
  confidence?: number | null;
  expires_at?: string | null;
}

export interface ChatRequest {
  message: string;
  source_id?: number;
  document_id?: number;
  file_type?: string;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  retrieval_summary: RetrievalSummary;
  model?: string | null;
  memories_used?: MemoryUsed[];
}

export interface SearchRequest {
  query: string;
  source_id?: number;
  document_id?: number;
  file_type?: string;
  top_k?: number;
}

export interface SearchResponse {
  query: string;
  top_k: number;
  results: SearchResult[];
}

export interface SourceSummary {
  source_id: number;
  source_type: string;
  name: string;
  uri: string;
}

export interface DocumentSummary {
  document_id: number;
  title: string;
  uri: string;
  mime_type: string;
  status: string;
  metadata: Record<string, unknown>;
}

export interface SearchResult {
  chunk_id: number;
  document_id: number;
  source_id: number;
  score: number;
  lexical_score: number;
  vector_score: number;
  text: string;
  snippet?: string | null;
  metadata: Record<string, unknown>;
  citation: Citation;
  document: DocumentSummary;
  source: SourceSummary;
}

export interface ChunkSummary {
  chunk_id: number;
  document_id: number;
  chunk_index: number;
  heading_path?: string | null;
  page_number?: number | null;
  token_count: number;
  text: string;
  metadata: Record<string, unknown>;
}

export interface DocumentDetail extends DocumentSummary {
  source_id: number;
  source: SourceSummary;
  chunks: ChunkSummary[];
}

export interface ChunkDetail extends ChunkSummary {
  document: DocumentSummary;
  source: SourceSummary;
}

export interface MemoryResponse {
  items: MemoryUsed[];
}

export interface CreateMemoryRequest {
  memory_type: MemoryType;
  content: string;
  source: string;
  confidence?: number;
  expires_at?: string;
}

export interface PersonalWikiApiClient {
  chat(request: ChatRequest): Promise<ChatResponse>;
  search(request: SearchRequest): Promise<SearchResponse>;
  getDocument(documentId: number): Promise<DocumentDetail>;
  getChunk(chunkId: number): Promise<ChunkDetail>;
  listMemory(params?: { query?: string; memory_type?: MemoryType | string; limit?: number }): Promise<MemoryResponse>;
  createMemory(request: CreateMemoryRequest): Promise<MemoryUsed>;
}

/** 规范化 Chat API 响应，确保可选 memory 字段不会让 UI 读取失败。 */
export function normalizeChatResponse(response: ChatResponse): ChatResponse {
  return {
    ...response,
    citations: response.citations ?? [],
    memories_used: response.memories_used ?? [],
  };
}

/** 创建 Personal Wiki 后端 API 客户端。 */
export function createApiClient(baseUrl = ""): PersonalWikiApiClient {
  const apiBase = baseUrl.replace(/\/$/, "");

  return {
    async chat(request: ChatRequest) {
      const response = await requestJson<ChatResponse>(apiBase, "/chat", {
        method: "POST",
        body: JSON.stringify(cleanPayload(request)),
      });
      return normalizeChatResponse(response);
    },
    async search(request: SearchRequest) {
      return requestJson<SearchResponse>(apiBase, "/search", {
        method: "POST",
        body: JSON.stringify(cleanPayload(request)),
      });
    },
    async getDocument(documentId: number) {
      return requestJson<DocumentDetail>(apiBase, `/documents/${documentId}`);
    },
    async getChunk(chunkId: number) {
      return requestJson<ChunkDetail>(apiBase, `/chunks/${chunkId}`);
    },
    async listMemory(params = {}) {
      const query = buildQuery(params);
      return requestJson<MemoryResponse>(apiBase, `/memory${query}`);
    },
    async createMemory(request: CreateMemoryRequest) {
      return requestJson<MemoryUsed>(apiBase, "/memory", {
        method: "POST",
        body: JSON.stringify(cleanPayload(request)),
      });
    },
  };
}

/** 移除 undefined 字段，避免把空过滤条件传给后端的严格 Pydantic 模型。 */
function cleanPayload<T extends object>(payload: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== undefined && value !== ""),
  ) as Partial<T>;
}

/** 将可选查询参数转换为后端 memory 接口接受的 query string。 */
function buildQuery(params: Record<string, string | number | undefined>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

/** 执行 JSON 请求，并把后端 detail 错误转换为可展示的异常信息。 */
async function requestJson<T>(baseUrl: string, path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return (await response.json()) as T;
}

/** 兼容 FastAPI detail 字符串或对象，生成面向 UI 的错误说明。 */
async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown; message?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (payload.detail && typeof payload.detail === "object" && "message" in payload.detail) {
      return String((payload.detail as { message?: unknown }).message);
    }
    if (typeof payload.message === "string") {
      return payload.message;
    }
  } catch {
    // 响应不是 JSON 时回退到 HTTP 状态，避免吞掉网络错误上下文。
  }
  return `请求失败：${response.status}`;
}
