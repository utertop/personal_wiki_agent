const sourceRows = [
  { name: "本地笔记目录", type: "local_directory", uri: "config/sources.yaml", status: "只读占位" },
  { name: "Obsidian Vault", type: "obsidian_vault", uri: "本地路径", status: "等待配置" },
  { name: "云笔记连接", type: "cloud_notes", uri: "后续接入", status: "未启用" },
];

/** 展示数据源只读列表，保持管理能力在侧栏视图内。 */
export function SourcesView() {
  return (
    <section className="management-view" aria-label="数据源">
      <header className="management-header">
        <div>
          <p className="eyebrow">Sources</p>
          <h1>数据源</h1>
        </div>
        <span className="readonly-badge">只读</span>
      </header>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>URI</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {sourceRows.map((row) => (
              <tr key={row.name}>
                <td>{row.name}</td>
                <td>{row.type}</td>
                <td>{row.uri}</td>
                <td>
                  <span className="table-status">{row.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
