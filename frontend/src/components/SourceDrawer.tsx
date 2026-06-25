import { useEffect, useState } from "react";
import { FileText, Loader2, X } from "lucide-react";
import type { ChunkDetail, Citation, DocumentDetail, PersonalWikiApiClient } from "../api/client";

export interface SourceDrawerProps {
  citation: Citation | null;
  client: PersonalWikiApiClient;
  open: boolean;
  onClose: () => void;
}

interface SourceState {
  document: DocumentDetail | null;
  chunk: ChunkDetail | null;
  loading: boolean;
  error: string | null;
}

/** 打开 citation 对应的文档和 chunk 详情，作为 Chat 的右侧来源抽屉。 */
export function SourceDrawer({ citation, client, open, onClose }: SourceDrawerProps) {
  const [state, setState] = useState<SourceState>({
    document: null,
    chunk: null,
    loading: false,
    error: null,
  });

  useEffect(() => {
    if (!open || !citation) {
      return;
    }

    let cancelled = false;
    setState({ document: null, chunk: null, loading: true, error: null });

    Promise.all([client.getDocument(citation.document_id), client.getChunk(citation.chunk_id)])
      .then(([document, chunk]) => {
        if (!cancelled) {
          setState({ document, chunk, loading: false, error: null });
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setState({
            document: null,
            chunk: null,
            loading: false,
            error: error instanceof Error ? error.message : "来源加载失败",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [citation, client, open]);

  return (
    <aside className={`source-drawer ${open ? "open" : ""}`} aria-label="来源详情" aria-hidden={!open}>
      <header className="drawer-header">
        <div>
          <p className="eyebrow">Source</p>
          <h2>引用详情</h2>
        </div>
        <button className="icon-button" type="button" aria-label="关闭来源详情" onClick={onClose}>
          <X size={18} aria-hidden="true" />
        </button>
      </header>

      {!citation ? (
        <p className="empty-state">选择引用后显示来源</p>
      ) : state.loading ? (
        <div className="drawer-loading">
          <Loader2 size={18} aria-hidden="true" />
          <span>加载来源</span>
        </div>
      ) : state.error ? (
        <div className="activity-error">{state.error}</div>
      ) : (
        <div className="drawer-content">
          <section>
            <div className="source-title">
              <FileText size={18} aria-hidden="true" />
              <h3>{state.document?.title ?? `Document ${citation.document_id}`}</h3>
            </div>
            <dl className="metadata-list">
              <div>
                <dt>Document</dt>
                <dd>{citation.document_id}</dd>
              </div>
              <div>
                <dt>Chunk</dt>
                <dd>{citation.chunk_id}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{state.document?.source.name ?? citation.source_id ?? "未知"}</dd>
              </div>
              <div>
                <dt>类型</dt>
                <dd>{state.document?.mime_type ?? "未知"}</dd>
              </div>
            </dl>
          </section>

          <section>
            <h3>定位</h3>
            <p className="muted-line">
              {state.chunk?.heading_path ?? citation.heading_path ?? "无标题路径"}
              {state.chunk?.page_number || citation.page_number
                ? ` · 第 ${state.chunk?.page_number ?? citation.page_number} 页`
                : ""}
            </p>
          </section>

          <section>
            <h3>片段</h3>
            <p className="chunk-text">{state.chunk?.text ?? citation.snippet ?? "没有片段文本"}</p>
          </section>

          <section>
            <h3>URI</h3>
            <p className="uri-line">{state.document?.uri ?? state.chunk?.document.uri ?? "未知"}</p>
          </section>
        </div>
      )}
    </aside>
  );
}
