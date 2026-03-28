import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET() {
  try {
    const res = await backendFetch({
      path: "/health",
      timeoutMs: 5_000,
      retries: 0,
    });

    if (res.ok) {
      return NextResponse.json({ status: "ok", backend: "reachable" });
    }

    return NextResponse.json(
      { status: "degraded", backend: "unreachable" },
      { status: 503 }
    );
  } catch {
    return NextResponse.json(
      { status: "degraded", backend: "unreachable" },
      { status: 503 }
    );
  }
}
