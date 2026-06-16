import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ChatInterface } from "../ChatInterface";

describe("ChatInterface", () => {
  beforeEach(() => {
    // Backend unreachable -> demo fallback answers.
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

  it("shows the empty prompt initially", () => {
    render(<ChatInterface />);
    expect(
      screen.getByText(/ask a question about your knowledge base/i)
    ).toBeInTheDocument();
  });

  it("answers an in-scope query with a citation from demo data", async () => {
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "What is the refund policy?" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      // "30 days" appears in both the answer and the citation excerpt.
      expect(screen.getAllByText(/30 days/i).length).toBeGreaterThan(0);
    });
    expect(screen.getByText(/sources:/i)).toBeInTheDocument();
  });

  it("shows a refusal note for an out-of-scope query", async () => {
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "tell me about zzzzz" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/outside the knowledge base scope/i)
      ).toBeInTheDocument();
    });
  });
});
