from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.services.operational_intelligence import dashboard_summary, student_rows


def attendance_drop_predictions(db: Session) -> list[dict[str, Any]]:
    predictions = []
    for row in student_rows(db):
        risk_points = 0
        reasons: list[str] = []

        if row['attendance_rate'] < 70:
            risk_points += 50
            reasons.append('Attendance is already below 70%')
        elif row['attendance_rate'] < 80:
            risk_points += 25
            reasons.append('Attendance is close to the intervention threshold')

        if row['trend'] == 'declining':
            risk_points += 20
            reasons.append('Performance trend is declining')
        if row['late_submissions'] > 0:
            risk_points += min(row['late_submissions'] * 8, 20)
            reasons.append('Late submissions indicate schedule pressure')
        if row['missing_assignments'] > 0:
            risk_points += min(row['missing_assignments'] * 10, 25)
            reasons.append('Missing assignments often correlate with attendance drops')

        probability = min(max(risk_points, 5), 95)
        level = 'High' if probability >= 60 else 'Medium' if probability >= 35 else 'Low'
        predictions.append(
            {
                'student': row['name'],
                'registration_number': row['registration_number'],
                'batch': row['batch'],
                'current_attendance': row['attendance_rate'],
                'drop_probability': probability,
                'risk_level': level,
                'reasons': reasons or ['Stable attendance and submission behavior'],
                'recommended_action': 'Schedule mentor check-in' if level == 'High' else 'Monitor next session' if level == 'Medium' else 'Continue normal tracking',
            }
        )

    return sorted(predictions, key=lambda item: item['drop_probability'], reverse=True)


def performance_forecasts(db: Session) -> list[dict[str, Any]]:
    forecasts = []
    for row in student_rows(db):
        adjustment = 0
        if row['trend'] == 'improving':
            adjustment += 4
        elif row['trend'] == 'declining':
            adjustment -= 6
        adjustment -= min(row['missing_assignments'] * 3, 12)
        adjustment -= min(row['late_submissions'] * 1.5, 6)

        final_score = round(min(max(row['overall_score'] + adjustment, 0), 100), 1)
        if final_score >= 85:
            outcome = 'Excellent completion'
        elif final_score >= 75:
            outcome = 'Good completion'
        elif final_score >= 65:
            outcome = 'Needs guided completion'
        else:
            outcome = 'High risk completion'

        forecasts.append(
            {
                'student': row['name'],
                'registration_number': row['registration_number'],
                'batch': row['batch'],
                'current_score': row['overall_score'],
                'forecast_score': final_score,
                'forecast_outcome': outcome,
                'confidence': _confidence_from_row(row),
                'drivers': _forecast_drivers(row),
            }
        )
    return sorted(forecasts, key=lambda item: item['forecast_score'], reverse=True)


def _confidence_from_row(row: dict[str, Any]) -> str:
    signals = 0
    signals += 1 if row['attendance_rate'] > 0 else 0
    signals += 1 if row['assignment_completion'] > 0 else 0
    signals += 1 if row['engagement_score'] > 0 else 0
    if signals >= 3:
        return 'High'
    if signals == 2:
        return 'Medium'
    return 'Low'


def _forecast_drivers(row: dict[str, Any]) -> list[str]:
    drivers = [
        f"Attendance at {row['attendance_rate']}%",
        f"Assignment completion at {row['assignment_completion']}%",
        f"Engagement score at {row['engagement_score']}%",
    ]
    if row['missing_assignments']:
        drivers.append(f"{row['missing_assignments']} missing assignment(s)")
    if row['late_submissions']:
        drivers.append(f"{row['late_submissions']} late submission(s)")
    return drivers


