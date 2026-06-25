import { FormEvent, useMemo, useState } from "react";
import { Loader2, Send, Settings2 } from "lucide-react";
import type { ChatResponse, Citation, PersonalWikiApiClient } from "../api/client";
import { ToolActivity } from "../components/ToolActivity";

export interface ChatViewProps {
  client: PersonalWikiApiClient;
  onOpenSource: (citation: Citation) => void;
}

type ChatRole = "assistant" | "user";

interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  citations?: Citation[];
  confidence?: number;
}

interface ChatFilters {
  sourceId: string;
  documentId: string;
  fileType: string;
  topK: number;
}

/** 渲染默认进入的对话式 Agent 工作台。 */
export function ChatView({ client, onOpenSource }: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "今天要查哪件事？",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [filters, setFilters] = useState<ChatFilters>({
    sourceId: "",
    documentId: "",
    fileType: "",
    topK: 5,
  });
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSend = draft.trim().length > 0 && !isLoading;
  const filterSummary = useMemo(() => {
    const activeFilters = [
      filters.sourceId ? `source ${filters.sourceId}` : null,
      filters.documentId ? `doc ${filters.documentId}` : null,
      filters.fileType ? filters.fileType : null,
      `top ${filters.topK}`,
    ].filter(Boolean);
    return activeFilters.join(" · ");
  }, [filters]);

  /** 提交用户问题，并把后端回答追加到消息流中。 */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: makeMessageId("user"),
      role: "user",
      content: message,
    };
    setMessages((current) => [...current, userMessage]);
    setDraft("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await client.chat({
        message,
        source_id: parseOptionalNumber(filters.sourceId),
        document_id: parseOptionalNumber(filters.documentId),
        file_type: filters.fileType || undefined,
        top_k: filters.topK,
      });
      setLatestResponse(response);
      setMessages((current) => [
        ...current,
        {
          id: makeMessageId("assistant"),
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          confidence: response.confidence,
        },
      ]);
    } catch (requestError) {
      const messageText = requestError instanceof Error ? requestError.message : "请求失败";
      setError(messageText);
      setMessages((current) => [
        ...current,
        {
          id: makeMessageId("assistant"),
          role: "assistant",
          content: `这次没有拿到回答：${messageText}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="chat-workbench" aria-label="对话工作台">
      <div className="chat-column">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Chat</p>
            <h1>Personal Wiki Agent</h1>
          </div>
          <details className="settings-popover">
            <summary>
              <Settings2 size={17} aria-hidden="true" />
              <span>检索设置</span>
            </summary>
            <div className="settings-grid">
              <label>
                Source ID
                <input
                  inputMode="numeric"
                  value={filters.sourceId}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, sourceId: event.target.value }))
                  }
                />
              </label>
              <label>
                Document ID
                <input
                  inputMode="numeric"
                  value={filters.documentId}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, documentId: event.target.value }))
                  }
                />
              </label>
              <label>
                文件类型
                <select
                  value={filters.fileType}
                  onChange={(event) =>
                    setFilters((current) => ({ ...current, fileType: event.target.value }))
                  }
                >
                  <option value="">全部</option>
                  <option value="markdown">Markdown</option>
                  <option value="text">Text</option>
                  <option value="pdf">PDF</option>
                  <option value="docx">Docx</option>
                  <option value="html">HTML</option>
                </select>
              </label>
              <label>
                Top K
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={filters.topK}
                  onChange={(event) =>
                    setFilters((current) => ({
                      ...current,
                      topK: Number(event.target.value) || 5,
                    }))
                  }
                />
              </label>
            </div>
          </details>
        </header>

        <div className="filter-line">{filterSummary}</div>

        <div className="message-list" aria-live="polite">
          {messages.map((message) => (
            <article className={`message message-${message.role}`} key={message.id}>
              <div className="message-role">{message.role === "user" ? "你" : "Agent"}</div>
              <p>{message.content}</p>
              {message.confidence !== undefined ? (
                <span className="confidence">置信度 {Math.round(message.confidence * 100)}%</span>
              ) : null}
              {message.citations && message.citations.length > 0 ? (
                <div className="citation-row">
                  {message.citations.map((citation, index) => (
                    <button
                      className="citation-button"
                      key={`${citation.document_id}-${citation.chunk_id}-${index}`}
                      type="button"
                      onClick={() => onOpenSource(citation)}
                    >
                      引用 {index + 1}
                      {citation.heading_path ? <span>{citation.heading_path}</span> : null}
                    </button>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
          {isLoading ? (
            <article className="message message-assistant loading-message">
              <Loader2 size={18} aria-hidden="true" />
              <span>检索中</span>
            </article>
          ) : null}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-input">
            输入问题
          </label>
          <textarea
            id="chat-input"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="输入问题"
            rows={3}
          />
          <button className="send-button" type="submit" disabled={!canSend}>
            <Send size={17} aria-hidden="true" />
            <span>发送</span>
          </button>
        </form>
      </div>
      <ToolActivity response={latestResponse} isLoading={isLoading} error={error} />
    </section>
  );
}

/** 把输入框里的数字过滤条件转换为后端可接受的可选 number。 */
function parseOptionalNumber(value: string): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

/** 生成本地消息 ID，避免前端列表渲染时出现重复 key。 */
function makeMessageId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
