'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

type Prediction = {
  student: string;
  registration_number: string;
  batch: string;
  current_attendance: number;
  drop_probability: number;
  risk_level: string;
  reasons: string[];
  recommended_action: string;
};

type Forecast = {
  student: string;
  registration_number: string;
  batch: string;
  current_score: number;
  forecast_score: number;
  forecast_outcome: string;
  confidence: string;
  drivers: string[];
};

type ExecutiveReport = {
  title: string;
  narrative: string;
  health_score: number;
  recommendations: string[];
  performance_forecast_mix: Record<string, number>;
};

type AiOverview = {
  attendance_predictions: Prediction[];
  performance_forecasts: Forecast[];
  executive_report: ExecutiveReport;
  model_status?: {
    model_version: string;
    training_rows_available: number;
    can_retrain: boolean;
    artifacts: Record<string, { exists: boolean; path: string }>;
  };
  provider_status?: {
    provider: string;
    live_enabled: boolean;
  };
  example_prompts: string[];
};

type AssistantResult = {
  query: string;
  count: number;
  summary: string;
  results: { name: string; registration_number: string; attendance_rate: number; overall_score: number; risk_level: string }[];
};

type EvaluationResult = {
  title: string;
  score: number;
  max_score: number;
  grade: string;
  strengths: string[];
  improvements: string[];
  risk_flags: string[];
  feedback: string;
};

type AuthenticityResult = {
  originality_score: number;
  similarity_score: number;
  ai_generated_risk: number;
  code_quality_score: number;
  github_activity_score: number;
  risk_level: string;
  findings: string[];
  recommendations: string[];
  github_evidence: { status: string; signals: string[] };
};

type ReportResult = {
  status: string;
  output_format: string;
  file_url: string;
};

type RetrainResult = {
  status: string;
  training_rows?: number;
  source_students?: number;
  artifacts?: Record<string, { path: string; metrics: Record<string, number | boolean> }>;
  message?: string;
};

type NotificationItem = {
  id: number;
  recipient_type: string;
  recipient_id: string;
  channel: string;
  status: string;
  response_status: string;
  payload: { event_type?: string; student_name?: string; message?: string; severity?: string };
};

type NudgeResult = {
  status: string;
  detected_events: number;
  created_notifications: number;
  skipped_duplicates: number;
  auto_send: boolean;
};

function toneClass(tone: string) {
  if (['Critical', 'High', 'Needs Revision'].includes(tone)) return 'border-red-500/20 bg-red-500/10 text-red-200';
  if (['Medium', 'D'].includes(tone)) return 'border-amber-500/20 bg-amber-500/10 text-amber-200';
  return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-200';
}

