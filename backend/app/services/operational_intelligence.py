from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from statistics import mean
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.operations import (
    Assignment,
    AttendanceRecord,
    AttendanceSession,
    AuditLog,
    Batch,
    Certificate,
    Notification,
    PerformanceScore,
    RiskProfile,
    Student,
    Submission,
)
from app.services.observability import api_metrics_collector


ROLE_CENTERS = {
    'Director': {
        'name': 'Executive Analytics Center',
        'question': 'Is the internship program healthy?',
        'primary_action': 'Review weekly AI summary',
    },
    'Host': {
        'name': 'Operations Command Center',
        'question': 'What is happening right now?',
        'primary_action': 'Import attendance',
    },
    'Mentor': {
        'name': 'Student Success Hub',
        'question': 'Which students need my attention today?',
        'primary_action': 'Open coaching queue',
    },
    'Admin': {
        'name': 'System Control Center',
        'question': 'Is the platform operating correctly?',
        'primary_action': 'Review security events',
    },
}


def safe_average(values: list[float]) -> float:
    return round(mean(values), 1) if values else 0.0


def calculate_performance_score(attendance_rate: float, assignment_completion: float, engagement_score: float) -> float:
    return round(attendance_rate * 0.4 + assignment_completion * 0.4 + engagement_score * 0.2, 1)


def categorize_performance(score: float) -> str:
    if score >= 92:
        return 'Outstanding'
    if score >= 84:
        return 'Excellent'
    if score >= 75:
        return 'Good'
    if score >= 65:
        return 'Average'
    return 'Needs Improvement'


def classify_risk(attendance_rate: float, missing_assignments: int, late_submissions: int, trend: str) -> dict[str, Any]:
    reasons: list[str] = []
    score = 0.0

    if attendance_rate < 70:
        score += 45
        reasons.append('Attendance below 70% threshold')
    elif attendance_rate < 80:
        score += 25
        reasons.append('Attendance requires monitoring')

    if missing_assignments >= 2:
        score += 35
        reasons.append('Multiple missing assignments')
    elif missing_assignments == 1:
        score += 18
        reasons.append('One assignment missing')

    if late_submissions >= 2:
        score += 15
        reasons.append('Repeated late submissions')

    if trend == 'declining':
        score += 10
        reasons.append('Performance trend is declining')

    level = 'Low'
    if score >= 65:
        level = 'High'
    elif score >= 30:
        level = 'Medium'

    recommendations = {
        'High': ['Schedule mentor intervention', 'Send attendance and assignment recovery plan'],
        'Medium': ['Send reminder sequence', 'Review next two submissions closely'],
        'Low': ['Continue normal monitoring'],
    }[level]

    return {
        'level': level,
        'score': min(round(score, 1), 100),
        'reasons': reasons or ['Healthy attendance and assignment behavior'],
        'recommendations': recommendations,
        'completion_probability': max(round(100 - score * 0.7, 1), 20),
    }


def compute_certificate_status(attendance_rate: float, assignment_completion: float, engagement_score: float) -> dict[str, Any]:
    eligibility_score = round(attendance_rate * 0.5 + assignment_completion * 0.35 + engagement_score * 0.15, 1)
    if attendance_rate >= 80 and assignment_completion >= 80 and eligibility_score >= 82:
        status = 'Eligible'
    elif attendance_rate >= 70 and assignment_completion >= 65:
        status = 'Warning'
    else:
        status = 'Not Eligible'
    return {'status': status, 'eligibility_score': eligibility_score}


