import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const cookieName = 'tfi_token';
const refreshCookieName = 'tfi_refresh_token';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const isFirebaseSession = Boolean(body.idToken);
  const endpoint = isFirebaseSession ? 'session' : 'login';
  const payload = isFirebaseSession
    ? { id_token: body.idToken }
    : { email: body.email, password: body.password };

  let response: Response;
  try {
    response = await fetch(`${backendUrl}/auth/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch {
    return NextResponse.json({ detail: `Backend auth service is unavailable at ${backendUrl}` }, { status: 502 });
  }

  const data = await safeJson(response);
  const nextResponse = NextResponse.json(data, { status: response.status });
  if (response.ok && data.access_token) {
    nextResponse.cookies.set(cookieName, data.access_token, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      maxAge: data.expires_in ?? 60 * 60,
    });
    if (data.refresh_token) {
      nextResponse.cookies.set(refreshCookieName, data.refresh_token, {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        path: '/',
        maxAge: data.refresh_expires_in ?? 60 * 60 * 24 * 7,
      });
    }
  }
  return nextResponse;
}

export async function PATCH(request: NextRequest) {
  const refreshToken = request.cookies.get(refreshCookieName)?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: 'Refresh token missing' }, { status: 401 });
  }

  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  let response: Response;
  try {
    response = await fetch(`${backendUrl}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    return NextResponse.json({ detail: `Backend auth service is unavailable at ${backendUrl}` }, { status: 502 });
  }

  const data = await safeJson(response);
  const nextResponse = NextResponse.json(data, { status: response.status });
  if (response.ok && data.access_token) {
    nextResponse.cookies.set(cookieName, data.access_token, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      path: '/',
      maxAge: data.expires_in ?? 60 * 60,
    });
    if (data.refresh_token) {
      nextResponse.cookies.set(refreshCookieName, data.refresh_token, {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        path: '/',
        maxAge: data.refresh_expires_in ?? 60 * 60 * 24 * 7,
      });
    }
  }
  return nextResponse;
}

export async function DELETE() {
  const response = NextResponse.json({ status: 'ok' });
  response.cookies.set(cookieName, '', { path: '/', maxAge: 0 });
  response.cookies.set(refreshCookieName, '', { path: '/', maxAge: 0 });
  return response;
}

async function safeJson(response: Response) {
  const text = await response.text();
  if (!text) return { detail: response.statusText || 'Empty backend response' };
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}
