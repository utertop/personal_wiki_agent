import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App navigation", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ items: [] }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("opens the Memory management page from the sidebar", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /Memory/ }));

    expect(await screen.findByRole("heading", { name: "长期记忆" })).toBeTruthy();
  });
});
