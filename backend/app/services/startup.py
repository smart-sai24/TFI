from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


REQUIRED_TABLES = {
    'roles',
    'permissions',
    'role_permissions',
    'users',
    'batches',
    'students',
    'attendance_sessions',
    'attendance_records',
    'assignments',
    'submissions',
    'performance_scores',
    'risk_profiles',
    'certificates',
    'notifications',
    'audit_logs',
    'reports',
    'attendance_predictions',
    'performance_predictions',
    'risk_predictions',
    'ai_reports',
    'ai_insights',
    'ai_conversations',
    'assignment_evaluations',
    'assignment_authenticity_checks',
}


def assert_database_ready(db: Session) -> None:
    try:
        inspector = inspect(db.bind)
        existing_tables = set(inspector.get_table_names())
    except OperationalError as exc:
        raise RuntimeError(
            'PostgreSQL is not reachable. Start the database first, then run migrations. '
            'For local Windows development run: docker compose up -d postgres; cd backend; alembic upgrade head'
        ) from exc

    missing_tables = sorted(REQUIRED_TABLES - existing_tables)
    if missing_tables:
        raise RuntimeError(
            'Database schema is not migrated. Missing tables: '
            f'{", ".join(missing_tables)}. Run: cd backend; alembic upgrade head'
        )
