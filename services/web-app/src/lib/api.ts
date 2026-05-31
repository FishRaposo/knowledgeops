const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";
const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN;

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

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function setApiToken(token: string): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("knowledgeops_token", token);
  }
}
