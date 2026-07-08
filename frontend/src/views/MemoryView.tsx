import { FormEvent, useEffect, useState } from "react";
import { Plus, RefreshCw, Search } from "lucide-react";
import type { CreateMemoryRequest, MemoryType, MemoryUsed, PersonalWikiApiClient } from "../api/client";

export interface MemoryViewProps {
  client: PersonalWikiApiClient;
}

interface MemoryFilterState {
  query: string;
  memoryType: "" | MemoryType;
  limit: string;
}

interface MemoryFormState {
  memoryType: MemoryType;
  content: string;
  source: string;
  confidence: string;
  expiresAt: string;
}

const memoryTypes: MemoryType[] = ["user_preference", "project_context", "workflow_habit", "stable_fact"];

const defaultFilters: MemoryFilterState = {
  query: "",
  memoryType: "",
  limit: "10",
};

const defaultForm: MemoryFormState = {
  memoryType: "user_preference",
  content: "",
  source: "manual",
  confidence: "",
  expiresAt: "",
};

/** 管理长期记忆，只调用 Memory API，不把记忆展示为文档引用来源。 */
export function MemoryView({ client }: MemoryViewProps) {
  const [memories, setMemories] = useState<MemoryUsed[]>([]);
  const [filters, setFilters] = useState<MemoryFilterState>(defaultFilters);
  const [form, setForm] = useState<MemoryFormState>(defaultForm);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadMemories(defaultFilters);
  }, [client]);

  async function loadMemories(nextFilters = filters) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await client.listMemory({
        query: nextFilters.query.trim() || undefined,
        memory_type: nextFilters.memoryType || undefined,
        limit: toPositiveLimit(nextFilters.limit),
      });
      setMemories(response.items);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "记忆加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadMemories(filters);
  }

  async function handleCreateMemory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.content.trim() || !form.source.trim() || isSaving) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await client.createMemory(buildCreateRequest(form));
      setForm(defaultForm);
      setFilters(defaultFilters);
      await loadMemories(defaultFilters);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "记忆创建失败");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="management-view" aria-label="长期记忆">
      <header className="management-header">
        <div>
          <p className="eyebrow">Memory</p>
          <h1>长期记忆</h1>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadMemories()} disabled={isLoading}>
          <RefreshCw size={16} aria-hidden="true" />
          <span>刷新</span>
        </button>
      </header>

      <form className="inline-form memory-filter-form" onSubmit={handleSearch}>
        <label>
          关键词
          <input
            value={filters.query}
            onChange={(event) => setFilters((current) => ({ ...current, query: event.target.value }))}
          />
        </label>
        <label>
          筛选类型
          <select
            value={filters.memoryType}
            onChange={(event) =>
              setFilters((current) => ({ ...current, memoryType: event.target.value as "" | MemoryType }))
            }
          >
            <option value="">全部</option>
            {memoryTypes.map((memoryType) => (
              <option key={memoryType} value={memoryType}>
                {memoryType}
              </option>
            ))}
          </select>
        </label>
        <label>
          条数
          <input
            min="1"
            type="number"
            value={filters.limit}
            onChange={(event) => setFilters((current) => ({ ...current, limit: event.target.value }))}
          />
        </label>
        <button className="secondary-button" type="submit" disabled={isLoading}>
          <Search size={16} aria-hidden="true" />
          <span>查询</span>
        </button>
      </form>

      <form className="inline-form memory-create-form" onSubmit={handleCreateMemory}>
        <label>
          记忆类型
          <select
            value={form.memoryType}
            onChange={(event) => setForm((current) => ({ ...current, memoryType: event.target.value as MemoryType }))}
          >
            {memoryTypes.map((memoryType) => (
              <option key={memoryType} value={memoryType}>
                {memoryType}
              </option>
            ))}
          </select>
        </label>
        <label className="wide-field">
          内容
          <textarea
            rows={2}
            value={form.content}
            onChange={(event) => setForm((current) => ({ ...current, content: event.target.value }))}
          />
        </label>
        <label>
          来源
          <input
            value={form.source}
            onChange={(event) => setForm((current) => ({ ...current, source: event.target.value }))}
          />
        </label>
        <label>
          置信度
          <input
            max="1"
            min="0"
            step="0.01"
            type="number"
            value={form.confidence}
            onChange={(event) => setForm((current) => ({ ...current, confidence: event.target.value }))}
          />
        </label>
        <label>
          过期时间
          <input
            type="datetime-local"
            value={form.expiresAt}
            onChange={(event) => setForm((current) => ({ ...current, expiresAt: event.target.value }))}
          />
        </label>
        <button className="secondary-button" type="submit" disabled={isSaving}>
          <Plus size={16} aria-hidden="true" />
          <span>添加记忆</span>
        </button>
      </form>

      {error ? <div className="activity-error">{error}</div> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>类型</th>
              <th>内容</th>
              <th>来源</th>
              <th>置信度</th>
              <th>过期时间</th>
            </tr>
          </thead>
          <tbody>
            {memories.length === 0 && !isLoading ? (
              <tr>
                <td colSpan={6}>暂无长期记忆</td>
              </tr>
            ) : null}
            {isLoading ? (
              <tr>
                <td colSpan={6}>加载中</td>
              </tr>
            ) : null}
            {memories.map((memory) => (
              <tr key={memory.memory_id ?? `${memory.memory_type}-${memory.content}`}>
                <td>{memory.memory_id ?? ""}</td>
                <td>
                  <span className="table-status">{memory.memory_type ?? "memory"}</span>
                </td>
                <td className="long-cell">{memory.content}</td>
                <td>{memory.source ?? ""}</td>
                <td>{formatConfidence(memory.confidence)}</td>
                <td>{formatExpiresAt(memory.expires_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function buildCreateRequest(form: MemoryFormState): CreateMemoryRequest {
  const request: CreateMemoryRequest = {
    memory_type: form.memoryType,
    content: form.content.trim(),
    source: form.source.trim(),
  };
  const confidence = Number(form.confidence);
  if (form.confidence !== "" && Number.isFinite(confidence)) {
    request.confidence = confidence;
  }
  if (form.expiresAt) {
    request.expires_at = form.expiresAt;
  }
  return request;
}

function toPositiveLimit(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 10;
}

function formatConfidence(value: number | null | undefined): string {
  return typeof value === "number" ? value.toFixed(2) : "";
}

function formatExpiresAt(value: string | null | undefined): string {
  return value ? value.replace("T", " ").slice(0, 16) : "永久";
}
