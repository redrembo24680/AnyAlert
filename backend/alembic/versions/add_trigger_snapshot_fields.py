"""Add missing trigger snapshot fields to platform tables

Revision ID: add_trigger_snapshot_fields
Revises: remove_trigger_columns
Create Date: 2026-05-04 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_trigger_snapshot_fields'
down_revision = 'remove_trigger_columns'
branch_labels = None
depends_on = None


def _existing_columns(table_name: str) -> set[str]:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return {column['name'] for column in inspector.get_columns(table_name)}


def _add_missing_columns(table_name: str, columns: list[sa.Column]) -> None:
    existing = _existing_columns(table_name)
    for column in columns:
        if column.name not in existing:
            op.add_column(table_name, column)


def upgrade() -> None:
    _add_missing_columns(
        'rozetka_tracker_data',
        [
            sa.Column('last_reviews_count', sa.Integer(), nullable=True),
            sa.Column('last_views', sa.Integer(), nullable=True),
        ],
    )
    _add_missing_columns(
        'olx_tracker_data',
        [sa.Column('last_views', sa.Integer(), nullable=True)],
    )
    _add_missing_columns(
        'prom_tracker_data',
        [sa.Column('last_reviews_count', sa.Integer(), nullable=True)],
    )
    _add_missing_columns(
        'allo_tracker_data',
        [sa.Column('last_views', sa.Integer(), nullable=True)],
    )
    _add_missing_columns(
        'comfy_tracker_data',
        [sa.Column('last_views', sa.Integer(), nullable=True)],
    )
    _add_missing_columns(
        'foxtrot_tracker_data',
        [sa.Column('last_views', sa.Integer(), nullable=True)],
    )
    _add_missing_columns(
        'comfy_offers_data',
        [
            sa.Column('last_reviews_count', sa.Integer(), nullable=True),
            sa.Column('last_views', sa.Integer(), nullable=True),
        ],
    )
    _add_missing_columns(
        'foxtrot_offers_data',
        [
            sa.Column('last_reviews_count', sa.Integer(), nullable=True),
            sa.Column('last_views', sa.Integer(), nullable=True),
        ],
    )


def downgrade() -> None:
    op.drop_column('foxtrot_offers_data', 'last_views')
    op.drop_column('foxtrot_offers_data', 'last_reviews_count')
    op.drop_column('comfy_offers_data', 'last_views')
    op.drop_column('comfy_offers_data', 'last_reviews_count')
    op.drop_column('foxtrot_tracker_data', 'last_views')
    op.drop_column('comfy_tracker_data', 'last_views')
    op.drop_column('allo_tracker_data', 'last_views')
    op.drop_column('prom_tracker_data', 'last_reviews_count')
    op.drop_column('olx_tracker_data', 'last_views')
    op.drop_column('rozetka_tracker_data', 'last_views')
    op.drop_column('rozetka_tracker_data', 'last_reviews_count')
