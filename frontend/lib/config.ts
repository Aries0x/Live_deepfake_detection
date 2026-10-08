/**
 * Network configuration utility.
 * Dynamically resolves API and WebSocket URLs using the current browser hostname
 * so the application works seamlessly on localhost and over LAN Wi-Fi (e.g., 172.16.242.15).
 */

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const proto = window.location.protocol;
    const host = window.location.hostname;
    return `${proto}//${host}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function getWsBase(): string {
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname;
    return `${proto}//${host}:8000`;
  }
  return "ws://localhost:8000";
}
