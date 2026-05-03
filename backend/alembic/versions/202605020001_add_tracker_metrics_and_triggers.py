"""add tracker metrics and trigger fields

Revision ID: 202605020001
Revises: 48471a851d9c
Create Date: 2026-05-02 22:35:00.000000

"""
# ruff: noqa: I001

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202605020001'
down_revision = '48471a851d9c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('product_trackers', sa.Column(
        'last_old_price', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_discount_percent', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_rating', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_views', sa.Integer(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_reviews_count', sa.Integer(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_cashback_amount', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_trade_in_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_credit_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_color', sa.String(length=100), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_memory_variant', sa.String(length=100), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_delivery_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_pickup_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_personal_price_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_gift_offer_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column(
        'last_availability', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('product_trackers', 'last_availability')
    op.drop_column('product_trackers', 'last_memory_variant')
    op.drop_column('product_trackers', 'last_color')
    op.drop_column('product_trackers', 'last_credit_available')
    op.drop_column('product_trackers', 'last_trade_in_available')
    op.drop_column('product_trackers', 'last_cashback_amount')
    op.drop_column('product_trackers', 'last_reviews_count')
    op.drop_column('product_trackers', 'last_pickup_available')
    op.drop_column('product_trackers', 'last_gift_offer_available')
    op.drop_column('product_trackers', 'last_personal_price_available')
    op.drop_column('product_trackers', 'last_delivery_available')
    op.drop_column('product_trackers', 'last_views')
    op.drop_column('product_trackers', 'last_rating')
    op.drop_column('product_trackers', 'last_discount_percent')
    op.drop_column('product_trackers', 'last_old_price')
