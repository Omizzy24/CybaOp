import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

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
      retries: 1,
    });

    if (res.ok) {
      return NextResponse.json(await res.json());
    }

    if (res.status === 401) {
      const response = NextResponse.json({ error: "Session expired" }, { status: 401 });
      response.cookies.delete("cybaop_token");
      return response;
    }

    return NextResponse.json(
      { error: "Failed to fetch profile" },
      { status: res.status >= 500 ? 502 : res.status }
    );
  } catch {
    return NextResponse.json(
      { error: "Profile service unavailable" },
      { status: 503 }
    );
  }
}
