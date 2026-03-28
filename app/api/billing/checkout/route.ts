import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function POST(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;
  if (!token) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

  try {
    const res = await backendFetch({
      path: "/billing/checkout",
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      timeoutMs: 15_000,
      retries: 0,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ success: false, message: "Checkout service unavailable" }, { status: 502 });
  }
}
