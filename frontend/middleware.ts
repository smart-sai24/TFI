import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const protectedPrefixes = ['/dashboard', '/attendance', '/assignments', '/reports'];

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const isProtected = protectedPrefixes.some((prefix) => pathname.startsWith(prefix));
  if (!isProtected) return NextResponse.next();

  const token = request.cookies.get('tfi_token')?.value;
  if (token) return NextResponse.next();

  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = '/login';
  loginUrl.searchParams.set('next', pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ['/dashboard/:path*', '/attendance/:path*', '/assignments/:path*', '/reports/:path*'],
};
