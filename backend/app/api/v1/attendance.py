from datetime import date, datetime
import hashlib
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
import pandas as pd
import io
import math
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.operations import AttendanceRecord, AttendanceSession, AuditLog, Batch, Student
from app.services.analytics import compute_attendance_quality, compute_attendance_summary
from app.services.nudges import run_auto_nudges

router = APIRouter()


COLUMN_ALIASES = {
    'student_name': {'student_name', 'student name', 'name', 'full name', 'participant name', 'participant', 'user name'},
    'registration_number': {'registration_number', 'registration number', 'registration', 'reg no', 'reg id', 'roll no', 'roll number', 'student id', 'user id'},
    'email': {'email', 'email address', 'participant email', 'user email', 'student email'},
    'join_time': {'join_time', 'join time', 'joined at', 'start time', 'first join', 'first joined', 'join timestamp', 'join date time'},
    'leave_time': {'leave_time', 'leave time', 'left at', 'end time', 'last leave', 'last left', 'leave timestamp', 'leave date time'},
}


class AttendanceImportResponse(BaseModel):
    records: list[dict[str, Any]]
    summary: dict[str, int]
    quality: dict[str, float | int]
    session_id: int
    import_hash: str


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = {str(column).strip().lower().replace('_', ' '): column for column in df.columns}
    rename_map = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_columns:
                rename_map[normalized_columns[alias]] = canonical
                break

    df = df.rename(columns=rename_map)
    missing = set(COLUMN_ALIASES) - set(df.columns)
    if missing:
        available_columns = ', '.join(str(column) for column in df.columns)
        raise HTTPException(
            status_code=422,
            detail=f'Missing required attendance columns: {", ".join(sorted(missing))}. Available columns: {available_columns}',
        )
    return df


def clean_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned_records = []
    for record in records:
        cleaned = {}
        for key, value in record.items():
            if pd.isna(value):
                cleaned[key] = None
            elif hasattr(value, 'isoformat'):
                cleaned[key] = value.isoformat()
            elif isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
                cleaned[key] = None
            else:
                cleaned[key] = value
        cleaned_records.append(cleaned)
    return cleaned_records


def to_python_datetime(value: Any):
    if value is None or pd.isna(value):
        return None
    if hasattr(value, 'to_pydatetime'):
        return value.to_pydatetime()
    if hasattr(value, 'isoformat'):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


