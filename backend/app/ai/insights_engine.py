from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.attendance_prediction import attendance_drop_predictions
from app.ai.model_training import model_status
from app.ai.performance_forecasting import performance_forecasts
from app.ai.providers import live_ai_configured, live_provider_name
from app.ai.risk_detection import risk_analysis
from app.services.ai_intelligence import executive_ai_report as base_executive_ai_report


def executive_ai_report(db: Session) -> dict[str, Any]:
    report = base_executive_ai_report(db)
    report['risk_analysis'] = risk_analysis(db)[:8]
    return report


def ai_module_overview(db: Session) -> dict[str, Any]:
    return {
        'attendance_predictions': attendance_drop_predictions(db)[:8],
        'performance_forecasts': performance_forecasts(db)[:8],
        'risk_analysis': risk_analysis(db)[:8],
        'executive_report': executive_ai_report(db),
        'model_status': model_status(db),
        'provider_status': {
            'provider': live_provider_name(),
            'live_enabled': live_ai_configured(),
        },
        'example_prompts': [
            'Show students with attendance below 70%.',
            'Who are the top performers?',
            'Which students are at risk?',
            'Show students missing assignments.',
            'Show certificate eligible students.',
            'Compare AIML and Data Science batches.',
        ],
    }
