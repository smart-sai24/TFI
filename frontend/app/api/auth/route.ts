import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const cookieName = 'tfi_token';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const isFirebaseSession = Boolean(body.idToken);
  const endpoint = isFirebaseSession ? 'session' : 'login';
  const payload = isFirebaseSession
    ? { id_token: body.idToken, role: body.role }
    : { email: body.email, password: body.password };

  const response = await fetch(`${backendUrl}/auth/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  const nextResponse = NextResponse.json(data, { status: response.status });
  if (response.ok && data.access_token) {
    nextResponse.cookies.set(cookieName, data.access_token, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      maxAge: data.expires_in ?? 60 * 60 * 8,
    });
  }
  return nextResponse;
}

export async function DELETE() {
  const response = NextResponse.json({ status: 'ok' });
  response.cookies.set(cookieName, '', { path: '/', maxAge: 0 });
  return response;
}
