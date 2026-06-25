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
});
