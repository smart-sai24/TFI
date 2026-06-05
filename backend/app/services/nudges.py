from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.operations import Assignment, AttendanceRecord, AttendanceSession, Notification, Student, Submission
from app.models.user import User
from app.services.notifications import send_email, send_whatsapp


def run_auto_nudges(
    db: Session,
    actor_uid: str | None = None,
    attendance_session_id: int | None = None,
    auto_send: bool | None = None,
) -> dict[str, Any]:
    should_send = settings.notification_auto_send if auto_send is None else auto_send
    events = [
        *missed_attendance_events(db, attendance_session_id),
        *missing_assignment_events(db),
    ]
    created: list[Notification] = []
    skipped = 0

    for event in events:
        for target in notification_targets(db, event):
            existing = existing_notification(db, event['event_key'], target['channel'], target['recipient_id'])
            if existing:
                skipped += 1
                continue

            notification = Notification(
                recipient_type=target['recipient_type'],
                recipient_id=target['recipient_id'],
                channel=target['channel'],
                template=event['template'],
                status='queued',
                response_status='pending',
                payload={
                    **event,
                    'actor_uid': actor_uid,
                    'recipient_name': target.get('recipient_name'),
                    'recipient_role': target['recipient_type'],
                    'message': target['message'],
                    'subject': target['subject'],
                    'delivery_mode': 'auto_send' if should_send else 'queued',
                },
            )
            db.add(notification)
            db.flush()
            if should_send:
                deliver_notification(notification)
            created.append(notification)

    db.commit()
    return {
        'status': 'completed',
        'detected_events': len(events),
        'created_notifications': len(created),
        'skipped_duplicates': skipped,
        'auto_send': should_send,
        'notifications': [serialize_notification(item) for item in created],
    }


def missed_attendance_events(db: Session, attendance_session_id: int | None = None) -> list[dict[str, Any]]:
    query = (
        select(AttendanceRecord)
        .options(
            selectinload(AttendanceRecord.student).selectinload(Student.batch),
            selectinload(AttendanceRecord.session),
        )
        .where(AttendanceRecord.attendance_percentage < settings.nudge_missed_attendance_threshold)
    )
    if attendance_session_id is not None:
        query = query.where(AttendanceRecord.session_id == attendance_session_id)

    events = []
    for record in db.scalars(query).all():
        student = record.student
        if not student or not record.session:
            continue
        severity = 'critical' if record.attendance_percentage < 25 else 'warning'
        events.append(
            {
                'event_key': f'attendance:{record.session_id}:{record.student_id}',
                'event_type': 'missed_attendance',
                'template': 'missed_attendance_nudge',
                'severity': severity,
                'student_id': student.id,
                'student_name': student.full_name,
                'student_email': student.email,
                'student_phone': student.phone,
                'batch_id': student.batch_id,
                'batch_name': student.batch.name if student.batch else 'Unassigned',
                'session_id': record.session_id,
                'session_title': record.session.title,
                'session_date': record.session.session_date.isoformat(),
                'attendance_percentage': round(float(record.attendance_percentage), 1),
                'reason': f"Attendance was {round(float(record.attendance_percentage), 1)}% for {record.session.title}.",
            }
        )
    return events


def missing_assignment_events(db: Session) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    submissions = db.scalars(
        select(Submission)
        .options(
            selectinload(Submission.student).selectinload(Student.batch),
            selectinload(Submission.assignment).selectinload(Assignment.batch),
        )
        .where(Submission.status == 'missing')
    ).all()
    missing_counts: dict[int, int] = {}
    for submission in submissions:
        missing_counts[submission.student_id] = missing_counts.get(submission.student_id, 0) + 1

    events = []
    for submission in submissions:
        student = submission.student
        assignment = submission.assignment
        if not student or not assignment:
            continue
        due_at = assignment.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if due_at > now:
            continue
        missing_count = missing_counts.get(student.id, 1)
        severity = 'critical' if missing_count >= settings.nudge_critical_missing_assignments else 'warning'
        events.append(
            {
                'event_key': f'assignment:{assignment.id}:{student.id}',
                'event_type': 'missing_assignment',
                'template': 'missing_assignment_nudge',
                'severity': severity,
                'student_id': student.id,
                'student_name': student.full_name,
                'student_email': student.email,
                'student_phone': student.phone,
                'batch_id': student.batch_id,
                'batch_name': student.batch.name if student.batch else 'Unassigned',
                'assignment_id': assignment.id,
                'assignment_title': assignment.title,
                'due_at': due_at.isoformat(),
                'missing_assignment_count': missing_count,
                'reason': f"{assignment.title} is still missing after the due date.",
            }
        )
    return events


