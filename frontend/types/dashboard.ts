export type TrendPoint = { name: string; value: number };
export type Insight = { title: string; body: string; severity: string };
export type Activity = { action: string; actor: string; timestamp: string };

export type StudentRow = {
  name: string;
  registration_number: string;
  batch: string;
  domain: string;
  attendance_rate: number;
  assignment_completion: number;
  engagement_score: number;
  overall_score: number;
  category: string;
  risk_level: string;
  certificate_status: string;
  trend: string;
  missing_assignments: number;
  late_submissions: number;
};

export type BatchPerformance = {
  name: string;
  domain: string;
  students: number;
  mentor: string;
  attendance_rate: number;
  assignment_completion: number;
  engagement_score: number;
  health_score: number;
};

export type DashboardSummary = {
  role_center: { name: string; question: string; primary_action: string };
  total_interns: number;
  total_batches: number;
  active_sessions: number;
  attendance_rate: number;
  assignment_completion: number;
  engagement_score: number;
  certificate_eligible: number;
  at_risk_students: number;
  high_risk_students: number;
  medium_risk_students: number;
  internship_health_score: number;
  weekly_growth: number;
  attendance_trend: TrendPoint[];
  completion_trend: TrendPoint[];
  engagement_trend: TrendPoint[];
  batch_performance: BatchPerformance[];
  risk_students: StudentRow[];
  top_performers: StudentRow[];
  ai_insights: Insight[];
  activity_feed: Activity[];
  session_timeline: { title: string; batch: string; host: string; status: string; attendance_rate: number; late_joiners: number; early_leavers: number; started_at: string }[];
  late_joiners: { name: string; batch: string; delay_minutes: number; session: string }[];
  early_leavers: { name: string; batch: string; left_minutes_early: number; session: string }[];
  attendance_alerts: { title: string; body: string; severity: string }[];
  assignment_reviews: { title: string; batch: string; pending_reviews: number; late_submissions: number }[];
  coaching_queue: StudentRow[];
  coaching_insights: { title: string; body: string }[];
  certificate_forecast: { status: string; count: number; color: string }[];
  risk_heatmap: { batch: string; high: number; medium: number; low: number }[];
  security_events: { event: string; severity: string; service: string; timestamp: string }[];
  api_metrics: { name: string; value: string; status: string }[];
  notifications: { title: string; channel: string; time: string }[];
};
