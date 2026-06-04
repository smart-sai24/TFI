'use client';

interface StatCardProps {
  label: string;
  value: string | number;
  tone?: 'red' | 'white';
}

export function StatCard({ label, value, tone = 'white' }: StatCardProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#111827] p-5 shadow-[0_18px_60px_rgba(0,0,0,0.24)]">
      <p className="text-xs font-medium uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`mt-3 text-3xl font-semibold ${tone === 'red' ? 'text-red-300' : 'text-white'}`}>{value}</p>
    </div>
  );
}