def student_rows(db: Session) -> list[dict[str, Any]]:
    students = db.scalars(
        select(Student)
        .options(
            selectinload(Student.batch),
            selectinload(Student.attendance_records).selectinload(AttendanceRecord.session),
            selectinload(Student.submissions),
            selectinload(Student.risk_profile),
        )
        .where(Student.enrollment_status == 'active')
    ).all()
    rows: list[dict[str, Any]] = []

    for student in students:
        attendance_records = list(student.attendance_records)
        submissions = list(student.submissions)
        latest_score = db.scalars(
            select(PerformanceScore)
            .where(PerformanceScore.student_id == student.id)
            .order_by(PerformanceScore.score_date.desc(), PerformanceScore.id.desc())
            .limit(1)
        ).first()
        persisted_risk = student.risk_profile
        latest_certificate = db.scalars(
            select(Certificate)
            .where(Certificate.student_id == student.id)
            .order_by(Certificate.issued_at.desc().nullslast(), Certificate.id.desc())
            .limit(1)
        ).first()

        attendance_rate = (
            round(float(latest_score.attendance_score), 1)
            if latest_score
            else safe_average([float(record.attendance_percentage) for record in attendance_records])
        )
        assignment_completion = (
            round(float(latest_score.assignment_score), 1)
            if latest_score
            else round((sum(1 for submission in submissions if submission.status not in {'missing', 'rejected'}) / len(submissions)) * 100, 1)
            if submissions
            else 0.0
        )
        engagement_score = (
            round(float(latest_score.engagement_score), 1)
            if latest_score
            else safe_average([float(record.engagement_score) for record in attendance_records])
        )
        missing_assignments = sum(1 for submission in submissions if submission.status == 'missing')
        late_submissions = sum(1 for submission in submissions if submission.is_late)
        trend = latest_score.trend if latest_score else 'stable'
        overall_score = (
            round(float(latest_score.overall_score), 1)
            if latest_score
            else calculate_performance_score(attendance_rate, assignment_completion, engagement_score)
        )
        risk = (
            {
                'level': persisted_risk.risk_level,
                'score': round(float(persisted_risk.risk_score), 1),
                'recommendations': persisted_risk.recommendations,
            }
            if persisted_risk
            else classify_risk(attendance_rate, missing_assignments, late_submissions, trend)
        )
        certificate = (
            {'status': latest_certificate.status, 'eligibility_score': round(float(latest_certificate.eligibility_score), 1)}
            if latest_certificate
            else compute_certificate_status(attendance_rate, assignment_completion, engagement_score)
        )

        rows.append(
            {
                'name': student.full_name,
                'registration_number': student.registration_number,
                'batch': student.batch.name if student.batch else 'Unassigned',
                'domain': student.domain,
                'attendance_rate': attendance_rate,
                'assignment_completion': assignment_completion,
                'engagement_score': engagement_score,
                'overall_score': overall_score,
                'overall_rank': 0,
                'category': categorize_performance(overall_score),
                'risk_level': risk['level'],
                'risk_score': risk['score'],
                'certificate_status': certificate['status'],
                'trend': trend,
                'missing_assignments': missing_assignments,
                'late_submissions': late_submissions,
                'recommendations': risk['recommendations'],
            }
        )

    ranked = sorted(rows, key=lambda row: row['overall_score'], reverse=True)
    for rank, row in enumerate(ranked, start=1):
        row['overall_rank'] = rank
    return ranked


