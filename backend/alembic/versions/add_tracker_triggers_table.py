"""Add tracker triggers table

Revision ID: add_tracker_triggers
Revises: normalize_platform_data
Create Date: 2026-05-03 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tracker_triggers'
down_revision = 'normalize_platform_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('product_tracker_triggers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tracker_id', sa.Integer(), nullable=False),
    sa.Column('trigger_type', sa.String(50), nullable=False),
    sa.Column('trigger_value', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.Index('ix_product_tracker_triggers_tracker_id', 'tracker_id')
    )


def downgrade() -> None:
    op.drop_table('product_tracker_triggers')
