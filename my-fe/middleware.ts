import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const tokenCookie = request.cookies.getAll().find(cookie =>
    cookie.name.startsWith('sb-') && cookie.name.endsWith('-auth-token')
  );
  const token = tokenCookie?.value
  // console.log("token: ",token)

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/Jobs/:path*','/apply'],
}