def batch_performance(db: Session, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    batches = db.scalars(
        select(Batch).options(selectinload(Batch.students)).where(Batch.status == 'active').order_by(Batch.name)
    ).all()
    by_batch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_batch[row['batch']].append(row)

    result = []
    for batch in batches:
        batch_rows = by_batch.get(batch.name, [])
        attendance = safe_average([row['attendance_rate'] for row in batch_rows])
        completion = safe_average([row['assignment_completion'] for row in batch_rows])
        engagement = safe_average([row['engagement_score'] for row in batch_rows])
        result.append(
            {
                'name': batch.name,
                'domain': batch.domain,
                'students': len(batch.students),
                'mentor': batch.mentor_uid or 'Unassigned',
                'attendance_rate': attendance,
                'assignment_completion': completion,
                'engagement_score': engagement,
                'health_score': calculate_performance_score(attendance, completion, engagement),
            }
        )
    return result


def trend_from_scores(db: Session, column_name: str) -> list[dict[str, Any]]:
    column = getattr(PerformanceScore, column_name)
    rows = db.execute(
        select(PerformanceScore.score_date, func.avg(column))
        .group_by(PerformanceScore.score_date)
        .order_by(PerformanceScore.score_date.desc())
        .limit(4)
    ).all()
    return [{'name': item[0].isoformat(), 'value': round(float(item[1] or 0), 1)} for item in reversed(rows)]


def session_timeline(db: Session) -> list[dict[str, Any]]:
    sessions = db.scalars(
        select(AttendanceSession)
        .options(selectinload(AttendanceSession.batch), selectinload(AttendanceSession.records))
        .order_by(AttendanceSession.session_date.desc(), AttendanceSession.id.desc())
        .limit(6)
    ).all()
    today = date.today()
    result = []
    for session in sessions:
        attendance_values = [float(record.attendance_percentage) for record in session.records]
        status = 'Completed'
        if session.session_date == today:
            status = 'Live'
        elif session.session_date > today:
            status = 'Upcoming'
        result.append(
            {
                'title': session.title,
                'batch': session.batch.name if session.batch else 'Unassigned',
                'host': session.created_by_uid or 'System',
                'status': status,
                'attendance_rate': safe_average(attendance_values),
                'late_joiners': sum(1 for record in session.records if record.late_joining),
                'early_leavers': sum(1 for record in session.records if record.early_leaving),
                'started_at': (session.starts_at or datetime.combine(session.session_date, datetime.min.time(), tzinfo=timezone.utc)).isoformat(),
            }
        )
    return result


def assignment_reviews(db: Session) -> list[dict[str, Any]]:
    assignments = db.scalars(
        select(Assignment)
        .options(selectinload(Assignment.batch), selectinload(Assignment.submissions))
        .order_by(Assignment.due_at.desc())
        .limit(6)
    ).all()
    return [
        {
            'title': assignment.title,
            'batch': assignment.batch.name if assignment.batch else 'Unassigned',
            'pending_reviews': sum(1 for submission in assignment.submissions if submission.status in {'submitted', 'resubmitted'}),
            'late_submissions': sum(1 for submission in assignment.submissions if submission.is_late),
        }
        for assignment in assignments
    ]


def dashboard_summary(db: Session, role: str = 'Director') -> dict[str, Any]:
    rows = student_rows(db)
    role_name = role if role in ROLE_CENTERS else 'Director'
    attendance_rate = safe_average([row['attendance_rate'] for row in rows])
    assignment_completion = safe_average([row['assignment_completion'] for row in rows])
    engagement_score = safe_average([row['engagement_score'] for row in rows])
    health_score = calculate_performance_score(attendance_rate, assignment_completion, engagement_score)
    high_risk_count = sum(1 for row in rows if row['risk_level'] == 'High')
    medium_risk_count = sum(1 for row in rows if row['risk_level'] == 'Medium')
    eligible_count = sum(1 for row in rows if row['certificate_status'] == 'Eligible')
    batches = db.scalars(select(Batch).where(Batch.status == 'active')).all()
    sessions = session_timeline(db)
    weekly_attendance = trend_from_scores(db, 'attendance_score') or [{'name': 'No data', 'value': 0}]
    weekly_completion = trend_from_scores(db, 'assignment_score') or [{'name': 'No data', 'value': 0}]
    weekly_engagement = trend_from_scores(db, 'engagement_score') or [{'name': 'No data', 'value': 0}]
    risk_rows = [row for row in rows if row['risk_level'] in {'High', 'Medium'}]

    return {
        'role': role,
        'role_center': ROLE_CENTERS[role_name],
        'total_interns': len(rows),
        'total_batches': len(batches),
        'active_sessions': len([session for session in sessions if session['status'] == 'Live']),
        'attendance_rate': attendance_rate,
        'assignment_completion': assignment_completion,
        'engagement_score': engagement_score,
        'certificate_eligible': eligible_count,
        'at_risk_students': high_risk_count + medium_risk_count,
        'high_risk_students': high_risk_count,
        'medium_risk_students': medium_risk_count,
        'internship_health_score': health_score,
        'weekly_growth': round((weekly_attendance[-1]['value'] - weekly_attendance[0]['value']) if len(weekly_attendance) > 1 else 0, 1),
        'attendance_trend': weekly_attendance,
        'completion_trend': weekly_completion,
        'engagement_trend': weekly_engagement,
        'batch_performance': batch_performance(db, rows),
        'risk_students': risk_rows,
        'top_performers': rows[:4],
        'ai_insights': generate_insights(rows, weekly_attendance, weekly_completion),
        'activity_feed': activity_feed(db),
        'session_timeline': sessions,
        'late_joiners': late_joiners(db),
        'early_leavers': early_leavers(db),
        'attendance_alerts': attendance_alerts(rows),
        'assignment_reviews': assignment_reviews(db),
        'coaching_queue': [row for row in rows if row['risk_level'] in {'High', 'Medium'} or row['missing_assignments'] > 0],
        'coaching_insights': coaching_insights(risk_rows, rows[:1]),
        'certificate_forecast': certificate_forecast(rows),
        'risk_heatmap': risk_heatmap(db, rows),
        'security_events': security_events(db),
        'api_metrics': api_metrics(),
        'notifications': notifications(db),
    }


def generate_insights(rows: list[dict[str, Any]], attendance_trend: list[dict[str, Any]], completion_trend: list[dict[str, Any]]) -> list[dict[str, str]]:
    high_risk = [row for row in rows if row['risk_level'] == 'High']
    attendance_delta = round((attendance_trend[-1]['value'] - attendance_trend[0]['value']) if len(attendance_trend) > 1 else 0, 1)
    completion = completion_trend[-1]['value'] if completion_trend else 0
    return [
        {'title': 'Attendance momentum', 'body': f'Attendance movement is {attendance_delta:+.1f}% across tracked score periods.', 'severity': 'positive' if attendance_delta >= 0 else 'warning'},
        {'title': 'Assignment throughput', 'body': f'Assignment completion is currently {completion:.1f}%.', 'severity': 'positive' if completion >= 80 else 'warning'},
        {'title': 'Mentor intervention queue', 'body': f'{len(high_risk)} students require immediate mentor intervention.', 'severity': 'critical' if high_risk else 'neutral'},
    ]


def activity_feed(db: Session) -> list[dict[str, str]]:
    audits = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(6)).all()
    return [
        {'action': audit.action, 'actor': audit.actor_uid or 'System', 'timestamp': audit.created_at.isoformat()}
        for audit in audits
    ]