def evaluate_assignment_submission(title: str, submission_text: str, max_score: int = 100) -> dict[str, Any]:
    text = submission_text.strip()
    words = [word for word in text.replace('\n', ' ').split(' ') if word.strip()]
    lower_text = text.lower()

    score = 35
    strengths: list[str] = []
    improvements: list[str] = []
    risk_flags: list[str] = []

    if len(words) >= 120:
        score += 18
        strengths.append('Submission has enough detail for meaningful review')
    elif len(words) >= 60:
        score += 10
        strengths.append('Submission includes a basic explanation')
    else:
        improvements.append('Add more implementation detail and reasoning')
        risk_flags.append('Submission is very short')

    technical_terms = ['function', 'api', 'database', 'test', 'component', 'model', 'algorithm', 'security', 'validation', 'error']
    matched_terms = [term for term in technical_terms if term in lower_text]
    score += min(len(matched_terms) * 4, 24)
    if matched_terms:
        strengths.append(f"Uses relevant technical language: {', '.join(matched_terms[:5])}")
    else:
        improvements.append('Use clearer technical terms from the assignment topic')

    if any(term in lower_text for term in ['test', 'tested', 'pytest', 'unit test', 'validation']):
        score += 12
        strengths.append('Mentions testing or validation')
    else:
        improvements.append('Include evidence of testing or validation')

    if any(term in lower_text for term in ['challenge', 'issue', 'fixed', 'debug', 'improved']):
        score += 8
        strengths.append('Reflects on implementation challenges')
    else:
        improvements.append('Explain one challenge faced and how it was solved')

    if any(term in lower_text for term in ['copied', 'chatgpt wrote', 'not sure']):
        score -= 15
        risk_flags.append('Needs originality/manual review')

    normalized_score = round(min(max(score, 0), max_score), 1)
    return {
        'title': title.strip() or 'Assignment submission',
        'score': normalized_score,
        'max_score': max_score,
        'grade': _grade(normalized_score, max_score),
        'strengths': strengths or ['Submission is reviewable'],
        'improvements': improvements or ['Ready for mentor approval after a quick manual check'],
        'risk_flags': risk_flags,
        'feedback': _feedback(normalized_score, max_score),
    }


def _grade(score: float, max_score: int) -> str:
    percentage = (score / max(max_score, 1)) * 100
    if percentage >= 90:
        return 'A'
    if percentage >= 80:
        return 'B'
    if percentage >= 70:
        return 'C'
    if percentage >= 60:
        return 'D'
    return 'Needs Revision'


def _feedback(score: float, max_score: int) -> str:
    percentage = (score / max(max_score, 1)) * 100
    if percentage >= 80:
        return 'Strong submission. Mentor can verify details and approve or add final comments.'
    if percentage >= 60:
        return 'Moderate submission. Ask the student to strengthen evidence, testing, and explanation.'
    return 'Weak submission. Request resubmission with clearer implementation details and proof of work.'


def executive_ai_report(db: Session) -> dict[str, Any]:
    summary = dashboard_summary(db)
    attendance_predictions = attendance_drop_predictions(db)
    forecasts = performance_forecasts(db)
    high_drop_count = sum(1 for item in attendance_predictions if item['risk_level'] == 'High')
    outcome_counter = Counter(item['forecast_outcome'] for item in forecasts)

    narrative = (
        f"Internship health is {summary['internship_health_score']}/100 with "
        f"{summary['total_interns']} active interns across {summary['total_batches']} batches. "
        f"{high_drop_count} students show high attendance-drop probability, and "
        f"{summary['at_risk_students']} students are currently in the intervention queue."
    )

    recommendations = []
    if high_drop_count:
        recommendations.append('Run mentor check-ins for high attendance-drop probability students within 48 hours.')
    if summary['assignment_completion'] < 80:
        recommendations.append('Prioritize assignment recovery plans before certificate eligibility is affected.')
    if summary['attendance_rate'] < 80:
        recommendations.append('Review session timing and attendance reminders for low-attendance batches.')
    recommendations.append('Use weekly AI report snapshots during director review meetings.')

    return {
        'title': 'AI Executive Internship Report',
        'narrative': narrative,
        'health_score': summary['internship_health_score'],
        'attendance_drop_risks': attendance_predictions[:5],
        'performance_forecast_mix': dict(outcome_counter),
        'top_forecasts': forecasts[:5],
        'recommendations': recommendations,
    }


def ai_module_overview(db: Session) -> dict[str, Any]:
    return {
        'attendance_predictions': attendance_drop_predictions(db)[:8],
        'performance_forecasts': performance_forecasts(db)[:8],
        'executive_report': executive_ai_report(db),
        'example_prompts': [
            'Show students with attendance below 70%.',
            'Who are the top performers?',
            'Which students are at risk?',
            'Show students missing assignments.',
        ],
    }
