from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.services.operational_intelligence import answer_assistant_query, dashboard_summary, student_rows

router = APIRouter()


class AssistantRequest(BaseModel):
    query: str


@router.get('/students')
def get_student_intelligence(
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return student_rows(db)


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


@router.post('/assistant')
def ask_ai_mentor_assistant(
    request: AssistantRequest,
    user: CurrentUser = require_permission('intelligence:read'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return answer_assistant_query(db, request.query)
