import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

/**
 * Proxy to the backend's authenticated user endpoint.
 * Reads the httpOnly cookie and forwards it as a Bearer token.
 */
export async function GET(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  try {
    const res = await backendFetch({
      path: "/auth/me",
      headers: { Authorization: `Bearer ${token}` },
      timeoutMs: 10_000,
      retries: 2,
    });

    if (!res.ok) {
      if (res.status === 401) {
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
