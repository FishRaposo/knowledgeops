import { test, expect } from "@playwright/test";

test("homepage loads without errors", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("body")).toBeVisible();
});
