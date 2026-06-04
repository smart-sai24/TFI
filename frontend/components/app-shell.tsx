'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode, useEffect, useState } from 'react';
import { CommandPalette } from './command-palette';
import { useAuthStore, type UserRole } from '../store/useAuthStore';

const workspaceNav: Record<UserRole, { section: string; items: { href: string; label: string; meta: string }[] }[]> = {
  Director: [
    { section: 'Executive Center', items: [{ href: '/dashboard', label: 'Internship Health', meta: 'Command view' }, { href: '/reports', label: 'Board Reports', meta: 'Forecasts' }] },
    { section: 'Decision Systems', items: [{ href: '/dashboard', label: 'Risk Center', meta: 'Interventions' }, { href: '/reports', label: 'Certificate Forecast', meta: 'Eligibility' }] },
  ],
  Host: [
    { section: 'Operations', items: [{ href: '/dashboard', label: 'Live Sessions', meta: 'Today' }, { href: '/attendance', label: 'Attendance Center', meta: 'Imports' }] },
    { section: 'Control Loops', items: [{ href: '/attendance', label: 'Import Center', meta: 'Normalize' }, { href: '/reports', label: 'Alerts', meta: 'Exceptions' }] },
  ],
  Mentor: [
    { section: 'Student Success', items: [{ href: '/dashboard', label: 'Coaching Queue', meta: 'Priority' }, { href: '/assignments', label: 'Reviews', meta: 'Feedback' }] },
    { section: 'Insight Workflows', items: [{ href: '/assignments', label: 'At Risk', meta: 'Recovery' }, { href: '/reports', label: 'Progress Reports', meta: 'Cohort' }] },
  ],
  Admin: [
    { section: 'System Center', items: [{ href: '/dashboard', label: 'Security', meta: 'Events' }, { href: '/reports', label: 'Audit Logs', meta: 'Governance' }] },
    { section: 'Platform Ops', items: [{ href: '/dashboard', label: 'Permissions', meta: 'RBAC' }, { href: '/attendance', label: 'Data Imports', meta: 'Controls' }] },
  ],
};

const roleNames: Record<UserRole, string> = {
  Director: 'Executive Analytics Center',
  Host: 'Operations Command Center',
  Mentor: 'Student Success Hub',
  Admin: 'System Control Center',
};

const roleLabels: UserRole[] = ['Director', 'Host', 'Mentor', 'Admin'];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const hydrate = useAuthStore((state) => state.hydrate);
  const logout = useAuthStore((state) => state.logout);
  const switchRole = useAuthStore((state) => state.switchRole);
  const activeRole = user?.role ?? 'Director';
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <div className="min-h-screen bg-[#0B1020] text-slate-100">
      <aside className="fixed bottom-4 left-4 top-4 z-40 hidden w-72 rounded-2xl border border-white/10 bg-[#0F172A]/96 shadow-[0_24px_80px_rgba(0,0,0,0.4)] backdrop-blur-xl lg:block">
        <div className="flex h-full flex-col">
          <Link href="/dashboard" className="flex items-center gap-3 border-b border-white/10 px-4 py-4">
            <span className="relative h-10 w-10 overflow-hidden rounded-lg border border-white/10 bg-white">
              <Image src="/logo.png" alt="Techno Future India logo" fill sizes="40px" className="object-contain" />
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-white">TFI Command Center</span>
              <span className="block text-xs text-slate-500">Operations OS 2.0</span>
            </span>
          </Link>

          <div className="border-b border-white/10 px-4 py-4">
            <p className="text-[11px] font-medium uppercase tracking-widest text-slate-500">Workspace</p>
            <div className="mt-3 grid grid-cols-2 gap-1 rounded-lg border border-white/10 bg-[#0B1020] p-1">
              {roleLabels.map((role) => (
                <button
                  key={role}
                  onClick={() => switchRole(role)}
                  className={`h-8 rounded-md text-xs font-medium transition ${activeRole === role ? 'bg-[#3B82F6] text-white' : 'text-slate-400 hover:bg-[#1F2937] hover:text-white'}`}
                >
                  {role}
                </button>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">{roleNames[activeRole]}</p>
          </div>

          <nav className="flex-1 overflow-y-auto px-3 py-4">
            {workspaceNav[activeRole].map((group) => (
              <div key={group.section} className="mb-5">
                <p className="mb-2 px-2 text-[11px] font-medium uppercase tracking-widest text-slate-600">{group.section}</p>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const active = pathname === item.href;
                    return (
                      <Link
                        key={`${group.section}-${item.label}`}
                        href={item.href}
                        className={`flex min-h-12 items-center justify-between rounded-lg px-3 py-2 text-sm transition ${
                          active ? 'bg-[#1F2937] text-white ring-1 ring-white/10' : 'text-slate-400 hover:bg-[#1F2937]/70 hover:text-white'
                        }`}
                      >
                        <span>
                          <span className="block font-medium">{item.label}</span>
                          <span className="block text-xs text-slate-600">{item.meta}</span>
                        </span>
                        <span className={`h-2 w-2 rounded-full ${active ? 'bg-[#3B82F6]' : 'bg-slate-700'}`} />
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>

          <div className="border-t border-white/10 p-3">
            <div className="rounded-xl border border-white/10 bg-[#0B1020] p-3">
              <p className="text-[11px] font-medium uppercase tracking-widest text-[#B91C1C]">Signed in</p>
              <p className="mt-2 truncate text-sm font-semibold text-white">{user?.email ?? 'director@techofutureindia.com'}</p>
              <button onClick={() => logout()} className="mt-3 h-8 w-full rounded-lg border border-white/10 text-xs font-medium text-slate-300 transition hover:border-[#B91C1C] hover:text-white">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </aside>

      <div className="lg:pl-80">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0B1020]/92 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <Link href="/dashboard" className="flex items-center gap-2 lg:hidden">
                <span className="relative h-9 w-9 overflow-hidden rounded-lg border border-white/10 bg-white">
                  <Image src="/logo.png" alt="TFI logo" fill sizes="36px" className="object-contain" />
                </span>
              </Link>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">{roleNames[activeRole]}</p>
                <p className="hidden text-xs text-slate-500 sm:block">AI-powered internship operations and intelligence</p>
              </div>
            </div>

            <div className="relative flex items-center gap-2">
              <CommandPalette />
              <button
                onClick={() => setNotificationsOpen((value) => !value)}
                className="relative grid h-9 w-9 place-items-center rounded-lg border border-white/10 bg-[#111827] text-sm font-semibold text-slate-300 transition hover:border-[#3B82F6]"
                title="Notifications"
              >
                <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-[#EF4444]" />
                !
              </button>
              {notificationsOpen && (
                <div className="absolute right-0 top-12 w-80 rounded-xl border border-white/10 bg-[#111827] p-3 shadow-2xl">
                  <p className="px-2 py-1 text-xs font-medium uppercase tracking-widest text-slate-500">Notification center</p>
                  {['Weekly executive report ready', 'Risk queue updated for mentors', 'Attendance import quality check passed'].map((item) => (
                    <div key={item} className="mt-2 rounded-lg border border-white/10 bg-[#0B1020] p-3">
                      <p className="text-sm font-medium text-white">{item}</p>
                      <p className="mt-1 text-xs text-slate-500">Operational intelligence</p>
                    </div>
                  ))}
                </div>
              )}
              <Link href="/login" className="hidden h-9 rounded-lg bg-[#B91C1C] px-3 py-2 text-sm font-medium text-white transition hover:bg-red-700 sm:block">
                Access
              </Link>
            </div>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
