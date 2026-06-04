'use client';

const lanes = [
  {
    title: 'Needs review',
    count: 38,
    items: [
      { title: 'Attendance Analytics Case Study', batch: 'Data Science June', meta: '18 submissions' },
      { title: 'React Dashboard Sprint', batch: 'Full Stack June', meta: '11 submissions' },
    ],
  },
  {
    title: 'At risk',
    count: 12,
    items: [
      { title: 'Risk Detection Notebook', batch: 'AIML June', meta: '2 missing, 2 late' },
      { title: 'Threat Modeling Brief', batch: 'Cyber Security June', meta: '4 missing' },
    ],
  },
  {
    title: 'Ready to publish',
    count: 24,
    items: [
      { title: 'Weekly Reflection Report', batch: 'All batches', meta: 'Feedback prepared' },
      { title: 'Certificate Eligibility Audit', batch: 'Full Stack June', meta: 'Scores finalized' },
    ],
  },
];

export default function AssignmentsPage() {
  return (
    <main className="min-h-screen bg-[#0B1020] px-4 py-6 text-slate-200 sm:px-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <section className="glass-panel p-5">
          <p className="text-[11px] font-medium uppercase tracking-widest text-[#3B82F6]">Assignment Intelligence</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Review pipeline and intervention planning</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">
            Track created, submitted, missing, rejected, late, and resubmitted work with mentor-focused review queues.
          </p>
        </section>

        <section className="grid gap-5 xl:grid-cols-3">
          {lanes.map((lane) => (
            <div key={lane.title} className="rounded-xl border border-white/10 bg-[#111827]">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <h2 className="text-sm font-semibold text-white">{lane.title}</h2>
                <span className="rounded-md bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-200">{lane.count}</span>
              </div>
              <div className="space-y-3 p-4">
                {lane.items.map((item) => (
                  <article key={item.title} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                    <p className="text-sm font-medium text-white">{item.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.batch}</p>
                    <p className="mt-4 text-xs text-slate-400">{item.meta}</p>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </section>

        <section className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
          <div className="glass-panel p-5">
            <h2 className="text-sm font-semibold text-white">Evaluation rubric</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {['Code quality', 'Documentation', 'Naming standards', 'Complexity', 'Best practices', 'Resubmission quality'].map((item) => (
                <div key={item} className="rounded-lg border border-white/10 bg-[#0B1020] p-4 text-sm text-slate-300">
                  {item}
                </div>
              ))}
            </div>
          </div>
          <div className="glass-panel p-5">
            <h2 className="text-sm font-semibold text-white">Mentor action summary</h2>
            <div className="mt-4 space-y-3 text-sm text-slate-400">
              <p>38 submissions are waiting for review across three active assignments.</p>
              <p>12 students need intervention before certificate eligibility is affected.</p>
              <p>AI evaluation can pre-score programming work before mentor approval.</p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
