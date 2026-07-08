import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";

const isWindows = process.platform === "win32";
const pythonCommand = isWindows && existsSync("../.venv/Scripts/python.exe") ? ".\\.venv\\Scripts\\python.exe" : "python";
const npmCommand = isWindows ? "npm.cmd" : "npm";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${pythonCommand} backend/tests/e2e_server.py`,
      cwd: "..",
      url: "http://127.0.0.1:8765/health",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: `${npmCommand} run dev -- --host 127.0.0.1 --port 5173`,
      cwd: ".",
      env: {
        VITE_API_BASE_URL: "http://127.0.0.1:8765",
      },
      url: "http://127.0.0.1:5173",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
