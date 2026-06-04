'use client';

import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface DatasetItem {
  name: string;
  value: number;
}

interface AnalyticsChartsProps {
  attendanceTrend: DatasetItem[];
  completionTrend: DatasetItem[];
}

export function AnalyticsCharts({ attendanceTrend, completionTrend }: AnalyticsChartsProps) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <div className="rounded-xl border border-white/10 bg-[#111827] p-5 shadow-[0_18px_60px_rgba(0,0,0,0.24)]">
        <h2 className="text-base font-semibold text-white">Attendance trend</h2>
        <div className="mt-6 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={attendanceTrend} margin={{ top: 5, right: 18, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="#1F2937" />
              <XAxis dataKey="name" stroke="#9CA3AF" tickLine={false} axisLine={false} />
              <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#1F2937', color: '#E5E7EB' }} />
              <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="rounded-xl border border-white/10 bg-[#111827] p-5 shadow-[0_18px_60px_rgba(0,0,0,0.24)]">
        <h2 className="text-base font-semibold text-white">Assignment completion</h2>
        <div className="mt-6 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={completionTrend} margin={{ top: 5, right: 18, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="4 4" stroke="#1F2937" />
              <XAxis dataKey="name" stroke="#9CA3AF" tickLine={false} axisLine={false} />
              <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#1F2937', color: '#E5E7EB' }} />
              <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
