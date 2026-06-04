'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

const commands = [
  { label: 'Executive Analytics Center', href: '/dashboard', scope: 'Director' },
  { label: 'Operations Command Center', href: '/dashboard', scope: 'Host' },
  { label: 'Student Success Hub', href: '/dashboard', scope: 'Mentor' },
  { label: 'System Control Center', href: '/dashboard', scope: 'Admin' },
  { label: 'Attendance Intelligence', href: '/attendance', scope: 'Operations' },
  { label: 'Assignment Intelligence', href: '/assignments', scope: 'Mentors' },
  { label: 'Report Center', href: '/reports', scope: 'Executive' },
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === 'Escape') setOpen(false);
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const filteredCommands = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    if (!normalized) return commands;
    return commands.filter((command) => `${command.label} ${command.scope}`.toLowerCase().includes(normalized));
  }, [query]);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="hidden h-9 items-center gap-2 rounded-lg border border-white/10 bg-[#111827] px-3 text-sm text-slate-400 transition hover:border-[#3B82F6] hover:text-white lg:flex"
      >
        <span>Search</span>
        <kbd className="rounded border border-white/10 px-1.5 py-0.5 text-[11px] text-slate-500">Ctrl K</kbd>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-[100] bg-[#0B1020]/70 px-4 pt-24 backdrop-blur-sm" onMouseDown={() => setOpen(false)}>
      <div
        className="mx-auto w-full max-w-2xl overflow-hidden rounded-xl border border-white/10 bg-[#111827] shadow-2xl"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="border-b border-white/10 p-3">
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search command centers, workflows, reports..."
            className="h-11 w-full rounded-lg border border-white/10 bg-[#0B1020] px-4 text-sm text-white outline-none focus:border-[#3B82F6]"
          />
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredCommands.map((command) => (
            <button
              key={`${command.label}-${command.scope}`}
              onClick={() => {
                router.push(command.href);
                setOpen(false);
              }}
              className="flex w-full items-center justify-between rounded-lg px-3 py-3 text-left text-sm transition hover:bg-[#1F2937]"
            >
              <span className="font-medium text-white">{command.label}</span>
              <span className="text-xs text-slate-500">{command.scope}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