def notification_targets(db: Session, event: dict[str, Any]) -> list[dict[str, Any]]:
    student_message = student_message_for(event)
    targets = [
        {
            'recipient_type': 'student',
            'recipient_id': event['student_email'],
            'recipient_name': event['student_name'],
            'channel': 'email',
            'subject': subject_for(event),
            'message': student_message,
        }
    ]
    if event.get('student_phone'):
        targets.append(
            {
                'recipient_type': 'student',
                'recipient_id': str(event['student_phone']),
                'recipient_name': event['student_name'],
                'channel': 'whatsapp',
                'subject': subject_for(event),
                'message': student_message,
            }
        )

    if event['severity'] == 'critical':
        targets.extend(critical_escalation_targets(db, event))
    return targets


def critical_escalation_targets(db: Session, event: dict[str, Any]) -> list[dict[str, Any]]:
    student = db.get(Student, event['student_id'])
    targets: list[dict[str, Any]] = []
    parent_email = (student.metadata_json or {}).get('parent_email') if student else None
    parent_phone = (student.metadata_json or {}).get('parent_phone') if student else None
    escalation_message = escalation_message_for(event)

    if parent_email:
        targets.append(
            {
                'recipient_type': 'parent',
                'recipient_id': str(parent_email),
                'recipient_name': 'Parent/Guardian',
                'channel': 'email',
                'subject': f"Critical TFI alert: {event['student_name']}",
                'message': escalation_message,
            }
        )
    if parent_phone:
        targets.append(
            {
                'recipient_type': 'parent',
                'recipient_id': str(parent_phone),
                'recipient_name': 'Parent/Guardian',
                'channel': 'whatsapp',
                'subject': f"Critical TFI alert: {event['student_name']}",
                'message': escalation_message,
            }
        )

    mentor_uid = student.batch.mentor_uid if student and student.batch else None
    mentor = db.get(User, mentor_uid) if mentor_uid else None
    if mentor and mentor.email:
        targets.append(
            {
                'recipient_type': 'mentor',
                'recipient_id': mentor.email,
                'recipient_name': mentor.name or mentor.email,
                'channel': 'email',
                'subject': f"Critical intervention needed: {event['student_name']}",
                'message': escalation_message,
            }
        )
    return targets


def student_message_for(event: dict[str, Any]) -> str:
    if event['event_type'] == 'missed_attendance':
        return (
            f"Hi {event['student_name']}, we noticed you missed or had very low attendance in "
            f"{event['session_title']} on {event['session_date']} ({event['attendance_percentage']}%). "
            "Please reply with your reason and connect with your mentor if you need support."
        )
    return (
        f"Hi {event['student_name']}, your assignment '{event['assignment_title']}' is still pending. "
        "Please submit it as soon as possible or reply with the blocker so your mentor can help."
    )


def escalation_message_for(event: dict[str, Any]) -> str:
    return (
        f"Critical TFI intervention alert for {event['student_name']} ({event['batch_name']}): "
        f"{event['reason']} Recommended action: mentor follow-up within 24 hours and response tracking."
    )


def subject_for(event: dict[str, Any]) -> str:
    if event['event_type'] == 'missed_attendance':
        return f"TFI attendance reminder: {event['session_title']}"
    return f"TFI assignment reminder: {event['assignment_title']}"


def existing_notification(db: Session, event_key: str, channel: str, recipient_id: str) -> Notification | None:
    notifications = db.scalars(
        select(Notification).where(Notification.channel == channel, Notification.recipient_id == recipient_id)
    ).all()
    for notification in notifications:
        if notification.payload.get('event_key') == event_key:
            return notification
    return None


def deliver_notification(notification: Notification) -> None:
    try:
        if notification.channel == 'email':
            if not settings.resend_api_key or not settings.resend_from_email:
                notification.status = 'queued'
                notification.payload = {**notification.payload, 'delivery_note': 'Resend credentials are not configured'}
                return
            response = send_email(
                notification.recipient_id,
                notification.payload['subject'],
                f"<p>{notification.payload['message']}</p>",
                settings.resend_api_key,
            )
        elif notification.channel == 'whatsapp':
            if not settings.whatsapp_api_token or not settings.whatsapp_phone_number_id:
                notification.status = 'queued'
                notification.payload = {**notification.payload, 'delivery_note': 'WhatsApp credentials are not configured'}
                return
            response = send_whatsapp(notification.payload['message'], notification.recipient_id, settings.whatsapp_api_token)
        else:
            notification.status = 'queued'
            notification.payload = {**notification.payload, 'delivery_note': f"Unsupported channel: {notification.channel}"}
            return
        notification.status = 'sent'
        notification.sent_at = datetime.now(timezone.utc)
        notification.payload = {**notification.payload, 'provider_response': response}
    except Exception as exc:
        notification.status = 'failed'
        notification.payload = {**notification.payload, 'delivery_error': str(exc)}


def serialize_notification(notification: Notification) -> dict[str, Any]:
    return {
        'id': notification.id,
        'recipient_type': notification.recipient_type,
        'recipient_id': notification.recipient_id,
        'channel': notification.channel,
        'template': notification.template,
        'status': notification.status,
        'response_status': notification.response_status,
        'payload': notification.payload,
        'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
        'responded_at': notification.responded_at.isoformat() if notification.responded_at else None,
        'created_at': notification.created_at.isoformat() if notification.created_at else None,
    }
