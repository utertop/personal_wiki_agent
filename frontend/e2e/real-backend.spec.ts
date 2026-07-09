import { expect, test } from "@playwright/test";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";

test("manages memory, creates a source, indexes it, chats with citations, and opens the source drawer", async ({
  page,
}) => {
  const knowledgeDir = path.resolve("../.codex_tmp/e2e_knowledge");
  rmSync(knowledgeDir, { recursive: true, force: true });
  mkdirSync(knowledgeDir, { recursive: true });
  writeFileSync(
    path.join(knowledgeDir, "rag.md"),
    "# RAG\n\nRAG 可以检索个人知识库资料，并基于来源引用回答问题。",
    "utf-8",
  );

  const longNestedDir = path.join(
    knowledgeDir,
    "nested",
    "very-long-folder-name-for-layout-regression-and-source-drawer",
  );
  mkdirSync(longNestedDir, { recursive: true });
  writeFileSync(
    path.join(longNestedDir, "long-source-title-for-layout-regression.md"),
    "# Extremely Long Source Drawer Heading For Layout Regression\n\n" +
      "longlayouttopic citation snippet keeps a very long source drawer entry readable. " +
      "The path should stay visible without breaking the surrounding chat layout.",
    "utf-8",
  );

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Personal Wiki Agent" })).toBeVisible();

  await page.getByRole("button", { name: /Memory/ }).click();
  await expect(page.getByRole("heading", { name: "长期记忆" })).toBeVisible();
  const memoryCreateForm = page.locator(".memory-create-form");
  await memoryCreateForm.getByLabel("记忆类型").selectOption("user_preference");
  await memoryCreateForm.getByLabel("内容").fill("用户希望回答优先使用中文。");
  await memoryCreateForm.getByLabel("来源").fill("e2e");
  await memoryCreateForm.getByLabel("置信度").fill("0.91");
  await page.getByRole("button", { name: "添加记忆" }).click();
  await expect(page.getByText("用户希望回答优先使用中文。")).toBeVisible();

  const memoryFilterForm = page.locator(".memory-filter-form");
  await memoryFilterForm.getByLabel("关键词").fill("中文");
  await memoryFilterForm.getByLabel("筛选类型").selectOption("user_preference");
  await page.getByRole("button", { name: "查询" }).click();
  await expect(page.getByText("用户希望回答优先使用中文。")).toBeVisible();

  await page.getByRole("button", { name: "Archive memory 1" }).click();
  await expect(page.getByText("暂无长期记忆")).toBeVisible();

  await page.getByRole("button", { name: /数据源/ }).click();
  await page.getByLabel("名称").fill("E2E 知识目录");
  await page.getByLabel("URI").fill(knowledgeDir);
  await page.getByRole("button", { name: /添加数据源/ }).click();
  await expect(page.getByRole("cell", { name: "E2E 知识目录" })).toBeVisible();

  await page.getByRole("button", { name: /索引/ }).click();
  await page.getByRole("button", { name: /运行索引/ }).click();
  await expect(page.getByText("completed")).toBeVisible();
  await expect(page.getByText("2 / 2")).toBeVisible();

  await page.getByRole("button", { name: /^Chat$/ }).click();
  await page.getByLabel("输入问题").fill("RAG 怎么帮助个人知识库？");
  await page.getByRole("button", { name: /发送/ }).click();

  await expect(page.getByText("RAG 可以先检索个人知识库资料")).toBeVisible();
  await expect(page.getByRole("button", { name: /引用 1/ })).toBeVisible();

  await page.getByRole("button", { name: /引用 1/ }).click();
  await expect(page.getByRole("heading", { name: "引用详情" })).toBeVisible();
  await expect(page.getByText("RAG 可以检索个人知识库资料")).toBeVisible();
  await expect(page.getByText("E2E 知识目录")).toBeVisible();

  await page.locator(".source-drawer.open .icon-button").click();
  await expect(page.locator(".source-drawer.open")).toHaveCount(0);

  await page.locator("#chat-input").fill("longlayouttopic");
  await page.locator(".send-button").click();
  const latestCitationButton = page.locator(".citation-button").last();
  await expect(latestCitationButton).toBeVisible();
  await latestCitationButton.click();
  const openDrawer = page.locator(".source-drawer.open");
  await expect(openDrawer).toContainText("Extremely Long Source Drawer Heading For Layout Regression");
  await expect(openDrawer).toContainText("longlayouttopic citation snippet");
  await expect(openDrawer).toContainText("very-long-folder-name-for-layout-regression");
});
