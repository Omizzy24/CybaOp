import { NextResponse } from "next/server";

export async function GET() {
  const clientId = process.env.SOUNDCLOUD_CLIENT_ID;
  const redirectUri = process.env.SOUNDCLOUD_REDIRECT_URI;

  const soundcloudAuthUrl = `https://soundcloud.com/connect?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=non-expiring`;

  return NextResponse.redirect(soundcloudAuthUrl);
}
