import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "../ErrorBoundary";

function ThrowError() {
  throw new Error("Test error");
}

describe("ErrorBoundary", () => {
  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">Hello</div>
      </ErrorBoundary>
    );
    expect(screen.getByTestId("child")).toHaveTextContent("Hello");
  });

  it("renders fallback UI on error", () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
