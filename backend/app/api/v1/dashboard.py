from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import CurrentUser, require_permission
from app.core.config import settings
from app.core.security import normalize_role
from app.db.session import get_db
from app.services.operational_intelligence import dashboard_summary

router = APIRouter()


@router.get('/summary')
def get_dashboard_summary(
    user: CurrentUser = require_permission('dashboard:read'),
    db: Session = Depends(get_db),
    role: str | None = Query(None),
) -> Any:
    effective_role = user.role
    if settings.demo_mode and role:
        try:
            effective_role = normalize_role(role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid demo role')
    return dashboard_summary(db, effective_role)
