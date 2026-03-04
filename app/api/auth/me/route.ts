import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("sc_access_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Not authenticated" },
      { status: 401 }
    );
  }

  const userRes = await fetch("https://api.soundcloud.com/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!userRes.ok) {
    return NextResponse.json(
      { error: "Failed to fetch user profile" },
      { status: 500 }
    );
  }

  const userData = await userRes.json();

  return NextResponse.json(userData);
}
