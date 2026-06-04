'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

type ReportsResponse = {
  certificate_eligible: number;
  total_students: number;
  defaulter_count: number;
  weekly_attendance: { name: string; value: number }[];
  report_status: string;
  exports: string[];
  ai_insights: { title: string; body: string; severity: string }[];
};

const reportTypes = ['Daily operations', 'Weekly executive', 'Mentor performance', 'Batch comparison', 'Certificate eligibility'];

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<ReportsResponse | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/reports')
      .then(async (res) => {
        const data = await res.json();
        if (res.status === 401) {
          router.push('/login?next=/reports');
          return null;
        }
        if (!res.ok) throw new Error(data.detail || 'Unable to load reports');
        return {
          certificate_eligible: Number(data.certificate_eligible ?? 0),
          total_students: Number(data.total_students ?? 0),
          defaulter_count: Number(data.defaulter_count ?? 0),
          weekly_attendance: Array.isArray(data.weekly_attendance) ? data.weekly_attendance : [],
          report_status: String(data.report_status ?? 'Unavailable'),
          exports: Array.isArray(data.exports) ? data.exports : [],
          ai_insights: Array.isArray(data.ai_insights) ? data.ai_insights : [],
        } satisfies ReportsResponse;
      })
      .then((data) => {
        if (data) setReports(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load reports'));
  }, [router]);

  const weeklyAttendance = reports?.weekly_attendance ?? [];
  const insights = reports?.ai_insights ?? [];
  const exportTypes = reports?.exports.length ? reports.exports : ['PDF', 'CSV', 'Excel'];

  return (
    <main className="min-h-screen bg-[#0B1020] px-4 py-6 text-slate-200 sm:px-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <section className="glass-panel p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-widest text-[#3B82F6]">Executive Reporting</p>
              <h1 className="mt-2 text-2xl font-semibold text-white">Report center</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-400">
                Generate board-ready internship reports with eligibility, risk, attendance, assignment, and mentor performance context.
              </p>
            </div>
            <button className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700">Generate report</button>
          </div>
        </section>

        {error && (
          <section className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
            {error}
          </section>
        )}

        <section className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="glass-panel p-5">
            <h2 className="text-sm font-semibold text-white">Report builder</h2>
            <div className="mt-4 space-y-3">
              {reportTypes.map((type) => (
                <button key={type} className="flex w-full items-center justify-between rounded-lg border border-white/10 bg-[#0B1020] px-4 py-3 text-left text-sm transition hover:border-[#3B82F6]">
                  <span className="text-white">{type}</span>
                  <span className="text-xs text-slate-500">PDF CSV Excel</span>
                </button>
              ))}
            </div>
          </div>

          <div className="table-shell">
            <div className="border-b border-white/10 px-5 py-4">
              <h2 className="text-sm font-semibold text-white">Current reporting snapshot</h2>
            </div>
            <div className="grid gap-4 p-5 md:grid-cols-3">
              <Snapshot label="Eligible" value={reports ? `${reports.certificate_eligible}` : '...'} />
              <Snapshot label="Tracked students" value={reports ? `${reports.total_students}` : '...'} />
              <Snapshot label="Intervention queue" value={reports ? `${reports.defaulter_count}` : '...'} danger />
            </div>
            <div className="border-t border-white/10 p-5">
              <p className="text-xs uppercase tracking-widest text-slate-500">Weekly attendance</p>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {weeklyAttendance.length === 0 && (
                  <div className="rounded-lg border border-white/10 bg-[#0B1020] p-4 text-sm text-slate-500">
                    No attendance trend data is available yet.
                  </div>
                )}
                {weeklyAttendance.map((item) => (
                  <div key={item.name} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                    <p className="text-xs text-slate-500">{item.name}</p>
                    <p className="mt-2 text-2xl font-semibold text-white">{item.value}%</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
          <div className="glass-panel p-5">
            <h2 className="text-sm font-semibold text-white">AI report insights</h2>
            <div className="mt-4 grid gap-3">
              {insights.length === 0 && <p className="text-sm text-slate-500">No report insights are available yet.</p>}
              {insights.map((insight) => (
                <div key={insight.title} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                  <p className="font-medium text-white">{insight.title}</p>
                  <p className="mt-1 text-sm text-slate-400">{insight.body}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-panel p-5">
            <h2 className="text-sm font-semibold text-white">Export readiness</h2>
            <div className="mt-4 space-y-3">
              {exportTypes.map((item) => (
                <div key={item} className="flex items-center justify-between rounded-lg border border-white/10 bg-[#0B1020] p-4">
                  <span className="text-sm text-white">{item}</span>
                  <span className="rounded-md bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-200">Ready</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function Snapshot({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${danger ? 'text-red-300' : 'text-white'}`}>{value}</p>
    </div>
  );
}
