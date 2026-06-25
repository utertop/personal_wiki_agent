import { useMemo, useState } from "react";
import { BookOpenText, Database, MessageSquareText, Settings2, TimerReset } from "lucide-react";
import { createApiClient, type Citation } from "./api/client";
import { SourceDrawer } from "./components/SourceDrawer";
import { ChatView } from "./views/ChatView";
import { IndexJobsView } from "./views/IndexJobsView";
import { SourcesView } from "./views/SourcesView";

type ActiveView = "chat" | "sources" | "indexJobs";

/** 控制整个前端工作台的导航、API 客户端和来源抽屉状态。 */
export default function App() {
  const [activeView, setActiveView] = useState<ActiveView>("chat");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  const client = useMemo(() => createApiClient(apiBaseUrl), [apiBaseUrl]);

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="主导航">
        <div className="brand-block">
          <BookOpenText size={22} aria-hidden="true" />
          <div>
            <strong>Wiki Agent</strong>
            <span>个人知识库</span>
          </div>
        </div>
        <nav className="nav-list">
          <button
            className={activeView === "chat" ? "active" : ""}
            type="button"
            onClick={() => setActiveView("chat")}
          >
            <MessageSquareText size={18} aria-hidden="true" />
            <span>Chat</span>
          </button>
          <button
            className={activeView === "sources" ? "active" : ""}
            type="button"
            onClick={() => setActiveView("sources")}
          >
            <Database size={18} aria-hidden="true" />
            <span>数据源</span>
          </button>
          <button
            className={activeView === "indexJobs" ? "active" : ""}
            type="button"
            onClick={() => setActiveView("indexJobs")}
          >
            <TimerReset size={18} aria-hidden="true" />
            <span>索引</span>
          </button>
        </nav>
        <details className="side-settings">
          <summary>
            <Settings2 size={17} aria-hidden="true" />
            <span>设置</span>
          </summary>
          <dl>
            <div>
              <dt>API</dt>
              <dd>{apiBaseUrl || "同源"}</dd>
            </div>
            <div>
              <dt>Memory</dt>
              <dd>可选</dd>
            </div>
          </dl>
        </details>
      </aside>
      <main className="workspace">
        {activeView === "chat" ? <ChatView client={client} onOpenSource={setSelectedCitation} /> : null}
        {activeView === "sources" ? <SourcesView /> : null}
        {activeView === "indexJobs" ? <IndexJobsView /> : null}
      </main>
      <SourceDrawer
        citation={selectedCitation}
        client={client}
        open={selectedCitation !== null}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
