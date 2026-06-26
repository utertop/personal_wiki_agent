import { afterEach, describe, expect, it, vi } from "vitest";
import { createApiClient, normalizeChatResponse } from "./client";

describe("Personal Wiki API 客户端", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("把缺失的 memories_used 规范为空数组，避免 UI 读取时报错", () => {
    const response = normalizeChatResponse({
      answer: "回答",
      citations: [],
      confidence: 0.72,
      retrieval_summary: {
        total_results: 2,
        used_results: 1,
        source_count: 1,
        has_reliable_sources: true,
      },
      model: "local:test",
    });

    expect(response.memories_used).toEqual([]);
  });

  it("使用统一 JSON 协议调用 Chat API", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          answer: "来自知识库的回答",
          citations: [],
          confidence: 0.8,
          retrieval_summary: {
            total_results: 3,
            used_results: 2,
            source_count: 1,
            has_reliable_sources: true,
          },
          model: "demo-model",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient("/api");
    const result = await client.chat({ message: "索引策略是什么？", top_k: 3 });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/chat",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "索引策略是什么？", top_k: 3 }),
      }),
    );
    expect(result.answer).toBe("来自知识库的回答");
    expect(result.memories_used).toEqual([]);
  });

  it("调用 Source 和 Index API 管理数据源与索引任务", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                source_id: 1,
                source_type: "local_directory",
                name: "本地资料",
                uri: "E:/Knowledge",
                storage_mode: "local_only",
                sync_direction: "read_only",
                enabled: true,
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            source_id: 2,
            source_type: "obsidian_vault",
            name: "Obsidian",
            uri: "E:/Vault",
            storage_mode: "local_only",
            sync_direction: "read_only",
            enabled: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            jobs: [
              {
                job_id: 10,
                source_id: 2,
                source_name: "Obsidian",
                status: "completed",
                total_items: 1,
                processed_items: 1,
                failed_items: 0,
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                job_id: 10,
                source_id: 2,
                source_name: "Obsidian",
                status: "completed",
                total_items: 1,
                processed_items: 1,
                failed_items: 0,
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient("/api");

    expect((await client.listSources()).items[0].name).toBe("本地资料");
    await client.createSource({
      source_type: "obsidian_vault",
      name: "Obsidian",
      uri: "E:/Vault",
    });
    expect((await client.runIndex({ source_id: 2 })).jobs[0].status).toBe("completed");
    expect((await client.listIndexJobs()).items[0].source_name).toBe("Obsidian");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/sources", expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/index/run", expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "/api/index/jobs",
      expect.objectContaining({ headers: { "Content-Type": "application/json" } }),
    );
  });
});
