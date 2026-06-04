'use client';

import { useState } from 'react';

interface RecordItem {
  student_name: string;
  registration_number: string;
  email: string;
  duration_minutes: number;
  attendance_percentage: number;
  attendance_status: string;
  late_joining: boolean;
  early_leaving: boolean;
  engagement_score: number;
}

const steps = ['Upload source file', 'Normalize participants', 'Validate attendance rules', 'Publish session history'];

export default function AttendancePage() {
  const [file, setFile] = useState<File | null>(null);
  const [batchName, setBatchName] = useState('');
  const [domain, setDomain] = useState('');
  const [sessionTitle, setSessionTitle] = useState('');
  const [platform, setPlatform] = useState('Zoom');
  const [sessionDate, setSessionDate] = useState(new Date().toISOString().slice(0, 10));
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [quality, setQuality] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUpload = async () => {
    if (!file) return;
    if (!batchName || !sessionTitle || !sessionDate) {
      setError('Batch name, session title, and session date are required before importing attendance.');
      return;
    }
    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('batch_name', batchName);
      formData.append('domain', domain || 'General');
      formData.append('session_title', sessionTitle);
      formData.append('platform', platform);
      formData.append('session_date', sessionDate);
      const response = await fetch('/api/attendance', { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed');
      setRecords(data.records.slice(0, 25));
      setSummary(data.summary);
      setQuality(data.quality ?? {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to import attendance file.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0B1020] px-4 py-6 text-slate-200 sm:px-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <section className="glass-panel p-5">
          <div className="flex flex-col gap-4">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-widest text-[#3B82F6]">Attendance Intelligence</p>
              <h1 className="mt-2 text-2xl font-semibold text-white">Session import and normalization</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-400">
                Convert Zoom, Google Meet, extension, and manual exports into consistent attendance, duration, late join, early leave, and engagement signals.
              </p>
            </div>
            <div className="grid gap-3 lg:grid-cols-5">
              <label className="block text-xs font-medium uppercase tracking-widest text-slate-500">
                Batch
                <input value={batchName} onChange={(event) => setBatchName(event.target.value)} className="mt-2 h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-[#3B82F6]" placeholder="AIML June" />
              </label>
              <label className="block text-xs font-medium uppercase tracking-widest text-slate-500">
                Domain
                <input value={domain} onChange={(event) => setDomain(event.target.value)} className="mt-2 h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-[#3B82F6]" placeholder="AIML" />
              </label>
              <label className="block text-xs font-medium uppercase tracking-widest text-slate-500">
                Session
                <input value={sessionTitle} onChange={(event) => setSessionTitle(event.target.value)} className="mt-2 h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-[#3B82F6]" placeholder="Model evaluation lab" />
              </label>
              <label className="block text-xs font-medium uppercase tracking-widest text-slate-500">
                Platform
                <select value={platform} onChange={(event) => setPlatform(event.target.value)} className="mt-2 h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-[#3B82F6]">
                  <option>Zoom</option>
                  <option>Google Meet</option>
                  <option>Microsoft Teams</option>
                  <option>Manual</option>
                </select>
              </label>
              <label className="block text-xs font-medium uppercase tracking-widest text-slate-500">
                Date
                <input type="date" value={sessionDate} onChange={(event) => setSessionDate(event.target.value)} className="mt-2 h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-[#3B82F6]" />
              </label>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <label className="flex h-10 cursor-pointer items-center justify-center rounded-lg border border-white/10 bg-[#111827] px-4 text-sm text-slate-300 transition hover:border-[#3B82F6]">
                {file ? file.name : 'Choose file'}
                <input type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              </label>
              <button
                onClick={handleUpload}
                disabled={!file || loading}
                className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? 'Importing...' : 'Import attendance'}
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-4">
          {steps.map((step, index) => (
            <div key={step} className="rounded-xl border border-white/10 bg-[#111827] p-4">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-blue-500/10 text-sm font-semibold text-blue-200">{index + 1}</span>
              <p className="mt-4 text-sm font-medium text-white">{step}</p>
            </div>
          ))}
        </section>

        {error && <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</div>}

        {Object.keys(summary).length > 0 && (
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Object.entries(summary).map(([label, value]) => (
              <div key={label} className="rounded-xl border border-white/10 bg-[#111827] p-4">
                <p className="text-xs uppercase tracking-widest text-slate-500">{label.replace(/_/g, ' ')}</p>
                <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
              </div>
            ))}
          </section>
        )}

        {Object.keys(quality).length > 0 && (
          <section className="rounded-xl border border-white/10 bg-[#111827] p-5">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-[11px] font-medium uppercase tracking-widest text-[#3B82F6]">Import quality</p>
                <h2 className="mt-1 text-sm font-semibold text-white">Operational confidence checks</h2>
              </div>
              <span className="rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-200">Validated</span>
            </div>
            <div className="grid gap-3 md:grid-cols-5">
              {Object.entries(quality).map(([label, value]) => (
                <div key={label} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                  <p className="text-xs text-slate-500">{label.replace(/_/g, ' ')}</p>
                  <p className="mt-2 text-xl font-semibold text-white">{value}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="table-shell">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="text-sm font-semibold text-white">Normalized attendance records</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[#1F2937] text-xs uppercase tracking-widest text-slate-400">
                <tr>
                  <th className="px-5 py-3">Student</th>
                  <th className="px-5 py-3">Email</th>
                  <th className="px-5 py-3">Duration</th>
                  <th className="px-5 py-3">Attendance</th>
                  <th className="px-5 py-3">Engagement</th>
                  <th className="px-5 py-3">Flags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-10 text-center text-slate-500">
                      Upload an attendance export to review normalized session records.
                    </td>
                  </tr>
                ) : (
                  records.map((row, index) => (
                    <tr key={`${row.email}-${index}`}>
                      <td className="px-5 py-4">
                        <p className="font-medium text-white">{row.student_name}</p>
                        <p className="text-xs text-slate-500">{row.registration_number}</p>
                      </td>
                      <td className="px-5 py-4 text-slate-400">{row.email}</td>
                      <td className="px-5 py-4">{row.duration_minutes.toFixed(0)} min</td>
                      <td className="px-5 py-4">{row.attendance_percentage}%</td>
                      <td className="px-5 py-4">{row.engagement_score}</td>
                      <td className="px-5 py-4 text-xs text-slate-400">
                        {row.attendance_status}
                        {row.late_joining ? ' - late' : ''}
                        {row.early_leaving ? ' - early' : ''}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
