import { NextResponse, type NextRequest } from "next/server";

/**
 * Safely decodes the payload of a JWT without verifying signature (for Next.js Edge UX routing).
 * Cryptographic signature verification is strictly enforced on the FastAPI backend.
 */
function decodeJwt(token: string): any | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Allow public assets and login routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/static") ||
    pathname === "/favicon.ico" ||
    pathname === "/" ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/models")
  ) {
    return NextResponse.next();
  }

  // 2. Extract Session Cookie
  const sessionCookie = request.cookies.get("securecall_session")?.value;
  const payload = sessionCookie ? decodeJwt(sessionCookie) : null;
  const isExpired = payload?.exp && payload.exp < Date.now() / 1000;

  // If unauthenticated -> redirect to /login
  if (!payload || isExpired) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const role = payload.role;

  // 3. Citizen restricted routes:
  // "A citizen opening any bulk/court route -> redirect to /dashboard/citizen with toast"
  if (role === "citizen") {
    if (
      pathname.startsWith("/bulk") ||
      pathname.startsWith("/dashboard/forensic") ||
      pathname.startsWith("/dashboard/judge") ||
      pathname.startsWith("/dashboard/admin")
    ) {
      const citizenUrl = new URL("/dashboard/citizen", request.url);
      citizenUrl.searchParams.set("access_denied", "1");
      return NextResponse.redirect(citizenUrl);
    }
  }

  // 4. Forensic Officer restricted routes:
  if (role === "forensic_officer") {
    if (pathname.startsWith("/dashboard/judge") || pathname.startsWith("/dashboard/admin")) {
      const forensicUrl = new URL("/dashboard/forensic", request.url);
      forensicUrl.searchParams.set("access_denied", "1");
      return NextResponse.redirect(forensicUrl);
    }
  }

  // 5. Judge restricted routes:
  if (role === "judge") {
    if (pathname.startsWith("/bulk") || pathname.startsWith("/dashboard/forensic") || pathname.startsWith("/dashboard/admin")) {
      const judgeUrl = new URL("/dashboard/judge", request.url);
      judgeUrl.searchParams.set("access_denied", "1");
      return NextResponse.redirect(judgeUrl);
    }
  }

  // Admin has full access to everything!
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/bulk/:path*",
    "/call/:path*",
  ],
};
