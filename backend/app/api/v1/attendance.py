from datetime import date, datetime
import hashlib
import re
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
import pandas as pd
import io
import math
from sqlalchemy import or_, select, func
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
    'student_name': {'student_name', 'student name', 'name', 'full name', 'participant name', 'participant', 'user name', 'name (original name)'},
    'registration_number': {'registration_number', 'registration number', 'registration', 'reg no', 'reg id', 'roll no', 'roll number', 'student id', 'user id'},
    'email': {'email', 'email address', 'participant email', 'user email', 'student email'},
    'join_time': {'join_time', 'join time', 'joined at', 'start time', 'first join', 'first joined', 'join timestamp', 'join date time'},
    'leave_time': {'leave_time', 'leave time', 'left at', 'end time', 'last leave', 'last left', 'leave timestamp', 'leave date time'},
    'duration_minutes': {'duration_minutes', 'duration minutes', 'total duration (minutes)', 'total duration', 'duration', 'time in session', 'minutes'},
}


class AttendanceImportResponse(BaseModel):
    records: list[dict[str, Any]]
    summary: dict[str, int]
    quality: dict[str, float | int]
    session_id: int
    import_hash: str


def load_and_detect_header(content: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith('.csv'):
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('latin1')
            except Exception:
                text = ""
        
        lines = text.splitlines()
        header_idx = None
        for i, line in enumerate(lines[:10]):
            lower_line = line.lower()
            if 'name (original name)' in lower_line or ('name' in lower_line and 'email' in lower_line):
                header_idx = i
                break
        
        if header_idx is not None:
            df = pd.read_csv(io.BytesIO(content), skiprows=header_idx)
        else:
            df = pd.read_csv(io.BytesIO(content))
    else:
        df_raw = pd.read_excel(io.BytesIO(content), header=None)
        header_idx = None
        for i in range(min(len(df_raw), 10)):
            row_values = [str(val).lower() for val in df_raw.iloc[i].values if pd.notna(val)]
            row_str = ' '.join(row_values)
            if 'name (original name)' in row_str or ('name' in row_str and 'email' in row_str):
                header_idx = i
                break
        
        if header_idx is not None:
            df = pd.read_excel(io.BytesIO(content), skiprows=header_idx)
        else:
            df = pd.read_excel(io.BytesIO(content))
            
    return df


def parse_student_name_and_reg(raw_name: str) -> tuple[str, str | None]:
    if not raw_name or pd.isna(raw_name):
        return "", None
        
    name_str = str(raw_name).strip()
    
    # 2 digits + 2 letters + 1 digit/letter + 1 letter + 4 digits/letters
    reg_pattern = r'(?:^|[^a-zA-Z0-9])(\d{2}\s*[a-zA-Z]{2}\s*\d\s*[a-zA-Z]\s*\d{2}\s*[a-zA-Z0-9]{2})(?:$|[^a-zA-Z0-9])'
    match = re.search(reg_pattern, name_str)
    
    if match:
        reg_no = match.group(1)
        reg_no_clean = re.sub(r'\s+', '', reg_no).upper()
        
        start_idx, end_idx = match.span(1)
        name_part = name_str[:start_idx] + " " + name_str[end_idx:]
        name_part = re.sub(r'[\-_()\[\]_]+', ' ', name_part)
        name_part = re.sub(r'\s+', ' ', name_part).strip()
        
        if not name_part:
            name_part = reg_no_clean
            
        return name_part, reg_no_clean
    
    # Fallback to other alphanumeric formats like L25CSC068 or similar 9-character code
    fallback_pattern = r'(?:^|[^a-zA-Z0-9])([a-zA-Z]\d{2}[a-zA-Z]{3}\d{3})(?:$|[^a-zA-Z0-9])'
    match_fallback = re.search(fallback_pattern, name_str)
    if match_fallback:
        reg_no_clean = match_fallback.group(1).upper()
        start_idx, end_idx = match_fallback.span(1)
        name_part = name_str[:start_idx] + " " + name_str[end_idx:]
        name_part = re.sub(r'[\-_()\[\]_]+', ' ', name_part)
        name_part = re.sub(r'\s+', ' ', name_part).strip()
        if not name_part:
            name_part = reg_no_clean
        return name_part, reg_no_clean

    return name_str, None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = {str(column).strip().lower().replace('_', ' '): column for column in df.columns}
    rename_map = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_columns:
                rename_map[normalized_columns[alias]] = canonical
                break

    df = df.rename(columns=rename_map)
    
    # Required: student_name
    if 'student_name' not in df.columns:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required student name column. Available columns: {', '.join(df.columns)}",
        )
        
    # Required: either duration_minutes OR both join_time and leave_time
    has_duration = 'duration_minutes' in df.columns
    has_times = 'join_time' in df.columns and 'leave_time' in df.columns
    if not has_duration and not has_times:
        raise HTTPException(
            status_code=422,
            detail=f"Missing duration/time columns. Must have either a duration column or both join/leave time columns. Available columns: {', '.join(df.columns)}",
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
        df = load_and_detect_header(content, filename)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f'Unable to parse file: {exc}')

    df = normalize_columns(df)
    df = df.dropna(how='all').copy()
    if df.empty:
        raise HTTPException(status_code=422, detail='Attendance file does not contain any usable rows')

    # Parse and clean name and registration number
    parsed_names = []
    parsed_regs = []
    for val in df['student_name']:
        c_name, r_no = parse_student_name_and_reg(val)
        parsed_names.append(c_name)
        parsed_regs.append(r_no)
        
    df['student_name'] = parsed_names
    if 'registration_number' not in df.columns:
        df['registration_number'] = parsed_regs
    else:
        df['registration_number'] = df['registration_number'].fillna(pd.Series(parsed_regs)).astype(str).str.strip()
        cleaned_regs = []
        for reg in df['registration_number']:
            if pd.isna(reg) or reg.lower() == 'nan' or not reg.strip():
                cleaned_regs.append(None)
            else:
                cleaned_regs.append(re.sub(r'\s+', '', reg).upper())
        df['registration_number'] = cleaned_regs

    if 'email' not in df.columns:
        df['email'] = None
    else:
        df['email'] = df['email'].astype(str).str.strip().str.lower()
        df['email'] = df['email'].apply(lambda x: x if (pd.notna(x) and '@' in x) else None)

    if 'join_time' in df.columns and 'leave_time' in df.columns:
        join_time = pd.to_datetime(df['join_time'], errors='coerce')
        leave_time = pd.to_datetime(df['leave_time'], errors='coerce')
        df['join_time'] = join_time
        df['leave_time'] = leave_time
        df['duration_minutes'] = (
            leave_time - join_time
        ).dt.total_seconds() / 60
    elif 'duration_minutes' in df.columns:
        df['duration_minutes'] = pd.to_numeric(df['duration_minutes'], errors='coerce')
        df['join_time'] = None
        df['leave_time'] = None
        
    df['duration_minutes'] = df['duration_minutes'].fillna(0).clip(lower=0)
    
    df['dedup_key'] = df['email'].fillna(df['registration_number'].fillna(df['student_name']))
    df = df.sort_values(['dedup_key', 'duration_minutes']).drop_duplicates(subset=['dedup_key'], keep='last')

    required_minutes = max(settings.attendance_session_minutes, 1)
    df['attendance_percentage'] = (df['duration_minutes'] / required_minutes * 100).clip(upper=100).round(1)
    df['late_joining'] = df['duration_minutes'] < required_minutes
    df['early_leaving'] = df['duration_minutes'] < required_minutes * 0.83
    df['engagement_score'] = (df['attendance_percentage'] * 0.8 + (~df['late_joining']).astype(int) * 10 + (~df['early_leaving']).astype(int) * 10).round(1)
    df['attendance_status'] = df['duration_minutes'].apply(
        lambda value: 'Full' if value >= required_minutes else 'Partial' if value >= required_minutes * 0.55 else 'Absent'
    )

    records = clean_records(df.to_dict(orient='records'))

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

        student_records = {}
        for record in records:
            raw_name = record.get('student_name') or ''
            email = record.get('email')
            reg_no = record.get('registration_number')
            
            student = None
            if reg_no:
                student = db.scalar(select(Student).where(Student.registration_number == reg_no))
            if not student and email:
                student = db.scalar(select(Student).where(Student.email == email))
            if not student:
                student = db.scalar(select(Student).where(func.lower(Student.full_name) == raw_name.lower()))
                
            if not student:
                if not reg_no:
                    name_hash = hashlib.md5(raw_name.encode('utf-8')).hexdigest()[:8].upper()
                    reg_no = f"TEMP-{name_hash}"
                    
                if not email:
                    email = f"{reg_no.lower()}@techofutureindia.com"
                    
                collision = db.scalar(select(Student).where(or_(Student.registration_number == reg_no, Student.email == email)))
                if collision:
                    student = collision
                else:
                    student = Student(
                        batch_id=batch.id,
                        registration_number=reg_no,
                        full_name=raw_name,
                        email=email,
                        domain=batch.domain,
                        enrollment_status='active',
                        metadata_json={},
                    )
                    db.add(student)
                    db.flush()
            else:
                student.batch_id = batch.id
                student.domain = batch.domain
                if raw_name and raw_name != reg_no:
                    student.full_name = raw_name
            
            student_id = student.id
            duration = float(record.get('duration_minutes') or 0)
            
            if student_id in student_records:
                student_records[student_id]['duration_minutes'] += duration
                if not student_records[student_id].get('join_time') and record.get('join_time'):
                    student_records[student_id]['join_time'] = record.get('join_time')
                if not student_records[student_id].get('leave_time') and record.get('leave_time'):
                    student_records[student_id]['leave_time'] = record.get('leave_time')
            else:
                record['student_id'] = student_id
                student_records[student_id] = record

        # Recalculate and persist records
        final_records = []
        for student_id, rec in student_records.items():
            duration = rec['duration_minutes']
            percentage = min(round(duration / required_minutes * 100, 1), 100.0)
            late_joining = duration < required_minutes
            early_leaving = duration < required_minutes * 0.83
            engagement_score = round(percentage * 0.8 + (0 if late_joining else 10) + (0 if early_leaving else 10), 1)
            status = 'Full' if duration >= required_minutes else 'Partial' if duration >= required_minutes * 0.55 else 'Absent'
            
            rec['attendance_percentage'] = percentage
            rec['late_joining'] = late_joining
            rec['early_leaving'] = early_leaving
            rec['engagement_score'] = engagement_score
            rec['attendance_status'] = status
            final_records.append(rec)

            db.add(
                AttendanceRecord(
                    session_id=attendance_session.id,
                    student_id=student_id,
                    join_time=to_python_datetime(rec.get('join_time')),
                    leave_time=to_python_datetime(rec.get('leave_time')),
                    duration_minutes=duration,
                    attendance_percentage=percentage,
                    status=status,
                    late_joining=late_joining,
                    early_leaving=early_leaving,
                    engagement_score=engagement_score,
                    raw_payload=rec,
                )
            )

        summary = compute_attendance_summary(final_records)
        quality = compute_attendance_quality(final_records)

        db.add(
            AuditLog(
                actor_uid=actor_uid,
                action='attendance.imported',
                entity_type='attendance_session',
                entity_id=str(attendance_session.id),
                metadata_json={'record_count': len(final_records), 'source_file': filename, 'severity': 'Low'},
            )
        )
        db.commit()
        run_auto_nudges(db, actor_uid=actor_uid, attendance_session_id=attendance_session.id)
    except Exception:
        db.rollback()
        raise

    return {
        'records': final_records,
        'summary': summary,
        'quality': quality,
        'session_id': attendance_session.id,
        'import_hash': import_hash,
    }
