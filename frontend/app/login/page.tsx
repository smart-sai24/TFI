'use client';

import { Suspense, useState, type FormEvent } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '../../store/useAuthStore';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((state) => state.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      router.push(searchParams.get('next') || '/dashboard');
    } catch {
      setError('Unable to sign in. Check your TFI email and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative grid min-h-screen overflow-hidden bg-[#070A0F] px-4 py-8 text-white sm:px-6">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(239,68,68,0.36),transparent_28%),radial-gradient(circle_at_82%_20%,rgba(255,255,255,0.12),transparent_22%),linear-gradient(135deg,#090B10_0%,#111827_42%,#7F1D1D_100%)]" />
      <div className="absolute left-1/2 top-1/2 h-[680px] w-[680px] -translate-x-1/2 -translate-y-1/2 rounded-[42%_58%_48%_52%] bg-gradient-to-br from-white/92 via-red-100/82 to-red-300/72 shadow-[0_50px_140px_rgba(0,0,0,0.36)]" />
      <div className="absolute left-[17%] top-[24%] h-32 w-32 rounded-[38%_62%_45%_55%] bg-gradient-to-br from-[#B91C1C] to-[#111827] opacity-80 blur-sm" />
      <div className="absolute bottom-[12%] right-[18%] h-40 w-40 rounded-[58%_42%_54%_46%] bg-gradient-to-br from-white/40 to-[#EF4444]/70 blur-sm" />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-center">
        <section className="w-full max-w-[520px] rounded-[32px] border border-white/55 bg-white/16 p-5 shadow-[0_34px_100px_rgba(0,0,0,0.35)] backdrop-blur-2xl sm:p-8">
          <div className="mx-auto -mt-20 mb-5 grid h-32 w-32 place-items-center rounded-full bg-white shadow-[0_24px_60px_rgba(0,0,0,0.22)]">
            <span className="relative h-20 w-20 overflow-hidden rounded-2xl">
              <Image src="/logo.png" alt="Techno Future India logo" fill sizes="80px" className="object-contain" />
            </span>
          </div>

          <div className="mb-8 text-center">
            <p className="text-xs font-black uppercase tracking-[0.28em] text-red-100">Techno Future India</p>
            <h1 className="mt-3 text-4xl font-black text-white sm:text-5xl">Sign In</h1>
            <p className="mt-3 text-sm font-medium text-white/78">Access Command Center 2.0 with your TFI account.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-white/82">Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@techofutureindia.com"
                className="h-14 w-full rounded-2xl border border-white/65 bg-white/10 px-5 text-base font-semibold text-white outline-none transition placeholder:text-white/55 focus:border-white focus:bg-white/18"
                required
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-bold text-white/82">Password</span>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter password"
                  className="h-14 w-full rounded-2xl border border-white/65 bg-white/10 px-5 pr-16 text-base font-semibold text-white outline-none transition placeholder:text-white/55 focus:border-white focus:bg-white/18"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-3 top-1/2 h-9 -translate-y-1/2 rounded-xl px-3 text-xs font-black uppercase tracking-wide text-white/76 transition hover:bg-white/15 hover:text-white"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </label>

            <div className="flex items-center justify-between gap-3 text-sm text-white/78">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="h-4 w-4 rounded border-white/40 accent-[#B91C1C]" />
                <span>Remember me</span>
              </label>
              <Link href="/" className="font-semibold text-white underline-offset-4 hover:underline">
                Back home
              </Link>
            </div>

            {error && <p className="rounded-2xl border border-red-100/40 bg-[#7F1D1D]/45 p-3 text-sm font-semibold text-red-50">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="h-14 w-full rounded-2xl bg-gradient-to-r from-[#111827] via-[#B91C1C] to-[#EF4444] px-5 text-base font-black uppercase tracking-[0.18em] text-white shadow-[0_22px_50px_rgba(127,29,29,0.34)] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Login'}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-[#0B1020]" />}>
      <LoginContent />
    </Suspense>
  );
}
