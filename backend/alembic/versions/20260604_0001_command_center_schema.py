"""command center operations schema

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = '20260604_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roles',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('name'),
    )
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),
    )
    op.create_table(
        'role_permissions',
        sa.Column('role_name', sa.String(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_name'], ['roles.name'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_name', 'permission_id'),
    )
    op.create_table(
        'users',
        sa.Column('uid', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['role'], ['roles.name']),
        sa.PrimaryKeyConstraint('uid'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_uid'), 'users', ['uid'], unique=False)
    op.create_table(
        'batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('starts_on', sa.Date(), nullable=True),
        sa.Column('ends_on', sa.Date(), nullable=True),
        sa.Column('mentor_uid', sa.String(), nullable=True),
        sa.Column('host_uid', sa.String(), nullable=True),
        sa.Column('coordinator_uid', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['coordinator_uid'], ['users.uid']),
        sa.ForeignKeyConstraint(['host_uid'], ['users.uid']),
        sa.ForeignKeyConstraint(['mentor_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_batches_name'), 'batches', ['name'], unique=True)
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('registration_number', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('enrollment_status', sa.String(), nullable=False),
        sa.Column('joined_on', sa.Date(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_students_batch_id'), 'students', ['batch_id'], unique=False)
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)
    op.create_index(op.f('ix_students_full_name'), 'students', ['full_name'], unique=False)
    op.create_index(op.f('ix_students_registration_number'), 'students', ['registration_number'], unique=True)
    op.create_table(
        'attendance_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('required_minutes', sa.Integer(), nullable=False),
        sa.Column('source_file', sa.String(), nullable=True),
        sa.Column('import_hash', sa.String(), nullable=True),
        sa.Column('created_by_uid', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_attendance_sessions_batch_id'), 'attendance_sessions', ['batch_id'], unique=False)
    op.create_index(op.f('ix_attendance_sessions_import_hash'), 'attendance_sessions', ['import_hash'], unique=False)
    op.create_index(op.f('ix_attendance_sessions_session_date'), 'attendance_sessions', ['session_date'], unique=False)
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assignment_type', sa.String(), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('created_by_uid', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignments_batch_id'), 'assignments', ['batch_id'], unique=False)
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('join_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('leave_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Float(), nullable=False),
        sa.Column('attendance_percentage', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('late_joining', sa.Boolean(), nullable=False),
        sa.Column('early_leaving', sa.Boolean(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['attendance_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'student_id', name='uq_attendance_record_session_student'),
    )
    op.create_index('ix_attendance_student_session', 'attendance_records', ['student_id', 'session_id'], unique=False)
    op.create_index(op.f('ix_attendance_records_session_id'), 'attendance_records', ['session_id'], unique=False)
    op.create_index(op.f('ix_attendance_records_student_id'), 'attendance_records', ['student_id'], unique=False)
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('is_late', sa.Boolean(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('ai_evaluation', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'student_id', name='uq_submission_assignment_student'),
    )
    op.create_index(op.f('ix_submissions_assignment_id'), 'submissions', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_submissions_student_id'), 'submissions', ['student_id'], unique=False)
    op.create_table(
        'performance_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('score_date', sa.Date(), nullable=False),
        sa.Column('attendance_score', sa.Float(), nullable=False),
        sa.Column('assignment_score', sa.Float(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('batch_rank', sa.Integer(), nullable=True),
        sa.Column('overall_rank', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('trend', sa.String(), nullable=False),
        sa.CheckConstraint('overall_score >= 0 AND overall_score <= 100', name='ck_performance_overall_score'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_performance_scores_score_date'), 'performance_scores', ['score_date'], unique=False)
    op.create_index(op.f('ix_performance_scores_student_id'), 'performance_scores', ['student_id'], unique=False)
    op.create_table(
        'risk_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('predicted_completion_probability', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id'),
    )
    op.create_index(op.f('ix_risk_profiles_risk_level'), 'risk_profiles', ['risk_level'], unique=False)
    op.create_table(
        'certificates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('eligibility_score', sa.Float(), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('certificate_url', sa.String(), nullable=True),
        sa.Column('requirements_snapshot', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_certificates_status'), 'certificates', ['status'], unique=False)
    op.create_index(op.f('ix_certificates_student_id'), 'certificates', ['student_id'], unique=False)
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_type', sa.String(), nullable=False),
        sa.Column('recipient_id', sa.String(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('template', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_recipient_id'), 'notifications', ['recipient_id'], unique=False)
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_uid', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['actor_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_uid'), 'audit_logs', ['actor_uid'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('generated_by_uid', sa.String(), nullable=True),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('metrics_snapshot', sa.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['generated_by_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reports_report_type'), 'reports', ['report_type'], unique=False)


def downgrade():
    for table in [
        'reports',
        'audit_logs',
        'notifications',
        'certificates',
        'risk_profiles',
        'performance_scores',
        'submissions',
        'attendance_records',
        'assignments',
        'attendance_sessions',
        'students',
        'batches',
        'users',
        'role_permissions',
        'permissions',
        'roles',
    ]:
        op.drop_table(table)
