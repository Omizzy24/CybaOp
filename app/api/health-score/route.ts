import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;
  if (!token) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

  try {
    const res = await backendFetch({
      path: "/workflows/health-score/history",
      headers: { Authorization: `Bearer ${token}` },
      timeoutMs: 15_000,
      retries: 1,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ success: false, message: "Health score service unavailable" }, { status: 502 });
  }
}
