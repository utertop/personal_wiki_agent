import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PersonalWikiApiClient } from "../api/client";
import { MemoryView } from "./MemoryView";

describe("MemoryView 长期记忆页", () => {
  it("加载、筛选并创建长期记忆", async () => {
    const client: PersonalWikiApiClient = {
      chat: vi.fn(),
      search: vi.fn(),
      getDocument: vi.fn(),
      getChunk: vi.fn(),
      listMemory: vi
        .fn()
        .mockResolvedValueOnce({
          items: [
            {
              memory_id: 1,
              memory_type: "user_preference",
              content: "用户希望回答优先使用中文。",
              source: "manual",
              confidence: 0.92,
              expires_at: null,
            },
          ],
        })
        .mockResolvedValueOnce({
          items: [
            {
              memory_id: 2,
              memory_type: "project_context",
              content: "当前项目正在补充 Memory 管理 UI。",
              source: "planning",
              confidence: 0.8,
              expires_at: null,
            },
          ],
        })
        .mockResolvedValueOnce({
          items: [
            {
              memory_id: 3,
              memory_type: "stable_fact",
              content: "Personal Wiki Agent 使用 FastAPI 和 React。",
              source: "manual",
              confidence: 0.85,
              expires_at: "2026-12-31T09:30:00",
            },
          ],
        }),
      createMemory: vi.fn().mockResolvedValue({
        memory_id: 3,
        memory_type: "stable_fact",
        content: "Personal Wiki Agent 使用 FastAPI 和 React。",
        source: "manual",
        confidence: 0.85,
        expires_at: "2026-12-31T09:30:00",
      }),
      updateMemory: vi.fn(),
      deleteMemory: vi.fn(),
      listSources: vi.fn(),
      createSource: vi.fn(),
      runIndex: vi.fn(),
      listIndexJobs: vi.fn(),
      cancelIndexJob: vi.fn(),
      retryIndexJob: vi.fn(),
    };

    render(<MemoryView client={client} />);

    await screen.findByText("用户希望回答优先使用中文。");

    fireEvent.change(screen.getByLabelText("关键词"), { target: { value: "项目" } });
    fireEvent.change(screen.getByLabelText("筛选类型"), { target: { value: "project_context" } });
    fireEvent.change(screen.getByLabelText("条数"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "查询" }));

    await screen.findByText("当前项目正在补充 Memory 管理 UI。");
    expect(client.listMemory).toHaveBeenLastCalledWith({
      query: "项目",
      memory_type: "project_context",
      limit: 3,
    });

    fireEvent.change(screen.getByLabelText("记忆类型"), { target: { value: "stable_fact" } });
    fireEvent.change(screen.getByLabelText("内容"), {
      target: { value: "Personal Wiki Agent 使用 FastAPI 和 React。" },
    });
    fireEvent.change(screen.getByLabelText("来源"), { target: { value: "manual" } });
    fireEvent.change(screen.getByLabelText("置信度"), { target: { value: "0.85" } });
    fireEvent.change(screen.getByLabelText("过期时间"), { target: { value: "2026-12-31T09:30" } });
    fireEvent.click(screen.getByRole("button", { name: "添加记忆" }));

    await screen.findByText("Personal Wiki Agent 使用 FastAPI 和 React。");
    await waitFor(() => {
      expect(client.createMemory).toHaveBeenCalledWith({
        memory_type: "stable_fact",
        content: "Personal Wiki Agent 使用 FastAPI 和 React。",
        source: "manual",
        confidence: 0.85,
        expires_at: "2026-12-31T09:30",
      });
    });
  });

  it("edits, archives, and deletes memories", async () => {
    const firstMemory = {
      memory_id: 1,
      memory_type: "user_preference",
      content: "Prefer concise answers.",
      source: "manual",
      confidence: 0.92,
      status: "active",
      expires_at: null,
    };
    const secondMemory = {
      memory_id: 2,
      memory_type: "project_context",
      content: "Project is hardening Memory management.",
      source: "review",
      confidence: 0.8,
      status: "active",
      expires_at: null,
    };
    const editedMemory = {
      ...firstMemory,
      content: "Prefer source-backed concise answers.",
      source: "review",
      confidence: 0.7,
    };
    const client: PersonalWikiApiClient = {
      chat: vi.fn(),
      search: vi.fn(),
      getDocument: vi.fn(),
      getChunk: vi.fn(),
      listMemory: vi
        .fn()
        .mockResolvedValueOnce({ items: [firstMemory, secondMemory] })
        .mockResolvedValueOnce({ items: [editedMemory, secondMemory] })
        .mockResolvedValueOnce({ items: [secondMemory] })
        .mockResolvedValueOnce({ items: [] }),
      createMemory: vi.fn(),
      updateMemory: vi
        .fn()
        .mockResolvedValueOnce(editedMemory)
        .mockResolvedValueOnce({ ...editedMemory, status: "archived" }),
      deleteMemory: vi.fn().mockResolvedValue(undefined),
      listSources: vi.fn(),
      createSource: vi.fn(),
      runIndex: vi.fn(),
      listIndexJobs: vi.fn(),
      cancelIndexJob: vi.fn(),
      retryIndexJob: vi.fn(),
    };

    render(<MemoryView client={client} />);

    await screen.findByText("Prefer concise answers.");
    fireEvent.click(screen.getByRole("button", { name: "Edit memory 1" }));
    fireEvent.change(screen.getByDisplayValue("Prefer concise answers."), {
      target: { value: "Prefer source-backed concise answers." },
    });
    fireEvent.change(screen.getByDisplayValue("manual"), { target: { value: "review" } });
    fireEvent.change(screen.getByDisplayValue("0.92"), { target: { value: "0.7" } });
    fireEvent.click(screen.getByRole("button", { name: "Save memory changes" }));

    await screen.findByText("Prefer source-backed concise answers.");
    expect(client.updateMemory).toHaveBeenCalledWith(1, {
      memory_type: "user_preference",
      content: "Prefer source-backed concise answers.",
      source: "review",
      confidence: 0.7,
    });

    fireEvent.click(screen.getByRole("button", { name: "Archive memory 1" }));
    await waitFor(() => {
      expect(client.updateMemory).toHaveBeenCalledWith(1, { status: "archived" });
    });
    await waitFor(() => {
      expect(screen.queryByText("Prefer source-backed concise answers.")).toBeNull();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete memory 2" }));
    await waitFor(() => {
      expect(client.deleteMemory).toHaveBeenCalledWith(2);
    });
    await waitFor(() => {
      expect(screen.queryByText("Project is hardening Memory management.")).toBeNull();
    });
  });
});
