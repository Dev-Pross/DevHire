// middleware.ts
import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Simple in-memory counter (not persisted, resets on restart)
let requestCount = 0;

// This middleware only applies to all routes after /api
export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Match only /api/* (case-sensitive)
  const isApi = pathname.startsWith("/api/");

  if (isApi) {
    requestCount += 1;
    console.log(`[Analytics] Request #${requestCount} to: ${pathname}`);

    const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
    if (!token) {
      return NextResponse.redirect(new URL("/signin", req.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*"],
};