def late_joiners(db: Session) -> list[dict[str, Any]]:
    records = db.scalars(
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.student).selectinload(Student.batch),
            selectinload(AttendanceRecord.session),
        )
        .where(AttendanceRecord.late_joining.is_(True))
        .order_by(AttendanceRecord.id.desc())
        .limit(8)
    ).all()
    return [
        {
            'name': record.student.full_name,
            'batch': record.student.batch.name if record.student and record.student.batch else 'Unassigned',
            'delay_minutes': max(int((record.session.required_minutes or 90) - record.duration_minutes), 0),
            'session': record.session.title,
        }
        for record in records
    ]


def early_leavers(db: Session) -> list[dict[str, Any]]:
    records = db.scalars(
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.student).selectinload(Student.batch),
            selectinload(AttendanceRecord.session),
        )
        .where(AttendanceRecord.early_leaving.is_(True))
        .order_by(AttendanceRecord.id.desc())
        .limit(8)
    ).all()
    return [
        {
            'name': record.student.full_name,
            'batch': record.student.batch.name if record.student and record.student.batch else 'Unassigned',
            'left_minutes_early': max(int((record.session.required_minutes or 90) - record.duration_minutes), 0),
            'session': record.session.title,
        }
        for record in records
    ]


def attendance_alerts(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    alerts = []
    for row in rows:
        if row['attendance_rate'] < 75:
            alerts.append({'title': f'{row["name"]} below attendance target', 'body': f'{row["batch"]} is at {row["attendance_rate"]}%.', 'severity': 'Warning'})
    return alerts[:6]


def coaching_insights(risk_rows: list[dict[str, Any]], top_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    insights = [
        {'title': f'Prioritize {row["name"]}', 'body': f'{row["risk_level"]} risk with {row["missing_assignments"]} missing assignments.'}
        for row in risk_rows[:3]
    ]
    if top_rows:
        insights.append({'title': f'Celebrate {top_rows[0]["name"]}', 'body': 'Top performer can anchor peer learning and reference submissions.'})
    return insights


def certificate_forecast(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {'status': 'Eligible', 'count': sum(1 for row in rows if row['certificate_status'] == 'Eligible'), 'color': '#22C55E'},
        {'status': 'Warning', 'count': sum(1 for row in rows if row['certificate_status'] == 'Warning'), 'color': '#F59E0B'},
        {'status': 'Not Eligible', 'count': sum(1 for row in rows if row['certificate_status'] == 'Not Eligible'), 'color': '#EF4444'},
    ]


def risk_heatmap(db: Session, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    batches = db.scalars(select(Batch).where(Batch.status == 'active').order_by(Batch.name)).all()
    result = []
    for batch in batches:
        batch_rows = [row for row in rows if row['batch'] == batch.name]
        result.append(
            {
                'batch': batch.name,
                'high': sum(1 for row in batch_rows if row['risk_level'] == 'High'),
                'medium': sum(1 for row in batch_rows if row['risk_level'] == 'Medium'),
                'low': sum(1 for row in batch_rows if row['risk_level'] == 'Low'),
            }
        )
    return result


def security_events(db: Session) -> list[dict[str, str]]:
    audits = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(6)).all()
    return [
        {'event': audit.action, 'severity': str(audit.metadata_json.get('severity', 'Low')), 'service': audit.entity_type, 'timestamp': audit.created_at.isoformat()}
        for audit in audits
    ]


def api_metrics() -> list[dict[str, str]]:
    return api_metrics_collector.snapshot()


def notifications(db: Session) -> list[dict[str, str]]:
    records = db.scalars(select(Notification).order_by(Notification.created_at.desc()).limit(6)).all()
    return [{'title': item.template, 'channel': item.channel, 'time': item.created_at.strftime('%H:%M')} for item in records]


def reports_overview(db: Session) -> dict[str, Any]:
    rows = student_rows(db)
    summary = dashboard_summary(db)
    return {
        'certificate_eligible': sum(1 for row in rows if row['certificate_status'] == 'Eligible'),
        'total_students': len(rows),
        'defaulter_count': summary['at_risk_students'],
        'report_status': 'Ready' if rows else 'No data',
        'weekly_attendance': summary['attendance_trend'][-3:],
        'exports': ['PDF', 'CSV', 'Excel'],
        'ai_insights': summary['ai_insights'],
    }


def answer_assistant_query(db: Session, query: str) -> dict[str, Any]:
    normalized = query.lower().strip()
    rows = student_rows(db)
    if 'below 70' in normalized or ('attendance' in normalized and '70' in normalized):
        result = [row for row in rows if row['attendance_rate'] < 70]
    elif 'missed' in normalized or 'missing' in normalized:
        result = [row for row in rows if row['missing_assignments'] > 0]
    elif 'eligible' in normalized:
        result = [row for row in rows if row['certificate_status'] == 'Eligible']
    elif 'top' in normalized or 'performer' in normalized:
        result = rows[:5]
    elif 'risk' in normalized:
        result = [row for row in rows if row['risk_level'] in {'High', 'Medium'}]
    else:
        result = rows
    return {'query': query, 'count': len(result), 'results': result, 'summary': f'Found {len(result)} matching student records.'}
