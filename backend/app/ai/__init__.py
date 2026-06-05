"""AI Intelligence Layer entry points.

The platform keeps deterministic local engines here so dashboards, tests, and
offline deployments work even when external LLM providers are not configured.
"""

from app.ai.assignment_evaluator import evaluate_assignment_submission
from app.ai.authenticity import run_authenticity_check
from app.ai.attendance_prediction import attendance_drop_predictions
from app.ai.insights_engine import ai_module_overview, executive_ai_report
from app.ai.mentor_assistant import answer_mentor_query
from app.ai.model_training import model_status, retrain_models
from app.ai.performance_forecasting import performance_forecasts
from app.ai.report_generator import generate_ai_report
from app.ai.risk_detection import risk_analysis

__all__ = [
    'ai_module_overview',
    'answer_mentor_query',
    'attendance_drop_predictions',
    'evaluate_assignment_submission',
    'executive_ai_report',
    'generate_ai_report',
    'model_status',
    'performance_forecasts',
    'retrain_models',
    'risk_analysis',
    'run_authenticity_check',
]
