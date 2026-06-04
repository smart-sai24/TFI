from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.services.operational_intelligence import reports_overview

router = APIRouter()


@router.get('/overview')
def get_reports_overview(
    user: CurrentUser = require_permission('reports:read'),
    db: Session = Depends(get_db),
) -> Any:
    return reports_overview(db)
