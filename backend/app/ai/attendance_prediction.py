from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.model_training import attendance_model_probabilities
from app.services.ai_intelligence import attendance_drop_predictions as base_attendance_drop_predictions


def attendance_drop_predictions(db: Session) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    model_probabilities = attendance_model_probabilities(db)
    for item in base_attendance_drop_predictions(db):
        model_probability = model_probabilities.get(item['registration_number'])
        probability = float(model_probability if model_probability is not None else item['drop_probability'])
        current_attendance = float(item['current_attendance'])
        seven_day_drop = round(probability * 0.06, 1)
        thirty_day_drop = round(probability * 0.16, 1)
        confidence = round(min(max(62 + probability * 0.28, 65), 92), 1)

        predictions.append(
            {
                **item,
                'drop_probability': probability,
                'attendance_risk_score': round(probability, 1),
                'confidence': confidence,
                'likely_to_become_inactive': probability >= 70 or current_attendance < 60,
                'likely_to_miss_future_sessions': probability >= 45,
                'trend_direction': 'declining' if probability >= 45 else 'stable',
                'next_7_days_forecast': round(max(current_attendance - seven_day_drop, 0), 1),
                'next_30_days_forecast': round(max(current_attendance - thirty_day_drop, 0), 1),
                'model_version': 'sklearn-v1' if model_probability is not None else 'heuristic-v1',
            }
        )
    return predictions
