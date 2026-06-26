import { FormEvent, useEffect, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import type { PersonalWikiApiClient, SourceRecord, SourceType } from "../api/client";

export interface SourcesViewProps {
  client: PersonalWikiApiClient;
}

interface SourceFormState {
  sourceType: SourceType;
  name: string;
  uri: string;
}

/** 展示真实数据源列表，并提供 MVP 阶段的本地数据源创建入口。 */
export function SourcesView({ client }: SourcesViewProps) {
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [form, setForm] = useState<SourceFormState>({
    sourceType: "local_directory",
    name: "",
    uri: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadSources();
  }, [client]);

  /** 从后端加载当前全部数据源。 */
  async function loadSources() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await client.listSources();
      setSources(response.items);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "数据源加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  /** 创建本地优先数据源，并刷新列表。 */
  async function handleCreateSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.name.trim() || !form.uri.trim() || isSaving) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await client.createSource({
        source_type: form.sourceType,
        name: form.name.trim(),
        uri: form.uri.trim(),
      });
      setForm((current) => ({ ...current, name: "", uri: "" }));
      await loadSources();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "数据源创建失败");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="management-view" aria-label="数据源">
      <header className="management-header">
        <div>
          <p className="eyebrow">Sources</p>
          <h1>数据源</h1>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadSources()} disabled={isLoading}>
          <RefreshCw size={16} aria-hidden="true" />
          <span>刷新</span>
        </button>
      </header>

      <form className="inline-form" onSubmit={handleCreateSource}>
        <label>
          名称
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
          />
        </label>
        <label>
          URI
          <input
            value={form.uri}
            onChange={(event) => setForm((current) => ({ ...current, uri: event.target.value }))}
          />
        </label>
        <label>
          类型
          <select
            value={form.sourceType}
            onChange={(event) =>
              setForm((current) => ({ ...current, sourceType: event.target.value as SourceType }))
            }
          >
            <option value="local_directory">local_directory</option>
            <option value="local_synced_notes">local_synced_notes</option>
            <option value="obsidian_vault">obsidian_vault</option>
          </select>
        </label>
        <button className="secondary-button" type="submit" disabled={isSaving}>
          <Plus size={16} aria-hidden="true" />
          <span>添加数据源</span>
        </button>
      </form>

      {error ? <div className="activity-error">{error}</div> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>类型</th>
              <th>URI</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {sources.length === 0 && !isLoading ? (
              <tr>
                <td colSpan={5}>暂无数据源</td>
              </tr>
            ) : null}
            {isLoading ? (
              <tr>
                <td colSpan={5}>加载中</td>
              </tr>
            ) : null}
            {sources.map((row) => (
              <tr key={row.source_id}>
                <td>{row.source_id}</td>
                <td>{row.name}</td>
                <td>{row.source_type}</td>
                <td>{row.uri}</td>
                <td>
                  <span className="table-status">{row.enabled ? "启用" : "停用"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
