"""add user password hash

Revision ID: 20260604_0002
Revises: 20260604_0001
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = '20260604_0002'
down_revision = '20260604_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))


def downgrade():
    op.drop_column('users', 'password_hash')