function Badge({ children, tone }: { children: React.ReactNode; tone: string }) {
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${toneClass(tone)}`}>{children}</span>;
}

function Panel({ title, eyebrow, children }: { title: string; eyebrow?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-white/10 bg-[#111827] shadow-[0_18px_60px_rgba(0,0,0,0.22)]">
      <div className="border-b border-white/10 px-5 py-4">
        {eyebrow && <p className="text-[11px] font-medium uppercase tracking-widest text-[#B91C1C]">{eyebrow}</p>}
        <h2 className="mt-1 text-sm font-semibold text-white">{title}</h2>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

export default function AiPage() {
  const router = useRouter();
  const [overview, setOverview] = useState<AiOverview | null>(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('Show students with attendance below 70%.');
  const [assistant, setAssistant] = useState<AssistantResult | null>(null);
  const [title, setTitle] = useState('React Dashboard Sprint');
  const [submissionText, setSubmissionText] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [authenticity, setAuthenticity] = useState<AuthenticityResult | null>(null);
  const [report, setReport] = useState<ReportResult | null>(null);
  const [retrainResult, setRetrainResult] = useState<RetrainResult | null>(null);
  const [nudgeResult, setNudgeResult] = useState<NudgeResult | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loadingAssistant, setLoadingAssistant] = useState(false);
  const [loadingEvaluation, setLoadingEvaluation] = useState(false);
  const [loadingAuthenticity, setLoadingAuthenticity] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [loadingRetrain, setLoadingRetrain] = useState(false);
  const [loadingNudges, setLoadingNudges] = useState(false);

  const loadNotifications = useCallback(async () => {
    try {
      const response = await fetch('/api/notifications');
      const data = await response.json();
      if (response.ok) setNotifications(Array.isArray(data.items) ? data.items : []);
    } catch {
      setNotifications([]);
    }
  }, []);

  useEffect(() => {
    fetch('/api/ai')
      .then(async (response) => {
        const data = await response.json();
        if (response.status === 401) {
          router.push('/login?next=/ai');
          return null;
        }
        if (!response.ok) throw new Error(data.detail || 'Unable to load AI module');
        return data as AiOverview;
      })
      .then((data) => {
        if (data) setOverview(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load AI module'));
    loadNotifications();
  }, [loadNotifications, router]);

  const askAssistant = async (prompt = query) => {
    setLoadingAssistant(true);
    setError('');
    try {
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'assistant', query: prompt }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Assistant query failed');
      setAssistant(data);
      setQuery(prompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assistant query failed');
    } finally {
      setLoadingAssistant(false);
    }
  };

  const evaluateSubmission = async () => {
    setLoadingEvaluation(true);
    setError('');
    try {
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'evaluate', title, submission_text: submissionText, max_score: 100 }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Assignment evaluation failed');
      setEvaluation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assignment evaluation failed');
    } finally {
      setLoadingEvaluation(false);
    }
  };

  const checkAuthenticity = async () => {
    setLoadingAuthenticity(true);
    setError('');
    try {
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'authenticity', title, submission_text: submissionText, github_url: githubUrl }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Authenticity check failed');
      setAuthenticity(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authenticity check failed');
    } finally {
      setLoadingAuthenticity(false);
    }
  };

  const generateReport = async () => {
    setLoadingReport(true);
    setError('');
    try {
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'report', report_type: 'Weekly executive', output_format: 'pdf' }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Report generation failed');
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report generation failed');
    } finally {
      setLoadingReport(false);
    }
  };

  const retrainModels = async () => {
    setLoadingRetrain(true);
    setError('');
    try {
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'retrain' }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Model retraining failed');
      setRetrainResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Model retraining failed');
    } finally {
      setLoadingRetrain(false);
    }
  };

  const runNudges = async () => {
    setLoadingNudges(true);
    setError('');
    try {
      const response = await fetch('/api/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_send: false }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Nudge generation failed');
      setNudgeResult(data);
      await loadNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nudge generation failed');
    } finally {
      setLoadingNudges(false);
    }
  };

  const markReplied = async (notificationId: number) => {
    setError('');
    try {
      const response = await fetch('/api/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'response', notification_id: notificationId, response_status: 'replied', notes: 'Response tracked from AI command center.' }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Response tracking failed');
      await loadNotifications();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Response tracking failed');
    }
  };

  return (
    <main className="min-h-screen bg-[#0B1020] px-4 py-6 text-slate-200 sm:px-6">
      <div className="mx-auto max-w-7xl space-y-5">
        <section className="rounded-xl border border-white/10 bg-[linear-gradient(135deg,#111827,#1F2937_55%,#7F1D1D)] p-5 shadow-[0_18px_70px_rgba(0,0,0,0.35)]">
          <p className="text-[11px] font-medium uppercase tracking-widest text-red-200">TFI AI Intelligence</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Prediction, forecasting, mentor assistant, evaluation, and reports</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-200">
            Operational AI tools for attendance risk, final-outcome forecasting, assignment review, and executive summaries.
          </p>
        </section>

        {error && <section className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">{error}</section>}

        <section className="grid gap-5 xl:grid-cols-3">
          <Panel title="Live AI provider" eyebrow="OpenAI / Gemini">
            <div className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
              <p className="text-2xl font-semibold text-white">{overview?.provider_status?.provider ?? 'local'}</p>
              <p className="mt-2 text-sm text-slate-400">{overview?.provider_status?.live_enabled ? 'Live provider calls enabled' : 'Local fallback active'}</p>
            </div>
          </Panel>

          <Panel title="ML model status" eyebrow="Scikit-learn">
            <div className="space-y-3">
              <div className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                <p className="text-sm text-slate-400">Training rows</p>
                <p className="mt-1 text-2xl font-semibold text-white">{overview?.model_status?.training_rows_available ?? 0}</p>
              </div>
              <button
                onClick={retrainModels}
                disabled={loadingRetrain}
                className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingRetrain ? 'Retraining...' : 'Retrain models'}
              </button>
              {retrainResult && <p className="text-sm text-slate-400">{retrainResult.status === 'completed' ? `Trained ${retrainResult.training_rows} rows.` : retrainResult.message}</p>}
            </div>
          </Panel>

          <Panel title="AI report export" eyebrow="PDF / HTML / Markdown">
            <div className="space-y-3">
              <button
                onClick={generateReport}
                disabled={loadingReport}
                className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingReport ? 'Generating...' : 'Generate PDF report'}
              </button>
              {report && (
                <div className="rounded-lg border border-white/10 bg-[#0B1020] p-3 text-sm text-slate-300">
                  {report.output_format.toUpperCase()} ready at {report.file_url}
                </div>
              )}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
          <Panel title="Auto nudges" eyebrow="WhatsApp / Email">
            <div className="space-y-3">
              <button
                onClick={runNudges}
                disabled={loadingNudges}
                className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingNudges ? 'Scanning...' : 'Run missed-attendance and assignment nudges'}
              </button>
              {nudgeResult && (
                <div className="rounded-lg border border-white/10 bg-[#0B1020] p-3 text-sm text-slate-300">
                  {nudgeResult.detected_events} events, {nudgeResult.created_notifications} notifications, {nudgeResult.skipped_duplicates} duplicates skipped.
                </div>
              )}
            </div>
          </Panel>

          <Panel title="Nudge response tracking" eyebrow="Latest queue">
            <div className="grid gap-3">
              {notifications.length === 0 && <p className="text-sm text-slate-500">No nudges queued yet.</p>}
              {notifications.slice(0, 5).map((item) => (
                <div key={item.id} className="grid gap-3 rounded-lg border border-white/10 bg-[#0B1020] p-4 md:grid-cols-[1fr_auto] md:items-center">
                  <div>
                    <p className="text-sm font-medium text-white">{item.payload.student_name ?? item.recipient_id}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.channel} to {item.recipient_type} - {item.status} - response {item.response_status}</p>
                    <p className="mt-2 line-clamp-2 text-sm text-slate-400">{item.payload.message}</p>
                  </div>
                  <button
                    onClick={() => markReplied(item.id)}
                    className="h-9 rounded-lg border border-white/10 px-3 text-xs font-semibold text-slate-200 transition hover:border-[#B91C1C]"
                  >
                    Mark replied
                  </button>
                </div>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
          <Panel title="AI executive report" eyebrow="Auto generated">
            {!overview ? (
              <div className="h-36 animate-pulse rounded-lg bg-[#0B1020]" />
            ) : (
              <div>
                <div className="rounded-lg border border-white/10 bg-[#0B1020] p-5">
                  <p className="text-5xl font-semibold text-white">{overview.executive_report.health_score}</p>
                  <p className="mt-2 text-sm text-slate-400">Internship health score</p>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-300">{overview.executive_report.narrative}</p>
                <div className="mt-4 grid gap-2">
                  {overview.executive_report.recommendations.map((item) => (
                    <div key={item} className="rounded-lg border border-white/10 bg-[#0B1020] p-3 text-sm text-slate-300">{item}</div>
                  ))}
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Performance forecast mix" eyebrow="Outcome prediction">
            <div className="grid gap-3">
              {overview && Object.entries(overview.executive_report.performance_forecast_mix).length === 0 && (
                <p className="text-sm text-slate-500">No forecast data available yet.</p>
              )}
              {overview && Object.entries(overview.executive_report.performance_forecast_mix).map(([name, count]) => (
                <div key={name} className="flex items-center justify-between rounded-lg border border-white/10 bg-[#0B1020] p-4">
                  <span className="text-sm text-slate-300">{name}</span>
                  <span className="text-lg font-semibold text-white">{count}</span>
                </div>
              ))}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 xl:grid-cols-2">
          <Panel title="Attendance drop prediction" eyebrow="Before it happens">
            <div className="space-y-3">
              {(overview?.attendance_predictions ?? []).map((item) => (
                <article key={item.registration_number} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{item.student}</p>
                      <p className="mt-1 text-xs text-slate-500">{item.batch} - {item.current_attendance}% attendance</p>
                    </div>
                    <Badge tone={item.risk_level}>{item.drop_probability}%</Badge>
                  </div>
                  <p className="mt-3 text-sm text-slate-400">{item.recommended_action}</p>
                </article>
              ))}
              {overview && overview.attendance_predictions.length === 0 && <p className="text-sm text-slate-500">No students available for prediction yet.</p>}
            </div>
          </Panel>

          <Panel title="Performance forecasting" eyebrow="Final outcome">
            <div className="space-y-3">
              {(overview?.performance_forecasts ?? []).map((item) => (
                <article key={item.registration_number} className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{item.student}</p>
                      <p className="mt-1 text-xs text-slate-500">{item.current_score} current to {item.forecast_score} forecast</p>
                    </div>
                    <Badge tone={item.confidence}>{item.confidence}</Badge>
                  </div>
                  <p className="mt-3 text-sm text-slate-400">{item.forecast_outcome}</p>
                </article>
              ))}
              {overview && overview.performance_forecasts.length === 0 && <p className="text-sm text-slate-500">No students available for forecasting yet.</p>}
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
          <Panel title="AI mentor assistant" eyebrow="Ask operational questions">
            <div className="space-y-3">
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="min-h-28 w-full rounded-lg border border-white/10 bg-[#0B1020] p-3 text-sm text-white outline-none focus:border-[#B91C1C]"
              />
              <button
                onClick={() => askAssistant()}
                disabled={loadingAssistant}
                className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingAssistant ? 'Asking...' : 'Ask assistant'}
              </button>
              <div className="flex flex-wrap gap-2">
                {(overview?.example_prompts ?? []).map((prompt) => (
                  <button key={prompt} onClick={() => askAssistant(prompt)} className="rounded-lg border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:border-[#B91C1C] hover:text-white">
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </Panel>

          <Panel title="Assistant results" eyebrow="Mentor view">
            {!assistant ? (
              <p className="text-sm text-slate-500">Ask a question to see matching students.</p>
            ) : (
              <div>
                <p className="text-sm text-slate-300">{assistant.summary}</p>
                <div className="mt-4 grid gap-3">
                  {assistant.results.slice(0, 6).map((item) => (
                    <div key={item.registration_number} className="grid gap-3 rounded-lg border border-white/10 bg-[#0B1020] p-4 sm:grid-cols-[1fr_auto] sm:items-center">
                      <div>
                        <p className="font-medium text-white">{item.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{item.registration_number}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge tone={item.risk_level}>{item.risk_level}</Badge>
                        <span className="rounded-md bg-white/5 px-2 py-1 text-xs font-semibold text-slate-300">{item.attendance_rate}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Panel>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <Panel title="AI assignment evaluation" eyebrow="Pre-score submissions">
            <div className="space-y-3">
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm text-white outline-none focus:border-[#B91C1C]"
              />
              <textarea
                value={submissionText}
                onChange={(event) => setSubmissionText(event.target.value)}
                placeholder="Paste student assignment text here..."
                className="min-h-44 w-full rounded-lg border border-white/10 bg-[#0B1020] p-3 text-sm text-white outline-none focus:border-[#B91C1C]"
              />
              <input
                value={githubUrl}
                onChange={(event) => setGithubUrl(event.target.value)}
                placeholder="GitHub repository URL optional"
                className="h-10 w-full rounded-lg border border-white/10 bg-[#0B1020] px-3 text-sm text-white outline-none focus:border-[#B91C1C]"
              />
              <button
                onClick={evaluateSubmission}
                disabled={loadingEvaluation || !submissionText.trim()}
                className="h-10 rounded-lg bg-[#B91C1C] px-4 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingEvaluation ? 'Evaluating...' : 'Evaluate submission'}
              </button>
              <button
                onClick={checkAuthenticity}
                disabled={loadingAuthenticity || !submissionText.trim()}
                className="h-10 rounded-lg border border-white/10 px-4 text-sm font-semibold text-white transition hover:border-[#B91C1C] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingAuthenticity ? 'Checking...' : 'Check authenticity'}
              </button>
            </div>
          </Panel>

          <Panel title="Evaluation output" eyebrow="Mentor approval support">
            {!evaluation ? (
              <p className="text-sm text-slate-500">Evaluation results will appear here.</p>
            ) : (
              <div className="space-y-4">
                <div className="flex items-end justify-between rounded-lg border border-white/10 bg-[#0B1020] p-5">
                  <div>
                    <p className="text-4xl font-semibold text-white">{evaluation.score}/{evaluation.max_score}</p>
                    <p className="mt-1 text-sm text-slate-400">{evaluation.feedback}</p>
                  </div>
                  <Badge tone={evaluation.grade}>{evaluation.grade}</Badge>
                </div>
                <ResultList title="Strengths" items={evaluation.strengths} />
                <ResultList title="Improvements" items={evaluation.improvements} />
                {evaluation.risk_flags.length > 0 && <ResultList title="Risk flags" items={evaluation.risk_flags} />}
              </div>
            )}
          </Panel>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
          <Panel title="Project authenticity" eyebrow="Similarity / AI risk / GitHub">
            {!authenticity ? (
              <p className="text-sm text-slate-500">Run an authenticity check from the assignment panel.</p>
            ) : (
              <div className="space-y-4">
                <div className="flex items-end justify-between rounded-lg border border-white/10 bg-[#0B1020] p-5">
                  <div>
                    <p className="text-4xl font-semibold text-white">{authenticity.originality_score}%</p>
                    <p className="mt-1 text-sm text-slate-400">Originality score</p>
                  </div>
                  <Badge tone={authenticity.risk_level}>{authenticity.risk_level}</Badge>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <ScoreTile label="Similarity" value={authenticity.similarity_score} />
                  <ScoreTile label="AI risk" value={authenticity.ai_generated_risk} />
                  <ScoreTile label="Code quality" value={authenticity.code_quality_score} />
                  <ScoreTile label="GitHub activity" value={authenticity.github_activity_score} />
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Authenticity findings" eyebrow="Mentor review">
            {!authenticity ? (
              <p className="text-sm text-slate-500">Findings and recommendations will appear here.</p>
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                <ResultList title="Findings" items={authenticity.findings} />
                <ResultList title="Recommendations" items={authenticity.recommendations} />
              </div>
            )}
          </Panel>
        </section>
      </div>
    </main>
  );
}

function ScoreTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#0B1020] p-4">
      <p className="text-xs uppercase tracking-widest text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}%</p>
    </div>
  );
}

function ResultList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-slate-500">{title}</p>
      <div className="mt-2 grid gap-2">
        {items.map((item) => (
          <div key={item} className="rounded-lg border border-white/10 bg-[#0B1020] p-3 text-sm text-slate-300">{item}</div>
        ))}
      </div>
    </div>
  );
}
