const indexJobRows = [
  { name: "解析文档", scope: "documents", status: "等待后端列表", updatedAt: "未运行" },
  { name: "写入全文索引", scope: "sqlite_fts", status: "只读占位", updatedAt: "未运行" },
  { name: "刷新向量索引", scope: "vector_store", status: "未启用", updatedAt: "未运行" },
];

/** 展示索引任务只读列表，避免把首页变成后台任务中心。 */
export function IndexJobsView() {
  return (
    <section className="management-view" aria-label="索引任务">
      <header className="management-header">
        <div>
          <p className="eyebrow">Index</p>
          <h1>索引任务</h1>
        </div>
        <span className="readonly-badge">只读</span>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>任务</th>
              <th>范围</th>
              <th>状态</th>
              <th>更新时间</th>
            </tr>
          </thead>
          <tbody>
            {indexJobRows.map((row) => (
              <tr key={row.name}>
                <td>{row.name}</td>
                <td>{row.scope}</td>
                <td>
                  <span className="table-status">{row.status}</span>
                </td>
                <td>{row.updatedAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
