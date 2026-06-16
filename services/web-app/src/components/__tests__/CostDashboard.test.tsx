import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { CostDashboard } from "../CostDashboard";

describe("CostDashboard", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders demo cost summary after loading", async () => {
    render(<CostDashboard />);
    await waitFor(() => {
      expect(screen.getByText(/total spend/i)).toBeInTheDocument();
    });
    // Demo summary aggregates two services (shown in the summary panel and
    // again in the recent-requests table, hence getAllByText).
    expect(screen.getAllByText("retrieval-service").length).toBeGreaterThan(0);
    expect(screen.getAllByText("eval-service").length).toBeGreaterThan(0);
  });

  it("renders demo budget alerts", async () => {
    render(<CostDashboard />);
    await waitFor(() => {
      expect(screen.getByText(/demo budget/i)).toBeInTheDocument();
    });
  });
});
