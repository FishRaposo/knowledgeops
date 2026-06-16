import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { DemoBanner } from "../DemoBanner";
import { fetchApi } from "../../lib/api";

describe("DemoBanner", () => {
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

  it("is hidden until demo mode activates", async () => {
    const { rerender } = render(<DemoBanner />);
    expect(screen.queryByTestId("demo-banner")).not.toBeInTheDocument();

    // Trigger a demo fallback, which flips the global demo-mode flag.
    await fetchApi("/documents");
    rerender(<DemoBanner />);

    await waitFor(() => {
      expect(screen.getByTestId("demo-banner")).toBeInTheDocument();
    });
    expect(screen.getByText(/demo mode/i)).toBeInTheDocument();
  });
});
