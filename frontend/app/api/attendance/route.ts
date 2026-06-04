import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const token = request.cookies.get('tfi_token')?.value;
  const response = await fetch(`${backendUrl}/attendance/import`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-TFI-Role': 'Host',
    },
    body: await request.formData(),
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
