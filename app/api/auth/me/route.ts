import { NextRequest, NextResponse } from "next/server";
import { backendFetch } from "@/lib/fetch";

export async function GET(req: NextRequest) {
  const token = req.cookies.get("cybaop_token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  // Try backend first (JWT path)
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

    // If backend rejects the token, it might be a raw SC token (fallback path)
    if (res.status === 401) {
      // Try using it as a SoundCloud token directly
      return fetchFromSoundCloud(token);
    }

    return NextResponse.json(
      { error: "Failed to fetch profile" },
      { status: res.status >= 500 ? 502 : res.status }
    );
  } catch {
    // Backend unreachable — try SC token directly
    return fetchFromSoundCloud(token);
  }
}

async function fetchFromSoundCloud(token: string) {
  try {
    const res = await fetch("https://api.soundcloud.com/me", {
      headers: { Authorization: `OAuth ${token}` },
    });

    if (!res.ok) {
      const response = NextResponse.json(
        { error: "Session expired" },
        { status: 401 }
      );
      response.cookies.delete("cybaop_token");
      return response;
    }

    const profile = await res.json();
    return NextResponse.json({
      user_id: `sc_${profile.id}`,
      username: profile.permalink || profile.username,
      display_name: profile.full_name || profile.username,
      followers_count: profile.followers_count,
      following_count: profile.followings_count,
      track_count: profile.track_count,
      playlist_count: profile.playlist_count,
      likes_count: profile.public_favorites_count || profile.likes_count,
      avatar_url: profile.avatar_url,
      tier: "free",
    });
  } catch {
    return NextResponse.json(
      { error: "Profile service unavailable" },
      { status: 503 }
    );
  }
}
