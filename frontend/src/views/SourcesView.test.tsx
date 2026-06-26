import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PersonalWikiApiClient } from "../api/client";
import { SourcesView } from "./SourcesView";


describe("SourcesView 数据源页", () => {
  it("加载真实数据源，并允许创建新的本地数据源", async () => {
    const client: PersonalWikiApiClient = {
      chat: vi.fn(),
      search: vi.fn(),
      getDocument: vi.fn(),
      getChunk: vi.fn(),
      listMemory: vi.fn(),
      createMemory: vi.fn(),
      listSources: vi.fn().mockResolvedValueOnce({
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
      }).mockResolvedValueOnce({
        items: [
          {
            source_id: 2,
            source_type: "obsidian_vault",
            name: "Obsidian",
            uri: "E:/Vault",
            storage_mode: "local_only",
            sync_direction: "read_only",
            enabled: true,
          },
        ],
      }),
      createSource: vi.fn().mockResolvedValue({ source_id: 2 }),
      runIndex: vi.fn(),
      listIndexJobs: vi.fn(),
    };

    render(<SourcesView client={client} />);

    await screen.findByText("本地资料");
    fireEvent.change(screen.getByLabelText("名称"), { target: { value: "Obsidian" } });
    fireEvent.change(screen.getByLabelText("URI"), { target: { value: "E:/Vault" } });
    fireEvent.change(screen.getByLabelText("类型"), { target: { value: "obsidian_vault" } });
    fireEvent.click(screen.getByRole("button", { name: "添加数据源" }));

    await screen.findByText("Obsidian");
    expect(client.createSource).toHaveBeenCalledWith({
      source_type: "obsidian_vault",
      name: "Obsidian",
      uri: "E:/Vault",
    });
  });
});
