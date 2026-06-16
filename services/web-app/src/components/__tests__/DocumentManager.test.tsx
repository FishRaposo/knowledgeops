import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { DocumentManager } from "../DocumentManager";

describe("DocumentManager", () => {
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

  it("shows a loading state then renders demo documents", async () => {
    render(<DocumentManager />);
    expect(screen.getByText(/loading documents/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Employee Handbook 2026")).toBeInTheDocument();
    });
    // Demo data includes a document in the processing state.
    expect(screen.getByText("processing")).toBeInTheDocument();
  });

  it("renders an upload control", async () => {
    render(<DocumentManager />);
    await waitFor(() => {
      expect(screen.getByText(/upload document/i)).toBeInTheDocument();
    });
  });
});
