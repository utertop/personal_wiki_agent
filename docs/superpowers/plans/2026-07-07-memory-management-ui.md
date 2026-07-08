# Memory Management UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a frontend Memory management page that can list, filter, and create long-term memories through the existing Memory API.

**Architecture:** Reuse the existing `PersonalWikiApiClient` Memory methods and the current management-view layout. Keep Memory separate from document citations: this UI only manages `/memory`, and does not present memories as knowledge-source references.

**Tech Stack:** React 18, Vite, TypeScript, Vitest, Testing Library, Playwright, existing FastAPI `/memory` endpoints.

## Global Constraints

- Do not add archive/delete controls until backend `PATCH /memory/{id}` or `DELETE /memory/{id}` exists.
- Supported memory types remain `user_preference`, `project_context`, `workflow_habit`, and `stable_fact`.
- Keep UI copy focused on current capabilities: list, search/filter, create.
- Preserve existing app shell and management page visual patterns.

---

### Task 1: Memory View

**Files:**
- Create: `frontend/src/views/MemoryView.tsx`
- Test: `frontend/src/views/MemoryView.test.tsx`

**Interfaces:**
- Consumes: `PersonalWikiApiClient.listMemory(params)` and `PersonalWikiApiClient.createMemory(request)`.
- Produces: `MemoryView({ client }: { client: PersonalWikiApiClient })`.

- [ ] Write a failing test that renders existing memory rows, submits filters, creates a memory, and verifies the API calls.
- [ ] Run `npm.cmd test -- MemoryView.test.tsx` and confirm it fails because `MemoryView` does not exist.
- [ ] Implement `MemoryView` with filter form, create form, refresh button, loading/error states, and table.
- [ ] Run `npm.cmd test -- MemoryView.test.tsx` and confirm it passes.

### Task 2: App Navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `MemoryView`.
- Produces: a sidebar Memory tab that renders the Memory management page.

- [ ] Write a failing app-level test that clicks the Memory navigation item and sees the Memory page heading.
- [ ] Run `npm.cmd test -- App.test.tsx` and confirm it fails.
- [ ] Add the Memory tab, icon, active view state, and responsive nav grid adjustment.
- [ ] Run `npm.cmd test -- App.test.tsx` and confirm it passes.

### Task 3: E2E And Docs

**Files:**
- Modify: `frontend/e2e/real-backend.spec.ts`
- Modify: `README.md`
- Modify: `docs/mvp-acceptance-report.md`

**Interfaces:**
- Consumes: real FastAPI E2E test server and existing `/memory` endpoint.
- Produces: browser coverage for Memory create/search/list behavior.

- [ ] Extend Playwright E2E to create a memory, filter it, and confirm it appears in the Memory table.
- [ ] Update docs to say Memory management UI is implemented and E2E-covered.
- [ ] Run frontend unit tests, TypeScript, build, Playwright E2E, backend tests, and docs hygiene.