@router.post('/import', response_model=AttendanceImportResponse)
async def import_attendance(
    user: CurrentUser = require_permission('attendance:import'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    batch_name: str = Form(...),
    domain: str = Form('General'),
    session_title: str = Form(...),
    platform: str = Form('Zoom'),
    session_date: date = Form(...),
):
    allowed_types = {
        'text/csv',
        'application/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
    }
    filename = file.filename or ''
    if file.content_type not in allowed_types and not filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail='Unsupported file type')

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f'File exceeds {settings.max_upload_bytes} byte upload limit')

    import_hash = hashlib.sha256(
        content + f'{batch_name}|{session_title}|{platform}|{session_date}'.encode('utf-8')
    ).hexdigest()
    existing_session = db.scalar(select(AttendanceSession).where(AttendanceSession.import_hash == import_hash))
    if existing_session:
        raise HTTPException(status_code=409, detail='This attendance file has already been imported for the selected session')

    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f'Unable to parse file: {exc}')

    df = normalize_columns(df)
    df = df.dropna(how='all').copy()
    if df.empty:
        raise HTTPException(status_code=422, detail='Attendance file does not contain any usable rows')

    df['student_name'] = df['student_name'].astype(str).str.strip()
    df['registration_number'] = df['registration_number'].astype(str).str.strip()
    df['email'] = df['email'].astype(str).str.strip().str.lower()
    df = df[df['email'].str.contains('@', na=False)]
    if df.empty:
        raise HTTPException(status_code=422, detail='No rows contain a valid participant email address')

    join_time = pd.to_datetime(df['join_time'], errors='coerce')
    leave_time = pd.to_datetime(df['leave_time'], errors='coerce')
    df['join_time'] = join_time
    df['leave_time'] = leave_time
    df['duration_minutes'] = (
        leave_time - join_time
    ).dt.total_seconds() / 60
    df['duration_minutes'] = df['duration_minutes'].fillna(0).clip(lower=0)
    df = df.sort_values(['email', 'duration_minutes']).drop_duplicates(subset=['email'], keep='last')

    required_minutes = max(settings.attendance_session_minutes, 1)
    df['attendance_percentage'] = (df['duration_minutes'] / required_minutes * 100).clip(upper=100).round(1)
    df['late_joining'] = df['duration_minutes'] < required_minutes
    df['early_leaving'] = df['duration_minutes'] < required_minutes * 0.83
    df['engagement_score'] = (df['attendance_percentage'] * 0.8 + (~df['late_joining']).astype(int) * 10 + (~df['early_leaving']).astype(int) * 10).round(1)
    df['attendance_status'] = df['duration_minutes'].apply(
        lambda value: 'Full' if value >= required_minutes else 'Partial' if value >= required_minutes * 0.55 else 'Absent'
    )

    records = clean_records(df.to_dict(orient='records'))
    summary = compute_attendance_summary(records)
    quality = compute_attendance_quality(records)

    try:
        actor_uid = user.uid if db.get(User, user.uid) else None
        batch = db.scalar(select(Batch).where(Batch.name == batch_name.strip()))
        if not batch:
            batch = Batch(name=batch_name.strip(), domain=domain.strip() or 'General', status='active')
            db.add(batch)
            db.flush()

        attendance_session = AttendanceSession(
            batch_id=batch.id,
            title=session_title.strip(),
            platform=platform.strip() or 'Unknown',
            session_date=session_date,
            required_minutes=required_minutes,
            source_file=filename,
            import_hash=import_hash,
            created_by_uid=actor_uid,
        )
        db.add(attendance_session)
        db.flush()

        for record in records:
            student = db.scalar(
                select(Student).where(
                    or_(
                        Student.email == record['email'],
                        Student.registration_number == record['registration_number'],
                    )
                )
            )
            if not student:
                student = Student(
                    batch_id=batch.id,
                    registration_number=record['registration_number'],
                    full_name=record['student_name'],
                    email=record['email'],
                    domain=batch.domain,
                    enrollment_status='active',
                    metadata_json={},
                )
                db.add(student)
                db.flush()
            else:
                student.batch_id = batch.id
                student.full_name = record['student_name'] or student.full_name
                student.domain = batch.domain

            db.add(
                AttendanceRecord(
                    session_id=attendance_session.id,
                    student_id=student.id,
                    join_time=to_python_datetime(record.get('join_time')),
                    leave_time=to_python_datetime(record.get('leave_time')),
                    duration_minutes=float(record['duration_minutes'] or 0),
                    attendance_percentage=float(record['attendance_percentage'] or 0),
                    status=record['attendance_status'],
                    late_joining=bool(record['late_joining']),
                    early_leaving=bool(record['early_leaving']),
                    engagement_score=float(record['engagement_score'] or 0),
                    raw_payload=record,
                )
            )

        db.add(
            AuditLog(
                actor_uid=actor_uid,
                action='attendance.imported',
                entity_type='attendance_session',
                entity_id=str(attendance_session.id),
                metadata_json={'record_count': len(records), 'source_file': filename, 'severity': 'Low'},
            )
        )
        db.commit()
        run_auto_nudges(db, actor_uid=actor_uid, attendance_session_id=attendance_session.id)
    except Exception:
        db.rollback()
        raise

    return {
        'records': records,
        'summary': summary,
        'quality': quality,
        'session_id': attendance_session.id,
        'import_hash': import_hash,
    }
