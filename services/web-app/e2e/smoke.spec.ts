import { test, expect } from "@playwright/test";

// These smoke checks run against `next start` with NO backend services. The
// console must still render every primary route via its demo-mode fallback.

test("homepage loads and shows the platform header", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("body")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "KnowledgeOps Platform" })
  ).toBeVisible();
});

test("chat route renders the prompt", async ({ page }) => {
  await page.goto("/chat");
  await expect(
    page.getByText(/ask a question about your knowledge base/i)
  ).toBeVisible();
});

test("documents route renders the upload control", async ({ page }) => {
  await page.goto("/documents");
  await expect(page.getByText(/upload document/i)).toBeVisible();
});

test("costs route renders the spend dashboard", async ({ page }) => {
  await page.goto("/costs");
  await expect(page.getByText(/total spend/i)).toBeVisible();
});

test("traces route renders the trace viewer controls", async ({ page }) => {
  await page.goto("/traces");
  await expect(page.getByText(/refresh traces/i)).toBeVisible();
});

test("evals route renders the run control", async ({ page }) => {
  await page.goto("/evals");
  await expect(page.getByRole("button", { name: /run evaluation/i })).toBeVisible();
});

test("demo banner appears when the backend is unavailable", async ({ page }) => {
  await page.goto("/documents");
  // The demo fallback flips on after the first failed API call.
  await expect(page.getByTestId("demo-banner")).toBeVisible({ timeout: 10_000 });
});
