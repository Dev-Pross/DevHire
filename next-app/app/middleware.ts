// middleware.ts
import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Simple in-memory counter (not persisted, resets on restart)
let requestCount = 0;

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Count all API requests
  if (pathname.startsWith("/api/")) {
    requestCount += 1;
    console.log(`[Analytics] Request #${requestCount} to: ${pathname}`);

    const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
    if (!token) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*"],
};
