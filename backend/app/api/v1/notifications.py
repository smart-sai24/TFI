from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.db.session import get_db
from app.models.operations import Notification
from app.services.nudges import run_auto_nudges, serialize_notification

router = APIRouter()


class RunNudgesRequest(BaseModel):
    attendance_session_id: int | None = None
    auto_send: bool | None = None


class TrackResponseRequest(BaseModel):
    response_status: str
    notes: str | None = None
    responder: str | None = None


@router.get('')
def list_notifications(
    user: CurrentUser = require_permission('notifications:read'),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    response_status: str | None = None,
) -> dict[str, Any]:
    query = select(Notification).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)
    if response_status:
        query = query.where(Notification.response_status == response_status)
    notifications = db.scalars(query).all()
    return {'items': [serialize_notification(item) for item in notifications], 'total': len(notifications)}


@router.post('/nudges/run')
def run_nudges(
    request: RunNudgesRequest,
    user: CurrentUser = require_permission('notifications:send'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    actor_uid = None if user.uid == 'demo-user' else user.uid
    return run_auto_nudges(db, actor_uid=actor_uid, attendance_session_id=request.attendance_session_id, auto_send=request.auto_send)


@router.post('/{notification_id}/response')
def track_notification_response(
    notification_id: int,
    request: TrackResponseRequest,
    user: CurrentUser = require_permission('notifications:send'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    allowed_statuses = {'pending', 'replied', 'resolved', 'no_response', 'invalid_contact'}
    normalized_status = request.response_status.strip().lower()
    if normalized_status not in allowed_statuses:
        raise HTTPException(status_code=422, detail=f'Response status must be one of: {", ".join(sorted(allowed_statuses))}')

    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail='Notification not found')

    notification.response_status = normalized_status
    notification.response_payload = {
        'notes': request.notes,
        'responder': request.responder or user.email,
        'tracked_by_uid': None if user.uid == 'demo-user' else user.uid,
    }
    notification.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)
    return serialize_notification(notification)
