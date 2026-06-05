"""add notification response tracking

Revision ID: 20260605_0004
Revises: 20260605_0003
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = '20260605_0004'
down_revision = '20260605_0003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notifications', sa.Column('response_status', sa.String(), nullable=False, server_default='pending'))
    op.add_column('notifications', sa.Column('response_payload', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('notifications', sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_notifications_response_status'), 'notifications', ['response_status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_notifications_response_status'), table_name='notifications')
    op.drop_column('notifications', 'responded_at')
    op.drop_column('notifications', 'response_payload')
    op.drop_column('notifications', 'response_status')
