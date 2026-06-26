import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatView } from "./ChatView";
import type { PersonalWikiApiClient } from "../api/client";

describe("ChatView 对话工作台", () => {
  it("提交问题后展示回答，并允许点击 citation 打开来源", async () => {
    const openSource = vi.fn();
    const client: PersonalWikiApiClient = {
      chat: vi.fn().mockResolvedValue({
        answer: "索引任务会先解析文档，再写入检索索引。",
        confidence: 0.84,
        citations: [
          {
            document_id: 42,
            chunk_id: 420,
            source_id: 3,
            heading_path: "索引流程",
            snippet: "解析文档并建立索引",
          },
        ],
        retrieval_summary: {
          total_results: 4,
          used_results: 1,
          source_count: 1,
          has_reliable_sources: true,
        },
        model: "local/demo",
        memories_used: [],
      }),
      search: vi.fn(),
      getDocument: vi.fn(),
      getChunk: vi.fn(),
      listMemory: vi.fn(),
      createMemory: vi.fn(),
      listSources: vi.fn(),
      createSource: vi.fn(),
      runIndex: vi.fn(),
      listIndexJobs: vi.fn(),
    };

    render(<ChatView client={client} onOpenSource={openSource} />);

    fireEvent.change(screen.getByLabelText("输入问题"), {
      target: { value: "索引任务怎么执行？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "发送" }));

    await screen.findByText("索引任务会先解析文档，再写入检索索引。");
    fireEvent.click(screen.getByRole("button", { name: /引用 1/ }));

    await waitFor(() => {
      expect(openSource).toHaveBeenCalledWith(
        expect.objectContaining({ document_id: 42, chunk_id: 420 }),
      );
    });
  });
});
