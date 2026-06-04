import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

function authHeaders(request: NextRequest) {
  const token = request.cookies.get('tfi_token')?.value;
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(!token ? { 'X-TFI-Role': 'Mentor' } : {}),
  };
}

export async function GET(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const response = await fetch(`${backendUrl}/intelligence/ai/overview`, {
    cache: 'no-store',
    headers: authHeaders(request),
  });
  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}

export async function POST(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const body = await request.json();
  const mode = body.mode === 'evaluate' ? 'evaluate' : 'assistant';
  const endpoint = mode === 'evaluate' ? 'ai/assignment-evaluation' : 'assistant';
  const payload = mode === 'evaluate'
    ? { title: body.title, submission_text: body.submission_text, max_score: body.max_score ?? 100 }
    : { query: body.query };

  const response = await fetch(`${backendUrl}/intelligence/${endpoint}`, {
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
