from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.operational_intelligence import student_rows


def risk_analysis(db: Session) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    for row in student_rows(db):
        risk_types: list[str] = []
        reasoning: list[str] = []

        if row['attendance_rate'] < 80:
            risk_types.append('Attendance Risk')
            reasoning.append(f"Attendance is {row['attendance_rate']}%, below the preferred 80% operating target.")
        if row['assignment_completion'] < 80 or row['missing_assignments'] > 0:
            risk_types.append('Assignment Risk')
            reasoning.append(f"Assignment completion is {row['assignment_completion']}% with {row['missing_assignments']} missing item(s).")
        if row['engagement_score'] < 70:
            risk_types.append('Engagement Risk')
            reasoning.append(f"Engagement score is {row['engagement_score']}%, requiring mentor follow-up.")
        if row['certificate_status'] != 'Eligible':
            risk_types.append('Certification Risk')
            reasoning.append(f"Certificate status is currently {row['certificate_status']}.")
        if row['overall_score'] < 70 or row['trend'] == 'declining':
            risk_types.append('Academic Risk')
            reasoning.append(f"Overall score is {row['overall_score']} with a {row['trend']} trend.")

        risk_level = 'Critical' if row['risk_score'] >= 75 else row['risk_level']
        analyses.append(
            {
                'student': row['name'],
                'registration_number': row['registration_number'],
                'batch': row['batch'],
                'risk_level': risk_level,
                'risk_score': row['risk_score'],
                'risk_types': risk_types or ['Low Operational Risk'],
                'reasoning': reasoning or ['Healthy attendance, assignment, engagement, and certificate signals.'],
                'recommendations': row['recommendations'],
            }
        )

    severity_rank = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
    return sorted(analyses, key=lambda item: (severity_rank.get(item['risk_level'], 0), item['risk_score']), reverse=True)
