import { NextRequest, NextResponse } from "next/server";

// Simple in-memory rate limiter for Vercel edge
// 60 requests per minute per IP on API routes
const WINDOW_MS = 60_000;
const MAX_REQUESTS = 60;
const ipHits = new Map<string, { count: number; resetAt: number }>();

function getRateLimitResponse() {
  return NextResponse.json(
    { error: "Too many requests" },
    { status: 429, headers: { "Retry-After": "60" } }
  );
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Only rate-limit API routes (not static pages)
  if (!pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // Skip health-equivalent routes
  if (pathname === "/api/auth/soundcloud") {
    return NextResponse.next();
  }

  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || req.headers.get("x-real-ip")
    || "unknown";

  const now = Date.now();
  const entry = ipHits.get(ip);

  if (!entry || now > entry.resetAt) {
    ipHits.set(ip, { count: 1, resetAt: now + WINDOW_MS });
    return NextResponse.next();
  }

  entry.count++;

  if (entry.count > MAX_REQUESTS) {
    return getRateLimitResponse();
  }

  return NextResponse.next();
}

export const config = {
  matcher: "/api/:path*",
};
