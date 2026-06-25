import type { ChatResponse } from "../api/client";

export type ToolActivityKind = "retrieval" | "citation" | "model" | "memory";

export interface ToolActivityItem {
  kind: ToolActivityKind;
  title: string;
  detail: string;
}

export interface ToolActivityProps {
  response?: ChatResponse | null;
  isLoading?: boolean;
  error?: string | null;
}

/** 从 Chat 响应整理右侧工具活动流。 */
export function buildToolActivities(response?: ChatResponse | null): ToolActivityItem[] {
  if (!response) {
    return [];
  }

  const summary = response.retrieval_summary;
  const activities: ToolActivityItem[] = [
    {
      kind: "retrieval",
      title: summary.has_reliable_sources ? "检索完成" : "检索不足",
      detail: summary.has_reliable_sources
        ? `命中 ${summary.total_results} 条，使用 ${summary.used_results} 条，覆盖 ${summary.source_count} 个来源`
        : `未找到可靠来源，命中 ${summary.total_results} 条候选结果`,
    },
  ];

  if (response.citations.length > 0) {
    activities.push({
      kind: "citation",
      title: "引用就绪",
      detail: `生成 ${response.citations.length} 条可追溯引用`,
    });
  }

  if (response.model) {
    activities.push({
      kind: "model",
      title: "模型",
      detail: `使用 ${response.model}，置信度 ${Math.round(response.confidence * 100)}%`,
    });
  }

  const memories = response.memories_used ?? [];
  if (memories.length > 0) {
    activities.push({
      kind: "memory",
      title: "Memory",
      detail: `使用 ${memories.length} 条记忆：${memories
        .map((memory) => memory.memory_type ?? "general")
        .join("、")}`,
    });
  }

  return activities;
}

/** 展示检索、引用、模型和 memory 使用情况。 */
export function ToolActivity({ response, isLoading = false, error = null }: ToolActivityProps) {
  const activities = buildToolActivities(response);

  return (
    <aside className="tool-activity" aria-label="工具活动">
      <div className="panel-heading">
        <span>活动</span>
        {isLoading ? <span className="status-dot">运行中</span> : <span className="status-muted">待命</span>}
      </div>
      {error ? <div className="activity-error">{error}</div> : null}
      {activities.length === 0 && !isLoading ? (
        <p className="empty-state">等待下一次检索</p>
      ) : (
        <ol className="activity-list">
          {isLoading ? (
            <li className="activity-item">
              <span className="activity-kind">检索</span>
              <div>
                <strong>正在查询知识库</strong>
                <p>整理候选片段和上下文</p>
              </div>
            </li>
          ) : null}
          {activities.map((activity) => (
            <li className="activity-item" key={`${activity.kind}-${activity.title}`}>
              <span className="activity-kind">{activity.kind}</span>
              <div>
                <strong>{activity.title}</strong>
                <p>{activity.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </aside>
  );
}
