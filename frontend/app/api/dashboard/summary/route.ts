import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const role = request.nextUrl.searchParams.get('role') ?? 'Director';
  const token = request.cookies.get('tfi_token')?.value;
  const response = await fetch(`${backendUrl}/dashboard/summary?role=${encodeURIComponent(role)}`, {
    cache: 'no-store',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-TFI-Role': role,
    },
  });
  const data = await response.json();

  return NextResponse.json(data, { status: response.status });
}
