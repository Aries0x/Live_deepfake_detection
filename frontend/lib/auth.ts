/**
 * SecureCall Frontend Authentication Client.
 * Manages user session state, /auth/me introspection, logout, and permission checks.
 */
import { getApiBase } from "@/lib/config";
import { UserSession, Permission, can } from "@/lib/permissions";

export { can };
export type { UserSession, Permission };

export const TOKEN_STORAGE_KEY = "securecall_token";

/**
 * Retrieves the stored JWT token from localStorage or cookie.
 */
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) return token;

    // Fallback: look in document.cookie
    const match = document.cookie.match(new RegExp("(^| )securecall_session=([^;]+)"));
    if (match) return match[2];
  } catch {
    // Ignore storage restrictions
  }
  return null;
}

/**
 * Persists the session token in localStorage and ensures cookie sync.
 */
export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    document.cookie = `securecall_session=${token}; path=/; max-age=28800; SameSite=Lax`;
  } catch {
    // Ignore storage restrictions
  }
}

/**
 * Clears stored tokens from storage and cookies.
 */
export function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    document.cookie = `securecall_session=; path=/; max-age=0; SameSite=Lax`;
  } catch {
    // Ignore
  }
}

/**
 * Returns authorization headers with Bearer token if available.
 */
export function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = getStoredToken();
  if (token) {
    return {
      ...extraHeaders,
      Authorization: `Bearer ${token}`,
    };
  }
  return extraHeaders;
}

/**
 * Robust authenticated fetch wrapper that includes both cookies (credentials: include)
 * and the Bearer authorization header if a token exists in storage.
 */
export async function authFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(init.headers || {});
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, {
    ...init,
    headers,
    credentials: "include",
  });
}

/**
 * Fetches the currently authenticated user from the backend session cookie or token.
 */
export async function getMe(): Promise<UserSession | null> {
  try {
    const res = await authFetch(`${getApiBase()}/auth/me`, {
      method: "GET",
    });

    if (!res.ok) {
      return null;
    }

    const data = await res.json();
    if (data.token) {
      setStoredToken(data.token);
    }

    return {
      user_id: data.user_id,
      name: data.name,
      role: data.role,
      court_id: data.court_id,
      assigned_cases: data.assigned_cases,
      consent_given: data.consent_given,
    };
  } catch (err) {
    console.warn("getMe network error:", err);
    return null;
  }
}

/**
 * Logs out the current session and redirects to /login.
 */
export async function logout(): Promise<void> {
  try {
    await authFetch(`${getApiBase()}/auth/logout`, {
      method: "POST",
    });
  } catch (err) {
    console.warn("Logout error:", err);
  } finally {
    clearStoredToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }
}

/**
 * Re-authenticates with TOTP before critical actions (e.g. report approval or evidence edit).
 */
export async function reauthTotp(totpCode: string, action: string = "bulk.approve_report"): Promise<boolean> {
  try {
    const res = await authFetch(`${getApiBase()}/auth/reauth-totp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ totp_code: totpCode, action }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Fetches dev credentials helper (only in DEV_MODE).
 */
export async function getDevCredentials(): Promise<any | null> {
  try {
    const res = await authFetch(`${getApiBase()}/auth/dev-credentials`);
    if (res.ok) {
      return await res.json();
    }
    return null;
  } catch {
    return null;
  }
}
