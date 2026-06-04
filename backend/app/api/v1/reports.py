from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.models.operations import AuditLog, Report
from app.services.operational_intelligence import reports_overview

router = APIRouter()


class GenerateReportRequest(BaseModel):
    report_type: str


@router.get('/overview')
def get_reports_overview(
    user: CurrentUser = require_permission('reports:read'),
    db: Session = Depends(get_db),
) -> Any:
    return reports_overview(db)


@router.post('/generate')
def generate_report(
    request: GenerateReportRequest,
    user: CurrentUser = require_permission('reports:generate'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    metrics = reports_overview(db)
    report = Report(
        report_type=request.report_type.strip() or 'General operations',
        status='completed',
        generated_by_uid=user.uid,
        parameters={'format': 'snapshot'},
        metrics_snapshot=metrics,
    )
    db.add(report)
    db.flush()
    db.add(
        AuditLog(
            actor_uid=user.uid,
            action='report.generated',
            entity_type='report',
            entity_id=str(report.id),
            metadata_json={'report_type': report.report_type, 'severity': 'Low'},
        )
    )
    db.commit()
    return {
        'id': report.id,
        'report_type': report.report_type,
        'status': report.status,
        'metrics_snapshot': metrics,
    }
