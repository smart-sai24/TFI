import Image from 'next/image';
import Link from 'next/link';

const heroImage =
  'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1800&q=85';

const platformCards = [
  {
    title: 'AI Analytics',
    body: 'Program health, certificate forecasts, risk queues, and executive summaries.',
    accent: 'from-[#EF4444] via-[#B91C1C] to-[#111827]',
  },
  {
    title: 'Live Operations',
    body: 'Attendance imports, session quality checks, late joiners, and audit trails.',
    accent: 'from-[#111827] via-[#B91C1C] to-[#EF4444]',
  },
  {
    title: 'Mentor Intelligence',
    body: 'Focused coaching lists, assignment signals, and intervention priorities.',
    accent: 'from-[#7F1D1D] via-[#DC2626] to-[#111827]',
  },
];

const metrics = [
  { value: '4', label: 'Role workspaces' },
  { value: '16', label: 'Tests passing' },
  { value: '88', label: 'Audit score' },
];

const roles = ['Director', 'Host', 'Mentor', 'Admin'];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#F6F8FB] text-slate-950">
      <section className="relative min-h-[820px] overflow-hidden">
        <div
          className="absolute inset-0 scale-105 bg-cover bg-center "
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        <div className="absolute inset-0 bg-[#070A0F]/46" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#050608]/96 via-[#111827]/80 to-[#7F1D1D]/20" />
        <div className="absolute inset-0 bg-gradient-to-br from-[#B91C1C]/22 via-transparent to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-44 bg-gradient-to-t from-[#F6F8FB] via-[#F6F8FB]/82 to-transparent" />

        <header className="relative z-10 mx-auto max-w-7xl px-4 pt-5 sm:px-6">
          <div className="flex h-20 items-center justify-between gap-4 rounded-2xl border border-white/15 bg-white/92 px-4 shadow-[0_24px_80px_rgba(8,47,73,0.18)] backdrop-blur-xl sm:px-5">
            <Link href="/" className="flex min-w-0 items-center gap-3">
              <span className="relative h-12 w-12 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <Image src="/logo.png" alt="Techno Future India logo" fill sizes="48px" className="object-contain p-1.5" />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-lg font-black tracking-normal text-[#082F49] sm:text-xl">
                  Techno Future India
                </span>
                <span className="block text-[10px] font-bold uppercase tracking-[0.28em] text-[#B91C1C]">
                  Command Center 
                </span>
              </span>
            </Link>

            <nav className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-black uppercase tracking-wide text-slate-600 lg:flex">
              {[
                ['Platform', '#platform'],
                ['Workspaces', '#workspaces'],
                ['Outcomes', '#outcomes'],
              ].map(([label, href]) => (
                <a key={label} href={href} className="rounded-full px-4 py-2 transition hover:bg-white hover:text-[#B91C1C] hover:shadow-sm">
                  {label}
                </a>
              ))}
            </nav>

            <Link
              href="/login"
              className="inline-flex h-11 items-center justify-center rounded-xl bg-gradient-to-r from-[#B91C1C] to-[#EF4444] px-5 text-sm font-black text-white shadow-[0_16px_38px_rgba(185,28,28,0.32)] transition hover:-translate-y-0.5 hover:from-[#991B1B] hover:to-[#DC2626]"
            >
              Login
            </Link>
          </div>
        </header>

        <div className="relative z-10 mx-auto flex max-w-7xl px-4 pb-32 pt-24 sm:px-6 lg:pt-28">
          <div className="max-w-4xl">
            <h1 className="max-w-4xl text-5xl font-black leading-[0.98] tracking-normal text-white sm:text-6xl lg:text-7xl">
              Learn today.
              <span className="block bg-gradient-to-r from-white via-red-100 to-[#EF4444] bg-clip-text text-transparent">Lead tomorrow.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base font-semibold leading-8 text-slate-200 sm:text-lg">
              A modern TFI operating system for attendance, mentorship, analytics, reports, and student success intelligence.
            </p>
          </div>
        </div>
      </section>

      <section id="platform" className="relative z-20 mx-auto -mt-24 max-w-6xl px-4 sm:px-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_28px_90px_rgba(8,47,73,0.14)] sm:p-5">
          <div className="grid gap-4 lg:grid-cols-[0.85fr_2fr] lg:items-center">
            <div className="px-2 py-4">
              <p className="text-xs font-black uppercase tracking-[0.24em] text-[#B91C1C]">Platform</p>
              <h2 className="mt-3 text-2xl font-black leading-tight text-[#082F49]">
                One premium workspace for the full internship journey.
              </h2>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {platformCards.map((card) => (
                <article key={card.title} className="rounded-xl border border-slate-200 bg-[#F8FAFC] p-4">
                  <div className={`mb-4 h-1.5 rounded-full bg-gradient-to-r ${card.accent}`} />
                  <h3 className="text-base font-black text-[#082F49]">{card.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{card.body}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="workspaces" className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-end">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-[#B91C1C]">Role intelligence</p>
            <h2 className="mt-4 text-3xl font-black leading-tight text-[#082F49] sm:text-4xl">
              Built for every team that moves the internship forward.
            </h2>
          </div>
          <p className="text-base leading-8 text-slate-600">
            Directors get executive clarity, Hosts get operational control, Mentors get student success queues, and Admins get platform governance.
          </p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {roles.map((role) => (
            <article key={role} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-[0_22px_55px_rgba(8,47,73,0.12)]">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Workspace</p>
              <h3 className="mt-3 text-xl font-black text-[#082F49]">{role}</h3>
              <p className="mt-4 text-sm leading-6 text-slate-600">
                Dedicated dashboard views with metrics, actions, and intelligence tuned to the role.
              </p>
            </article>
          ))}
        </div>
      </section>

      <section id="outcomes" className="border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[1fr_1.2fr] lg:items-center">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-[#B91C1C]">Operational proof</p>
            <h2 className="mt-4 text-3xl font-black text-[#082F49]">Professional, measurable, ready for growth.</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {metrics.map((metric) => (
              <div key={metric.label} className="rounded-2xl border border-slate-200 bg-[#F8FAFC] p-5">
                <p className="text-3xl font-black text-[#B91C1C]">{metric.value}</p>
                <p className="mt-2 text-sm font-semibold text-slate-600">{metric.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
