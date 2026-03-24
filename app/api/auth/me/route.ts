import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const PROFILE_TIMEOUT_MS = 10_000;

/**
 * Proxy to the backend's authenticated user endpoint.
 * The Next.js layer is a thin pass-through — it reads the httpOnly cookie
 * (which the browser can't access directly) and forwards it as a Bearer token
 * to the backend, which owns JWT verification and user data.
 */
export async function GET(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(PROFILE_TIMEOUT_MS),
    });

    if (!res.ok) {
      if (res.status === 401) {
        // JWT expired/invalid — clear the stale cookie
        const response = NextResponse.json(
          { error: "Session expired" },
          { status: 401 }
        );
        response.cookies.delete("cybaop_token");
        return response;
      }
      return NextResponse.json(
        { error: "Failed to fetch profile" },
        { status: res.status >= 500 ? 502 : res.status }
      );
    }

    return NextResponse.json(await res.json());
  } catch (err) {
    console.error("Backend unreachable for /auth/me:", err);
    return NextResponse.json(
      { error: "Profile service unavailable" },
      { status: 503 }
    );
  }
}
