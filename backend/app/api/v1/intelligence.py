from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.ai.assignment_evaluator import evaluate_assignment_submission
from app.ai.attendance_prediction import attendance_drop_predictions
from app.ai.insights_engine import ai_module_overview, executive_ai_report
from app.ai.mentor_assistant import answer_mentor_query
from app.ai.model_training import model_status, retrain_models
from app.ai.performance_forecasting import performance_forecasts
from app.ai.report_generator import generate_ai_report
from app.ai.risk_detection import risk_analysis
from app.db.session import get_db
from app.models.operations import (
    AiConversation,
    AiReport,
    AssignmentEvaluation,
)
from app.services.operational_intelligence import dashboard_summary, student_rows

router = APIRouter()


class AssistantRequest(BaseModel):
    query: str


class AssignmentEvaluationRequest(BaseModel):
    title: str
    submission_text: str
    max_score: int = 100
    submission_id: int | None = None
    student_id: int | None = None


class AiReportRequest(BaseModel):
    report_type: str = 'Weekly Report'
    output_format: str = 'markdown'


@router.get('/students')
def get_student_intelligence(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return student_rows(db)


@router.get('/students/page')
def get_student_intelligence_page(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    rows = student_rows(db)
    return {
        'items': rows[offset:offset + limit],
        'total': len(rows),
        'limit': limit,
        'offset': offset,
        'has_more': offset + limit < len(rows),
    }


@router.get('/insights')
def get_ai_insights(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    summary = dashboard_summary(db, user.role)
    return {
        'insights': summary['ai_insights'],
        'risk_students': summary['risk_students'],
        'top_performers': summary['top_performers'],
        'activity_feed': summary['activity_feed'],
    }


@router.get('/ai/overview')
def get_ai_module_overview(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return ai_module_overview(db)


@router.get('/ai/attendance-predictions')
def get_attendance_predictions(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return attendance_drop_predictions(db)


@router.get('/ai/attendance-prediction')
def get_attendance_prediction(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return attendance_drop_predictions(db)


@router.get('/ai/performance-forecasts')
def get_performance_forecasts(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return performance_forecasts(db)


@router.get('/ai/performance-forecast')
def get_performance_forecast(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return performance_forecasts(db)


@router.get('/ai/risk-analysis')
def get_risk_analysis(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return risk_analysis(db)


@router.get('/ai/executive-report')
def get_executive_ai_report(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return executive_ai_report(db)


@router.post('/assistant')
def ask_ai_mentor_assistant(
    request: AssistantRequest,
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    response = answer_mentor_query(db, request.query)
    conversation_uid = None if user.uid == 'demo-user' else user.uid
    db.add(AiConversation(user_uid=conversation_uid, query=request.query, response=response))
    db.commit()
    return response


@router.post('/ai/mentor-chat')
def ask_ai_mentor_chat(
    request: AssistantRequest,
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return ask_ai_mentor_assistant(request, user, db)


@router.post('/ai/report-generation')
def generate_ai_report_endpoint(
    request: AiReportRequest,
    user: CurrentUser = require_permission('reports:generate'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = generate_ai_report(db, request.report_type, request.output_format)
    db.add(
        AiReport(
            report_type=result['report_type'],
            output_format=result['output_format'],
            status=result['status'],
            generated_by_uid=user.uid,
            file_url=result['file_url'],
            content=result['content'],
            payload=result['payload'],
        )
    )
    db.commit()
    return result


@router.get('/ai/model-status')
def get_ai_model_status(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return model_status(db)


@router.post('/ai/model-retraining')
def retrain_ai_models(
    user: CurrentUser = require_permission('system:admin'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return retrain_models(db)


@router.post('/ai/assignment-evaluation')
def evaluate_assignment(
    request: AssignmentEvaluationRequest,
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = evaluate_assignment_submission(request.title, request.submission_text, request.max_score)
    db.add(
        AssignmentEvaluation(
            submission_id=request.submission_id,
            student_id=request.student_id,
            title=result['title'],
            score=result['score'],
            max_score=result['max_score'],
            grade=result['grade'],
            feedback=result['feedback'],
            strengths=result['strengths'],
            improvements=result['improvements'],
            risk_flags=result['risk_flags'],
            model_version=result['model_version'],
        )
    )
    db.commit()
    return result
