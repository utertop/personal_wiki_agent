import { expect, test } from "@playwright/test";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";

test("creates a source, indexes it, chats with citations, and opens the source drawer", async ({ page }) => {
  const knowledgeDir = path.resolve("../.codex_tmp/e2e_knowledge");
  rmSync(knowledgeDir, { recursive: true, force: true });
  mkdirSync(knowledgeDir, { recursive: true });
  writeFileSync(
    path.join(knowledgeDir, "rag.md"),
    "# RAG\n\nRAG 可以检索个人知识库资料，并基于来源引用回答问题。",
    "utf-8",
  );

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Personal Wiki Agent" })).toBeVisible();

  await page.getByRole("button", { name: /数据源/ }).click();
  await page.getByLabel("名称").fill("E2E 知识目录");
  await page.getByLabel("URI").fill(knowledgeDir);
  await page.getByRole("button", { name: /添加数据源/ }).click();
  await expect(page.getByRole("cell", { name: "E2E 知识目录" })).toBeVisible();

  await page.getByRole("button", { name: /索引/ }).click();
  await page.getByRole("button", { name: /运行索引/ }).click();
  await expect(page.getByText("completed")).toBeVisible();
  await expect(page.getByText("1 / 1")).toBeVisible();

  await page.getByRole("button", { name: /^Chat$/ }).click();
  await page.getByLabel("输入问题").fill("RAG 怎么帮助个人知识库？");
  await page.getByRole("button", { name: /发送/ }).click();

  await expect(page.getByText("RAG 可以先检索个人知识库资料")).toBeVisible();
  await expect(page.getByRole("button", { name: /引用 1/ })).toBeVisible();

  await page.getByRole("button", { name: /引用 1/ }).click();
  await expect(page.getByRole("heading", { name: "引用详情" })).toBeVisible();
  await expect(page.getByText("RAG 可以检索个人知识库资料")).toBeVisible();
  await expect(page.getByText("E2E 知识目录")).toBeVisible();
});
