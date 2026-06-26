import { useEffect, useState } from "react";
import { Play, RefreshCw } from "lucide-react";
import type { IndexJobRecord, PersonalWikiApiClient } from "../api/client";

export interface IndexJobsViewProps {
  client: PersonalWikiApiClient;
}

/** 展示真实索引任务列表，并提供手动触发索引入口。 */
export function IndexJobsView({ client }: IndexJobsViewProps) {
  const [jobs, setJobs] = useState<IndexJobRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadJobs();
  }, [client]);

  /** 从后端加载最近索引任务。 */
  async function loadJobs() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await client.listIndexJobs();
      setJobs(response.items);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "索引任务加载失败");
    } finally {
      setIsLoading(false);
    }
  }

  /** 触发全部启用数据源索引，并刷新任务列表。 */
  async function handleRunIndex() {
    if (isRunning) {
      return;
    }

    setIsRunning(true);
    setError(null);
    try {
      await client.runIndex({});
      await loadJobs();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "索引任务触发失败");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <section className="management-view" aria-label="索引任务">
      <header className="management-header">
        <div>
          <p className="eyebrow">Index</p>
          <h1>索引任务</h1>
        </div>
        <div className="header-actions">
          <button className="secondary-button" type="button" onClick={() => void loadJobs()} disabled={isLoading}>
            <RefreshCw size={16} aria-hidden="true" />
            <span>刷新</span>
          </button>
          <button className="secondary-button" type="button" onClick={() => void handleRunIndex()} disabled={isRunning}>
            <Play size={16} aria-hidden="true" />
            <span>运行索引</span>
          </button>
        </div>
      </header>
      {error ? <div className="activity-error">{error}</div> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>数据源</th>
              <th>状态</th>
              <th>进度</th>
              <th>错误</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 && !isLoading ? (
              <tr>
                <td colSpan={5}>暂无索引任务</td>
              </tr>
            ) : null}
            {isLoading ? (
              <tr>
                <td colSpan={5}>加载中</td>
              </tr>
            ) : null}
            {jobs.map((row) => (
              <tr key={row.job_id}>
                <td>{row.job_id}</td>
                <td>{row.source_name ?? row.source_id}</td>
                <td>
                  <span className="table-status">{row.status}</span>
                </td>
                <td>{row.processed_items} / {row.total_items}</td>
                <td>{row.error_message ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
