"""add assignment authenticity checks

Revision ID: 20260605_0005
Revises: 20260605_0004
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = '20260605_0005'
down_revision = '20260605_0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'assignment_authenticity_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=True),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('ai_generated_risk', sa.Float(), nullable=False),
        sa.Column('code_quality_score', sa.Float(), nullable=False),
        sa.Column('github_activity_score', sa.Float(), nullable=False),
        sa.Column('originality_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('matched_submission_id', sa.Integer(), nullable=True),
        sa.Column('fingerprint', sa.JSON(), nullable=False),
        sa.Column('github_evidence', sa.JSON(), nullable=False),
        sa.Column('findings', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assignment_authenticity_checks_assignment_id'), 'assignment_authenticity_checks', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_assignment_authenticity_checks_content_hash'), 'assignment_authenticity_checks', ['content_hash'], unique=False)
    op.create_index(op.f('ix_assignment_authenticity_checks_created_at'), 'assignment_authenticity_checks', ['created_at'], unique=False)
    op.create_index(op.f('ix_assignment_authenticity_checks_originality_score'), 'assignment_authenticity_checks', ['originality_score'], unique=False)
    op.create_index(op.f('ix_assignment_authenticity_checks_risk_level'), 'assignment_authenticity_checks', ['risk_level'], unique=False)
    op.create_index(op.f('ix_assignment_authenticity_checks_student_id'), 'assignment_authenticity_checks', ['student_id'], unique=False)
    op.create_index(op.f('ix_assignment_authenticity_checks_submission_id'), 'assignment_authenticity_checks', ['submission_id'], unique=False)


def downgrade():
    op.drop_table('assignment_authenticity_checks')
