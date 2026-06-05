from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.model_training import performance_model_scores
from app.services.ai_intelligence import performance_forecasts as base_performance_forecasts


def performance_forecasts(db: Session) -> list[dict[str, Any]]:
    forecasts: list[dict[str, Any]] = []
    model_scores = performance_model_scores(db)
    for item in base_performance_forecasts(db):
        model_score = model_scores.get(item['registration_number'])
        forecast_score = float(model_score if model_score is not None else item['forecast_score'])
        probability = round(min(max(forecast_score + 8, 5), 98), 1)
        if forecast_score >= 85:
            category = 'Excellent'
        elif forecast_score >= 75:
            category = 'Good'
        elif forecast_score >= 65:
            category = 'Average'
        else:
            category = 'Needs Improvement'

        forecasts.append(
            {
                **item,
                'forecast_score': forecast_score,
                'predicted_final_score': forecast_score,
                'predicted_category': category,
                'certificate_eligibility_probability': probability,
                'model_version': 'sklearn-v1' if model_score is not None else 'heuristic-v1',
            }
        )
    return forecasts
