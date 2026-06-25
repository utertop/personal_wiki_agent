import { describe, expect, it } from "vitest";
import { buildToolActivities } from "./ToolActivity";

describe("ToolActivity 活动流", () => {
  it("从回答中整理检索、引用、模型和记忆活动", () => {
    const activities = buildToolActivities({
      answer: "回答",
      confidence: 0.91,
      citations: [
        { document_id: 1, chunk_id: 11, source_id: 7, snippet: "片段一" },
        { document_id: 2, chunk_id: 22, source_id: 8, snippet: "片段二" },
      ],
      retrieval_summary: {
        total_results: 5,
        used_results: 2,
        source_count: 2,
        has_reliable_sources: true,
      },
      model: "local/qwen",
      memories_used: [
        {
          memory_id: 9,
          memory_type: "preference",
          content: "偏好本地优先",
          confidence: 0.7,
        },
      ],
    });

    expect(activities.map((activity) => activity.kind)).toEqual([
      "retrieval",
      "citation",
      "model",
      "memory",
    ]);
    expect(activities[0].detail).toContain("命中 5 条");
    expect(activities[3].detail).toContain("1 条记忆");
  });

  it("后端未返回 memories_used 时仍然能生成稳定活动流", () => {
    const activities = buildToolActivities({
      answer: "回答",
      confidence: 0.45,
      citations: [],
      retrieval_summary: {
        total_results: 0,
        used_results: 0,
        source_count: 0,
        has_reliable_sources: false,
      },
      model: null,
    });

    expect(activities.some((activity) => activity.kind === "memory")).toBe(false);
    expect(activities[0].detail).toContain("未找到可靠来源");
  });
});
