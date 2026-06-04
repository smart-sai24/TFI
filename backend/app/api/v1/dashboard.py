from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.services.operational_intelligence import dashboard_summary

router = APIRouter()


@router.get('/summary')
def get_dashboard_summary(
    user: CurrentUser = require_permission('dashboard:read'),
    db: Session = Depends(get_db),
    role: str | None = Query(None),
) -> Any:
    return dashboard_summary(db, role or user.role)
