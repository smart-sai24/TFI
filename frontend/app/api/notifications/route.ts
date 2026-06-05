import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

function authHeaders(request: NextRequest) {
  const token = request.cookies.get('tfi_token')?.value;
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(!token ? { 'X-TFI-Role': 'Admin' } : {}),
  };
}

export async function GET(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const response = await fetch(`${backendUrl}/notifications`, {
    cache: 'no-store',
    headers: authHeaders(request),
  });
  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}

export async function POST(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const body = await request.json();
  const isResponseUpdate = body.mode === 'response' && body.notification_id;
  const endpoint = isResponseUpdate ? `notifications/${body.notification_id}/response` : 'notifications/nudges/run';
  const payload = isResponseUpdate
    ? { response_status: body.response_status, notes: body.notes }
    : { auto_send: body.auto_send ?? false, attendance_session_id: body.attendance_session_id ?? null };

  const response = await fetch(`${backendUrl}/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(request),
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
