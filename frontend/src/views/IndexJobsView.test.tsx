import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PersonalWikiApiClient } from "../api/client";
import { IndexJobsView } from "./IndexJobsView";


describe("IndexJobsView 索引任务页", () => {
  it("加载索引任务，并允许触发全部数据源索引", async () => {
    const client: PersonalWikiApiClient = {
      chat: vi.fn(),
      search: vi.fn(),
      getDocument: vi.fn(),
      getChunk: vi.fn(),
      listMemory: vi.fn(),
      createMemory: vi.fn(),
      listSources: vi.fn(),
      createSource: vi.fn(),
      runIndex: vi.fn().mockResolvedValue({ jobs: [] }),
      listIndexJobs: vi.fn().mockResolvedValueOnce({
        items: [
          {
            job_id: 1,
            source_id: 1,
            source_name: "本地资料",
            status: "completed",
            total_items: 2,
            processed_items: 2,
            failed_items: 0,
          },
        ],
      }).mockResolvedValueOnce({
        items: [
          {
            job_id: 2,
            source_id: 1,
            source_name: "本地资料",
            status: "completed",
            total_items: 3,
            processed_items: 3,
            failed_items: 0,
          },
        ],
      }),
    };

    render(<IndexJobsView client={client} />);

    await screen.findByText("本地资料");
    fireEvent.click(screen.getByRole("button", { name: "运行索引" }));

    await screen.findByText("3 / 3");
    expect(client.runIndex).toHaveBeenCalledWith({});
  });
});
