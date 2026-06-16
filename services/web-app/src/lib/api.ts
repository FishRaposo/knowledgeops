import { getDemoResponse } from "./demoData";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";
const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN;

// When the backend is unreachable, the console falls back to a static demo
// dataset so the UI stays fully interactive with no services running. This flag
// tracks whether we are currently serving demo data so the UI can show a banner.
let demoMode = false;
const demoListeners = new Set<(active: boolean) => void>();

export function isDemoMode(): boolean {
  return demoMode;
}

export function subscribeDemoMode(listener: (active: boolean) => void): () => void {
  demoListeners.add(listener);
  return () => {
    demoListeners.delete(listener);
  };
}

function setDemoMode(active: boolean): void {
  if (demoMode === active) return;
  demoMode = active;
  for (const listener of demoListeners) listener(active);
}

/** Error raised when the server returns a non-OK HTTP status. */
export class ApiHttpError extends Error {
  readonly status: number;
  constructor(status: number, statusText: string) {
    super(`API error: ${status} ${statusText}`);
    this.name = "ApiHttpError";
    this.status = status;
  }
}

function getAuthToken(): string | undefined {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem("knowledgeops_token");
    if (stored) return stored;
  }
  return DEMO_TOKEN;
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options?.headers);
  const isFormData = options?.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const method = options?.method ?? "GET";

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      // Any non-OK status (a 5xx outage, or a 404 when the /api proxy is not
      // wired to a running backend) falls back to demo data when available, so
      // the console is usable with no backend. Auth failures (401/403) are NOT
      // masked — they should surface to the user.
      if (response.status !== 401 && response.status !== 403) {
        const demo = maybeDemo<T>(path, method, options?.body);
        if (demo !== undefined) return demo;
      }
      throw new ApiHttpError(response.status, response.statusText);
    }

    setDemoMode(false);
    return response.json() as Promise<T>;
  } catch (err) {
    // An HTTP error already had its chance at a demo fallback above; re-throw it
    // so auth failures and unmatched routes surface to the caller. Only genuine
    // network failures (backend down) fall through to the demo dataset here.
    if (err instanceof ApiHttpError) throw err;
    const demo = maybeDemo<T>(path, method, options?.body);
    if (demo !== undefined) return demo;
    throw err;
  }
}

function maybeDemo<T>(
  path: string,
  method: string,
  body: BodyInit | null | undefined
): T | undefined {
  const demo = getDemoResponse(
    path,
    method,
    typeof body === "string" ? body : undefined
  );
  if (demo === undefined) return undefined;
  setDemoMode(true);
  return demo as T;
}

export function setApiToken(token: string): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("knowledgeops_token", token);
  }
}
