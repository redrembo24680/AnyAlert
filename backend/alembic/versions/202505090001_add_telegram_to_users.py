"""add telegram fields to users

Revision ID: 202505090001
Revises: add_trigger_snapshot_fields
Create Date: 2025-05-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "202505090001"
down_revision = "add_trigger_snapshot_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("telegram_username", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_users_telegram_id", "users", ["telegram_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_column("users", "telegram_username")
    op.drop_column("users", "telegram_id")
