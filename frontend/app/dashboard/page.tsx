'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { useAuthStore, type UserRole } from '../../store/useAuthStore';
import type { DashboardSummary, StudentRow } from '../../types/dashboard';

function toneClass(tone: string) {
  if (['High', 'critical', 'Danger', 'Medium'].includes(tone)) return 'border-red-500/20 bg-red-500/10 text-red-200';
  if (['Warning', 'warning'].includes(tone)) return 'border-amber-500/20 bg-amber-500/10 text-amber-200';
  if (['Eligible', 'Healthy', 'Success', 'positive', 'Live'].includes(tone)) return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-200';
  return 'border-blue-500/20 bg-blue-500/10 text-blue-200';
}

function Badge({ children, tone = 'Info' }: { children: React.ReactNode; tone?: string }) {
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium ${toneClass(tone)}`}>{children}</span>;
}

function Panel({ title, eyebrow, children, action }: { title: string; eyebrow?: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-white/10 bg-[#111827] shadow-[0_18px_60px_rgba(0,0,0,0.22)]">
      <div className="flex items-start justify-between gap-4 border-b border-white/10 px-5 py-4">
        <div>
          {eyebrow && <p className="text-[11px] font-medium uppercase tracking-widest text-slate-500">{eyebrow}</p>}
          <h2 className="mt-1 text-sm font-semibold text-slate-100">{title}</h2>
        </div>
        {action}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function WorkspaceHeader({ summary, role }: { summary: DashboardSummary; role: UserRole }) {
  return (
    <section className="rounded-xl border border-white/10 bg-[#111827] p-5 shadow-[0_18px_60px_rgba(0,0,0,0.22)]">
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-widest text-[#3B82F6]">{role} workspace</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">{summary.role_center.name}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{summary.role_center.question}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            <Badge tone="Healthy">Health {summary.internship_health_score}/100</Badge>
            <Badge tone="Warning">{summary.at_risk_students} intervention records</Badge>
            <Badge tone="Info">{summary.active_sessions} sessions active</Badge>
          </div>
        </div>
        <div className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
          <p className="text-xs uppercase tracking-widest text-slate-500">Primary operating loop</p>
          <p className="mt-2 text-lg font-semibold text-white">{summary.role_center.primary_action}</p>
          <p className="mt-2 text-sm text-slate-400">Prioritized by attendance, assignment completion, engagement, and risk movement.</p>
        </div>
      </div>
    </section>
  );
}

function ProgressRow({ label, value, tone = '#3B82F6' }: { label: string; value: number; tone?: string }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-semibold text-white">{value}%</span>
      </div>
      <div className="h-2 rounded-full bg-[#1F2937]">
        <div className="h-2 rounded-full" style={{ width: `${Math.min(Math.max(value, 4), 100)}%`, backgroundColor: tone }} />
      </div>
    </div>
  );
}

function SignalList({ items }: { items: { title: string; body: string; tone?: string }[] }) {
  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <article key={`${item.title}-${item.body}-${index}`} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-medium text-white">{item.title}</p>
            {item.tone && <Badge tone={item.tone}>{item.tone}</Badge>}
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-400">{item.body}</p>
        </article>
      ))}
    </div>
  );
}

function EnterpriseStudentTable({ rows }: { rows: StudentRow[] }) {
  const [query, setQuery] = useState('');
  const [sortKey, setSortKey] = useState<keyof StudentRow>('overall_score');
  const [descending, setDescending] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 8;

  const filteredRows = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    const result = rows.filter((row) => `${row.name} ${row.registration_number} ${row.batch} ${row.domain} ${row.risk_level}`.toLowerCase().includes(normalized));
    return result.sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];
      if (typeof aValue === 'number' && typeof bValue === 'number') return descending ? bValue - aValue : aValue - bValue;
      return descending ? String(bValue).localeCompare(String(aValue)) : String(aValue).localeCompare(String(bValue));
    });
  }, [descending, query, rows, sortKey]);

  useEffect(() => {
    setPage(1);
  }, [query, rows, sortKey, descending]);

  const totalPages = Math.max(Math.ceil(filteredRows.length / pageSize), 1);
  const currentPage = Math.min(page, totalPages);
  const pageRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleExport = () => {
    const headers = ['Student', 'Registration', 'Batch', 'Domain', 'Attendance', 'Assignments', 'Score', 'Risk', 'Certificate'];
    const csvRows = filteredRows.map((row) =>
      [
        row.name,
        row.registration_number,
        row.batch,
        row.domain,
        row.attendance_rate,
        row.assignment_completion,
        row.overall_score,
        row.risk_level,
        row.certificate_status,
      ]
        .map((value) => `"${String(value).replace(/"/g, '""')}"`)
        .join(','),
    );
    const blob = new Blob([[headers.join(','), ...csvRows].join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'tfi-student-signal-view.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const columns: { key: keyof StudentRow; label: string }[] = [
    { key: 'name', label: 'Student' },
    { key: 'batch', label: 'Batch' },
    { key: 'attendance_rate', label: 'Attendance' },
    { key: 'assignment_completion', label: 'Assignments' },
    { key: 'overall_score', label: 'Score' },
    { key: 'risk_level', label: 'Risk' },
  ];

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search students, batches, risk..."
          className="h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm text-white outline-none focus:border-[#3B82F6] sm:max-w-sm"
        />
        <button onClick={handleExport} className="h-10 rounded-lg border border-white/10 px-3 text-sm font-medium text-slate-300 transition hover:border-[#3B82F6] hover:text-white">Export view</button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 bg-[#1F2937] text-xs uppercase tracking-widest text-slate-400">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className="px-4 py-3">
                  <button
                    onClick={() => {
                      setDescending(sortKey === column.key ? !descending : true);
                      setSortKey(column.key);
                    }}
                    className="font-medium transition hover:text-white"
                  >
                    {column.label}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {pageRows.map((row) => (
              <tr key={row.registration_number} className="bg-[#111827] transition hover:bg-[#162033]">
                <td className="px-4 py-3">
                  <p className="font-medium text-white">{row.name}</p>
                  <p className="text-xs text-slate-500">{row.registration_number}</p>
                </td>
                <td className="px-4 py-3 text-slate-300">{row.batch}</td>
                <td className="px-4 py-3 text-slate-300">{row.attendance_rate}%</td>
                <td className="px-4 py-3 text-slate-300">{row.assignment_completion}%</td>
                <td className="px-4 py-3 font-semibold text-white">{row.overall_score}</td>
                <td className="px-4 py-3"><Badge tone={row.risk_level}>{row.risk_level}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex flex-col gap-3 border-t border-white/10 pt-4 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
        <p>
          Showing {filteredRows.length ? (currentPage - 1) * pageSize + 1 : 0}-{Math.min(currentPage * pageSize, filteredRows.length)} of {filteredRows.length}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((value) => Math.max(value - 1, 1))}
            disabled={currentPage === 1}
            className="h-9 rounded-lg border border-white/10 px-3 font-medium text-slate-300 transition hover:border-[#3B82F6] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Prev
          </button>
          <span className="grid h-9 min-w-16 place-items-center rounded-lg border border-white/10 bg-[#0B1020] px-3 text-xs font-semibold text-white">
            {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => setPage((value) => Math.min(value + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="h-9 rounded-lg border border-white/10 px-3 font-medium text-slate-300 transition hover:border-[#3B82F6] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

function DirectorWorkspace({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="space-y-5">
      <WorkspaceHeader summary={summary} role="Director" />
      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.35fr_0.85fr]">
        <Panel title="Internship health score" eyebrow="Executive signal">
          <div className="rounded-xl border border-white/10 bg-[#0B1020] p-6 text-center">
            <p className="text-6xl font-semibold text-white">{summary.internship_health_score}</p>
            <p className="mt-2 text-sm text-slate-400">Excellent operating range</p>
          </div>
          <div className="mt-5 space-y-4">
            <ProgressRow label="Attendance" value={summary.attendance_rate} />
            <ProgressRow label="Assignment completion" value={summary.assignment_completion} tone="#22C55E" />
            <ProgressRow label="Engagement quality" value={summary.engagement_score} tone="#F59E0B" />
          </div>
        </Panel>
        <Panel title="Executive decision brief" eyebrow="AI operating narrative">
          <SignalList items={summary.ai_insights.map((insight) => ({ title: insight.title, body: insight.body, tone: insight.severity }))} />
        </Panel>
        <Panel title="Certificate forecast" eyebrow="Readiness">
          <div className="space-y-4">
            {summary.certificate_forecast.map((item) => (
              <ProgressRow key={item.status} label={`${item.status} (${item.count})`} value={Math.min(item.count * 16, 100)} tone={item.color} />
            ))}
          </div>
        </Panel>
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <Panel title="Risk distribution by batch" eyebrow="Intervention planning">
          <div className="grid gap-3 md:grid-cols-2">
            {summary.risk_heatmap.map((item) => (
              <div key={item.batch} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                <p className="text-sm font-medium text-white">{item.batch}</p>
                <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                  <span className="rounded-md bg-red-500/10 p-2 text-red-200">{item.high} high</span>
                  <span className="rounded-md bg-amber-500/10 p-2 text-amber-200">{item.medium} medium</span>
                  <span className="rounded-md bg-emerald-500/10 p-2 text-emerald-200">{item.low} low</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Operations activity" eyebrow="Recent intelligence">
          <SignalList items={summary.activity_feed.map((item) => ({ title: item.action, body: item.actor }))} />
        </Panel>
      </div>
      <Panel title="Enterprise student signal table" eyebrow="Sortable operational view">
        <EnterpriseStudentTable rows={[...summary.risk_students, ...summary.top_performers]} />
      </Panel>
    </div>
  );
}

function HostWorkspace({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="space-y-5">
      <WorkspaceHeader summary={summary} role="Host" />
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <Panel title="Live session control" eyebrow="Today">
          <div className="space-y-3">
            {summary.session_timeline.map((session) => (
              <div key={session.title} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{session.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{session.batch} hosted by {session.host}</p>
                  </div>
                  <Badge tone={session.status}>{session.status}</Badge>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-slate-300">
                  <span>{session.attendance_rate}% present</span>
                  <span>{session.late_joiners} late</span>
                  <span>{session.early_leavers} early</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Import quality loop" eyebrow="Attendance center">
          <SignalList
            items={[
              { title: 'Normalize identities', body: 'Participant email, registration number, and duplicate joins are reconciled before publish.', tone: 'Healthy' },
              { title: 'Duration guardrails', body: 'Required minutes and early-leave thresholds are centralized in backend configuration.', tone: 'Info' },
              { title: 'Upload controls', body: 'File type and size limits are enforced before parsing.', tone: 'Success' },
            ]}
          />
        </Panel>
        <Panel title="Exception queues" eyebrow="Follow up">
          <SignalList items={summary.attendance_alerts.map((alert) => ({ title: alert.title, body: alert.body, tone: alert.severity }))} />
        </Panel>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel title="Late joiners" eyebrow="Action required">
          <SignalList items={summary.late_joiners.map((item) => ({ title: item.name, body: `${item.batch} - ${item.delay_minutes} minutes late in ${item.session}`, tone: 'Warning' }))} />
        </Panel>
        <Panel title="Early leavers" eyebrow="Session integrity">
          <SignalList items={summary.early_leavers.map((item) => ({ title: item.name, body: `${item.batch} - left ${item.left_minutes_early} minutes early from ${item.session}`, tone: 'Medium' }))} />
        </Panel>
      </div>
    </div>
  );
}

function MentorWorkspace({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="space-y-5">
      <WorkspaceHeader summary={summary} role="Mentor" />
      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <Panel title="Students needing attention" eyebrow="Coaching queue">
          <EnterpriseStudentTable rows={summary.coaching_queue} />
        </Panel>
        <Panel title="Mentor playbook" eyebrow="AI recommendations">
          <SignalList items={summary.coaching_insights.map((insight) => ({ title: insight.title, body: insight.body, tone: 'Info' }))} />
        </Panel>
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        {summary.assignment_reviews.map((assignment) => (
          <Panel key={assignment.title} title={assignment.title} eyebrow={assignment.batch}>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-4xl font-semibold text-white">{assignment.pending_reviews}</p>
                <p className="mt-1 text-sm text-slate-400">reviews pending</p>
              </div>
              <Badge tone="Warning">{assignment.late_submissions} late</Badge>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}

function AdminWorkspace({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="space-y-5">
      <WorkspaceHeader summary={summary} role="Admin" />
      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr_0.85fr]">
        <Panel title="API reliability" eyebrow="System center">
          <div className="grid gap-3">
            {summary.api_metrics.map((metric) => (
              <div key={metric.name} className="flex items-center justify-between rounded-lg border border-white/10 bg-[#0B1020] p-4">
                <span className="text-sm text-slate-300">{metric.name}</span>
                <span className="font-semibold text-white">{metric.value}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Security event stream" eyebrow="Governance">
          <SignalList items={summary.security_events.map((event) => ({ title: event.event, body: `${event.service} - ${event.timestamp}`, tone: event.severity }))} />
        </Panel>
        <Panel title="RBAC readiness" eyebrow="Controls">
          <SignalList
            items={[
              { title: 'JWT auth context', body: 'Backend routes now evaluate token or demo-mode role headers through a shared dependency.', tone: 'Success' },
              { title: 'Permission checks', body: 'Dashboard, attendance, reports, and intelligence endpoints enforce role permissions.', tone: 'Healthy' },
              { title: 'Production switch', body: 'Disable demo mode and rotate SECRET_KEY before deployment.', tone: 'Warning' },
            ]}
          />
        </Panel>
      </div>
      <Panel title="Audit stream" eyebrow="Operational history">
        <SignalList items={summary.activity_feed.map((item) => ({ title: item.action, body: `${item.actor} - ${item.timestamp}` }))} />
      </Panel>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState('');
  const user = useAuthStore((state) => state.user);
  const activeRole = user?.role ?? 'Director';

  useEffect(() => {
    setSummary(null);
    fetch(`/api/dashboard?role=${encodeURIComponent(activeRole)}`)
      .then((res) => {
        if (res.status === 401) {
          router.replace('/login?next=/dashboard');
          return null;
        }
        if (!res.ok) throw new Error('Unable to load dashboard');
        return res.json();
      })
      .then((data) => {
        if (data) setSummary(data);
      })
      .catch(() => setError('Command Center intelligence is temporarily unavailable.'));
  }, [activeRole, router]);

  if (error) {
    return (
      <main className="min-h-screen bg-[#0B1020] px-4 py-6 sm:px-6">
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>
      </main>
    );
  }

  if (!summary) {
    return (
      <main className="min-h-screen bg-[#0B1020] px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-7xl space-y-5">
          <div className="h-40 animate-pulse rounded-xl bg-[#111827]" />
          <div className="grid gap-5 xl:grid-cols-3">
            <div className="h-96 animate-pulse rounded-xl bg-[#111827]" />
            <div className="h-96 animate-pulse rounded-xl bg-[#111827]" />
            <div className="h-96 animate-pulse rounded-xl bg-[#111827]" />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0B1020] px-4 py-6 text-slate-200 sm:px-6">
      <div className="mx-auto max-w-7xl">
        {activeRole === 'Director' && <DirectorWorkspace summary={summary} />}
        {activeRole === 'Host' && <HostWorkspace summary={summary} />}
        {activeRole === 'Mentor' && <MentorWorkspace summary={summary} />}
        {activeRole === 'Admin' && <AdminWorkspace summary={summary} />}
      </div>
    </main>
  );
}
