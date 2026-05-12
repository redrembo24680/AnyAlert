"""add extended trigger fields to rozetka_tracker_data

Revision ID: 202605090001
Revises: 202605020001
Create Date: 2026-05-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202605090001'
down_revision = '202505090001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('rozetka_tracker_data', sa.Column('last_cashback_amount', sa.Float(), nullable=True))
    op.add_column('rozetka_tracker_data', sa.Column('last_trade_in_available', sa.Boolean(), nullable=True))
    op.add_column('rozetka_tracker_data', sa.Column('last_credit_available', sa.Boolean(), nullable=True))
    op.add_column('rozetka_tracker_data', sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True))
    op.add_column('rozetka_tracker_data', sa.Column('last_personal_price_available', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('rozetka_tracker_data', 'last_personal_price_available')
    op.drop_column('rozetka_tracker_data', 'last_gift_offer_available')
    op.drop_column('rozetka_tracker_data', 'last_credit_available')
    op.drop_column('rozetka_tracker_data', 'last_trade_in_available')
    op.drop_column('rozetka_tracker_data', 'last_cashback_amount')
