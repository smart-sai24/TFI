from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.services.ai_intelligence import (
    ai_module_overview,
    attendance_drop_predictions,
    evaluate_assignment_submission,
    executive_ai_report,
    performance_forecasts,
)
from app.services.operational_intelligence import answer_assistant_query, dashboard_summary, student_rows

router = APIRouter()


class AssistantRequest(BaseModel):
    query: str


class AssignmentEvaluationRequest(BaseModel):
    title: str
    submission_text: str
    max_score: int = 100


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


@router.get('/ai/performance-forecasts')
def get_performance_forecasts(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return performance_forecasts(db)


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
    return answer_assistant_query(db, request.query)


@router.post('/ai/assignment-evaluation')
def evaluate_assignment(
    request: AssignmentEvaluationRequest,
    user: CurrentUser = require_permission('intelligence:read'),
) -> dict[str, Any]:
    return evaluate_assignment_submission(request.title, request.submission_text, request.max_score)
