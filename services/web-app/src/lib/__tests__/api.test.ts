import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchApi, isDemoMode, subscribeDemoMode } from "../api";

describe("fetchApi demo-mode fallback", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON on a successful response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ documents: [{ id: "1" }] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );
    const data = await fetchApi<{ documents: { id: string }[] }>("/documents");
    expect(data.documents[0].id).toBe("1");
    expect(isDemoMode()).toBe(false);
  });

  it("falls back to demo data when the network fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
    const data = await fetchApi<{ documents: unknown[] }>("/documents");
    expect(Array.isArray(data.documents)).toBe(true);
    expect(data.documents.length).toBeGreaterThan(0);
    expect(isDemoMode()).toBe(true);
  });

  it("falls back to demo data on a 5xx response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("boom", { status: 503 }))
    );
    const data = await fetchApi<{ alerts: unknown[] }>("/alerts");
    expect(Array.isArray(data.alerts)).toBe(true);
    expect(isDemoMode()).toBe(true);
  });

  it("falls back to demo data on a 404 (unwired /api proxy)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("Not Found", { status: 404 }))
    );
    const data = await fetchApi<{ status: string }>("/health");
    expect(data.status).toBe("demo");
    expect(isDemoMode()).toBe(true);
  });

  it("does NOT mask auth failures (401/403) with demo data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("Unauthorized", { status: 401 }))
    );
    await expect(fetchApi("/documents")).rejects.toThrow(/401/);
  });

  it("re-throws when there is no demo payload for the route", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
    await expect(fetchApi("/no-such-route")).rejects.toThrow();
  });

  it("notifies demo-mode subscribers when fallback activates", async () => {
    // Force a clean (non-demo) state first so the transition to demo mode is
    // observable regardless of test ordering.
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ traces: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );
    await fetchApi("/traces");

    const states: boolean[] = [];
    const unsubscribe = subscribeDemoMode((active) => states.push(active));
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
    await fetchApi("/traces");
    expect(states).toContain(true);
    unsubscribe();
  });

  it("returns a refusal for an out-of-scope demo query", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
    const data = await fetchApi<{ refusal: boolean }>("/query", {
      method: "POST",
      body: JSON.stringify({ query: "what is the meaning of zzzzz" }),
    });
    expect(data.refusal).toBe(true);
  });

  it("answers an in-scope demo query with citations", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      })
    );
    const data = await fetchApi<{ refusal: boolean; citations: unknown[] }>(
      "/query",
      {
        method: "POST",
        body: JSON.stringify({ query: "what is the refund policy?" }),
      }
    );
    expect(data.refusal).toBe(false);
    expect(data.citations.length).toBeGreaterThan(0);
  });
});
