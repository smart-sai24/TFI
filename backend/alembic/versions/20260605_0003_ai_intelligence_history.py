"""add ai intelligence history tables

Revision ID: 20260605_0003
Revises: 20260604_0002
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = '20260605_0003'
down_revision = '20260604_0002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'attendance_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('prediction_window', sa.String(), nullable=False),
        sa.Column('current_attendance', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('forecast', sa.JSON(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_attendance_predictions_created_at'), 'attendance_predictions', ['created_at'], unique=False)
    op.create_index(op.f('ix_attendance_predictions_risk_level'), 'attendance_predictions', ['risk_level'], unique=False)
    op.create_index(op.f('ix_attendance_predictions_student_id'), 'attendance_predictions', ['student_id'], unique=False)

    op.create_table(
        'performance_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('current_score', sa.Float(), nullable=False),
        sa.Column('predicted_final_score', sa.Float(), nullable=False),
        sa.Column('predicted_category', sa.String(), nullable=False),
        sa.Column('certificate_probability', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('drivers', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_performance_predictions_created_at'), 'performance_predictions', ['created_at'], unique=False)
    op.create_index(op.f('ix_performance_predictions_predicted_category'), 'performance_predictions', ['predicted_category'], unique=False)
    op.create_index(op.f('ix_performance_predictions_student_id'), 'performance_predictions', ['student_id'], unique=False)

    op.create_table(
        'risk_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_types', sa.JSON(), nullable=False),
        sa.Column('reasoning', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_risk_predictions_created_at'), 'risk_predictions', ['created_at'], unique=False)
    op.create_index(op.f('ix_risk_predictions_risk_level'), 'risk_predictions', ['risk_level'], unique=False)
    op.create_index(op.f('ix_risk_predictions_student_id'), 'risk_predictions', ['student_id'], unique=False)

    op.create_table(
        'ai_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('output_format', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('generated_by_uid', sa.String(), nullable=True),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['generated_by_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_reports_created_at'), 'ai_reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_reports_report_type'), 'ai_reports', ['report_type'], unique=False)
    op.create_index(op.f('ix_ai_reports_status'), 'ai_reports', ['status'], unique=False)

    op.create_table(
        'ai_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('audience_role', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_insights_audience_role'), 'ai_insights', ['audience_role'], unique=False)
    op.create_index(op.f('ix_ai_insights_created_at'), 'ai_insights', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_insights_severity'), 'ai_insights', ['severity'], unique=False)

    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_uid', sa.String(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('response', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_uid'], ['users.uid']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_conversations_created_at'), 'ai_conversations', ['created_at'], unique=False)
    op.create_index(op.f('ix_ai_conversations_user_uid'), 'ai_conversations', ['user_uid'], unique=False)

    op.create_table(
        'assignment_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=False),
        sa.Column('improvements', sa.JSON(), nullable=False),
        sa.Column('risk_flags', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignment_evaluations_created_at'), 'assignment_evaluations', ['created_at'], unique=False)
    op.create_index(op.f('ix_assignment_evaluations_grade'), 'assignment_evaluations', ['grade'], unique=False)
    op.create_index(op.f('ix_assignment_evaluations_student_id'), 'assignment_evaluations', ['student_id'], unique=False)
    op.create_index(op.f('ix_assignment_evaluations_submission_id'), 'assignment_evaluations', ['submission_id'], unique=False)


def downgrade():
    for table in [
        'assignment_evaluations',
        'ai_conversations',
        'ai_insights',
        'ai_reports',
        'risk_predictions',
        'performance_predictions',
        'attendance_predictions',
    ]:
        op.drop_table(table)
