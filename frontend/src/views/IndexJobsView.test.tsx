import { fireEvent, render, screen } from "@testing-library/react";
import { act } from "react";
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
      updateMemory: vi.fn(),
      deleteMemory: vi.fn(),
      listSources: vi.fn(),
      createSource: vi.fn(),
      runIndex: vi.fn().mockResolvedValue({ jobs: [] }),
      cancelIndexJob: vi.fn(),
      retryIndexJob: vi.fn(),
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

  it("allows cancelling queued jobs and retrying failed jobs", async () => {
    const client: PersonalWikiApiClient = {
      chat: vi.fn(),
      search: vi.fn(),
      getDocument: vi.fn(),
      getChunk: vi.fn(),
      listMemory: vi.fn(),
      createMemory: vi.fn(),
      updateMemory: vi.fn(),
      deleteMemory: vi.fn(),
      listSources: vi.fn(),
      createSource: vi.fn(),
      runIndex: vi.fn(),
      cancelIndexJob: vi.fn().mockResolvedValue({
        job_id: 1,
        source_id: 1,
        source_name: "Queued Source",
        status: "cancelled",
        total_items: 0,
        processed_items: 0,
        failed_items: 0,
        attempt_count: 0,
        max_attempts: 3,
      }),
      retryIndexJob: vi.fn().mockResolvedValue({
        job_id: 2,
        source_id: 1,
        source_name: "Failed Source",
        status: "queued",
        total_items: 1,
        processed_items: 0,
        failed_items: 1,
        attempt_count: 1,
        max_attempts: 3,
      }),
      listIndexJobs: vi.fn()
        .mockResolvedValueOnce({
          items: [
            {
              job_id: 1,
              source_id: 1,
              source_name: "Queued Source",
              status: "queued",
              total_items: 0,
              processed_items: 0,
              failed_items: 0,
              attempt_count: 0,
              max_attempts: 3,
            },
            {
              job_id: 2,
              source_id: 1,
              source_name: "Failed Source",
              status: "failed",
              total_items: 1,
              processed_items: 0,
              failed_items: 1,
              attempt_count: 1,
              max_attempts: 3,
              error_message: "boom",
            },
          ],
        })
        .mockResolvedValue({
          items: [],
        }),
    };

    render(<IndexJobsView client={client} />);

    await screen.findByText("boom");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Cancel index job 1" }));
      fireEvent.click(screen.getByRole("button", { name: "Retry index job 2" }));
    });

    expect(client.cancelIndexJob).toHaveBeenCalledWith(1);
    expect(client.retryIndexJob).toHaveBeenCalledWith(2);
  });
});
