const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8010").replace(/\/$/, "");
const API_KEY = import.meta.env.VITE_API_KEY || "demo-emoti-key-change-me";

const TOKEN_KEY = "emoti_jwt";

export function setAuthToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...((init.headers as Record<string, string>) || {}),
  };

  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else if (API_KEY) {
    // Fallback for the demo until the operator logs in via /auth/login.
    headers["X-Api-Key"] = API_KEY;
  }

  const hasBody = init.body !== undefined && init.body !== null;
  if (hasBody && !headers["Content-Type"] && !(init.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!res.ok) {
    if (res.status === 401) setAuthToken(null);
    const msg = (data as { detail?: string })?.detail || `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, data, msg);
  }
  return data as T;
}

export async function login(username: string, password: string): Promise<{ access_token: string; expires_in: number; role: string }> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body, "login failed");
  }
  const data = (await res.json()) as { access_token: string; expires_in: number; role: string };
  setAuthToken(data.access_token);
  return data;
}

export const apiBase = BASE;
