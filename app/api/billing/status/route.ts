import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;
  if (!token) return NextResponse.json({ error: "Not authenticated" }, { status: 401 });

  try {
    const res = await backendFetch({
      path: "/billing/status",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    const response = NextResponse.json(data, { status: res.status });

    // If backend detected a tier mismatch, update the cookie with refreshed JWT
    const refreshedToken = res.headers.get("x-refreshed-token");
    if (refreshedToken) {
      response.cookies.set("cybaop_token", refreshedToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 60 * 60 * 24 * 30,
      });
    }

    return response;
  } catch {
    return NextResponse.json({ error: "Billing service unavailable" }, { status: 502 });
  }
}
