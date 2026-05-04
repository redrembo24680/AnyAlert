"""Remove trigger columns from product_trackers

Revision ID: remove_trigger_columns
Revises: add_tracker_triggers
Create Date: 2026-05-03 18:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_trigger_columns'
down_revision = 'add_tracker_triggers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop trigger_type and trigger_value from product_trackers
    # (they are now in product_tracker_triggers table)
    op.drop_column('product_trackers', 'trigger_type')
    op.drop_column('product_trackers', 'trigger_value')


def downgrade() -> None:
    op.add_column('product_trackers',
        sa.Column('trigger_type', sa.String(50), nullable=False, server_default='price_below')
    )
    op.add_column('product_trackers',
        sa.Column('trigger_value', sa.Float(), nullable=True)
    )
