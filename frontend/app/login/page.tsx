'use client';

import { Suspense, useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore, type UserRole } from '../../store/useAuthStore';

const roles: UserRole[] = ['Director', 'Host', 'Mentor', 'Admin'];

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((state) => state.login);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('Director');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password, role);
      router.push(searchParams.get('next') || '/dashboard');
    } catch {
      setError('Unable to sign in. Check your TFI email and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0B1020] px-4 py-6 text-slate-200 sm:px-6">
      <div className="mx-auto grid max-w-5xl gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <section className="glass-panel hidden p-6 lg:block">
          <p className="text-xs font-medium uppercase tracking-widest text-[#3B82F6]">Access control</p>
          <h1 className="mt-3 text-3xl font-semibold text-white">Role-aware operations for TFI teams</h1>
          <div className="mt-6 grid gap-3">
            {roles.map((roleOption) => (
              <div key={roleOption} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                <p className="font-medium">{roleOption}</p>
                <p className="mt-1 text-sm text-slate-400">Scoped access to internship workflows and analytics.</p>
              </div>
            ))}
          </div>
        </section>

        <section className="glass-panel p-6">
          <div className="mb-6">
            <p className="text-xs font-medium uppercase tracking-widest text-[#3B82F6]">Secure sign in</p>
            <h1 className="mt-3 text-2xl font-semibold text-white">Sign in to Command Center 2.0</h1>
            <p className="mt-2 text-sm text-slate-400">Use a TFI role to access the current operational console.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block text-sm font-medium text-slate-300">
              Email
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 h-11 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-white outline-none transition focus:border-[#3B82F6]"
                required
              />
            </label>

            <label className="block text-sm font-medium text-slate-300">
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 h-11 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-white outline-none transition focus:border-[#3B82F6]"
                required
              />
            </label>

            <label className="block text-sm font-medium text-slate-300">
              Role
              <select
                value={role}
                onChange={(event) => setRole(event.target.value as UserRole)}
                className="mt-2 h-11 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-white outline-none transition focus:border-[#3B82F6]"
              >
                {roles.map((roleOption) => (
                  <option key={roleOption} value={roleOption}>
                    {roleOption}
                  </option>
                ))}
              </select>
            </label>

            {error && <p className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-100">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="h-11 w-full rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Sign in'}
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
