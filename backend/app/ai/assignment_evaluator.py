from __future__ import annotations

from typing import Any

from app.services.ai_intelligence import evaluate_assignment_submission as base_evaluate_assignment_submission


def evaluate_assignment_submission(title: str, submission_text: str, max_score: int = 100) -> dict[str, Any]:
    return {
        **base_evaluate_assignment_submission(title, submission_text, max_score),
        'model_version': 'heuristic-v1',
    }
