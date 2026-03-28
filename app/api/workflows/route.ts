import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;
  if (!token) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

  try {
    const url = new URL(req.url);
    const status = url.searchParams.get("status");
    const path = status ? `/workflows?status=${status}` : "/workflows";

    const res = await backendFetch({
      path,
      headers: { Authorization: `Bearer ${token}` },
      timeoutMs: 15_000,
      retries: 1,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ success: false, message: "Workflow service unavailable" }, { status: 502 });
  }
}

export async function POST(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;
  if (!token) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

  try {
    const body = await req.text();
    const res = await backendFetch({
      path: "/workflows",
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body,
      timeoutMs: 30_000,
      retries: 0,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ success: false, message: "Workflow service unavailable" }, { status: 502 });
  }
}
