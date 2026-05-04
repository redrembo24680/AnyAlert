"""Normalize platform data - split into separate tables

Revision ID: normalize_platform_data
Revises: 202605020001
Create Date: 2026-05-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'normalize_platform_data'
down_revision = '202605020001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection to check which columns exist
    conn = op.get_bind()
    
    # List of columns from the old structure that might exist
    columns_to_check = [
        'title', 'last_price', 'last_old_price', 'last_discount_percent',
        'last_rating', 'last_views', 'last_reviews_count', 'last_cashback_amount',
        'last_trade_in_available', 'last_credit_available', 'last_color',
        'last_memory_variant', 'last_delivery_available', 'last_pickup_available',
        'last_personal_price_available', 'last_gift_offer_available',
        'last_availability', 'last_status', 'last_checked_at'
    ]
    
    # Get existing columns
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('product_trackers')}
    
    # Drop only columns that exist
    for col_name in columns_to_check:
        if col_name in existing_columns:
            op.drop_column('product_trackers', col_name)

    # Create Rozetka tracker data table
    op.create_table('rozetka_tracker_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_status', sa.String(length=100), nullable=True),
        sa.Column('last_availability', sa.Boolean(), nullable=True),
        sa.Column('last_rating', sa.Float(), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id')
    )
    op.create_index(op.f('ix_rozetka_tracker_data_id'), 'rozetka_tracker_data', ['id'], unique=False)

    # Create OLX tracker data table
    op.create_table('olx_tracker_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_status', sa.String(length=100), nullable=True),
        sa.Column('last_availability', sa.Boolean(), nullable=True),
        sa.Column('last_rating', sa.Float(), nullable=True),
        sa.Column('last_reviews_count', sa.Integer(), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id')
    )
    op.create_index(op.f('ix_olx_tracker_data_id'), 'olx_tracker_data', ['id'], unique=False)

    # Create PROM tracker data table
    op.create_table('prom_tracker_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_status', sa.String(length=100), nullable=True),
        sa.Column('last_availability', sa.Boolean(), nullable=True),
        sa.Column('last_rating', sa.Float(), nullable=True),
        sa.Column('last_views', sa.Integer(), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id')
    )
    op.create_index(op.f('ix_prom_tracker_data_id'), 'prom_tracker_data', ['id'], unique=False)

    # Create ALLO tracker data table
    op.create_table('allo_tracker_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_cashback_amount', sa.Float(), nullable=True),
        sa.Column('last_personal_price_available', sa.Boolean(), nullable=True),
        sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True),
        sa.Column('last_status', sa.String(length=100), nullable=True),
        sa.Column('last_availability', sa.Boolean(), nullable=True),
        sa.Column('last_rating', sa.Float(), nullable=True),
        sa.Column('last_reviews_count', sa.Integer(), nullable=True),
        sa.Column('last_trade_in_available', sa.Boolean(), nullable=True),
        sa.Column('last_credit_available', sa.Boolean(), nullable=True),
        sa.Column('last_delivery_available', sa.Boolean(), nullable=True),
        sa.Column('last_pickup_available', sa.Boolean(), nullable=True),
        sa.Column('last_color', sa.String(length=100), nullable=True),
        sa.Column('last_memory_variant', sa.String(length=100), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id')
    )
    op.create_index(op.f('ix_allo_tracker_data_id'), 'allo_tracker_data', ['id'], unique=False)

    # Create COMFY tracker data table
    op.create_table('comfy_tracker_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_cashback_amount', sa.Float(), nullable=True),
        sa.Column('last_personal_price_available', sa.Boolean(), nullable=True),
        sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True),
        sa.Column('last_status', sa.String(length=100), nullable=True),
        sa.Column('last_availability', sa.Boolean(), nullable=True),
        sa.Column('last_rating', sa.Float(), nullable=True),
        sa.Column('last_reviews_count', sa.Integer(), nullable=True),
        sa.Column('last_trade_in_available', sa.Boolean(), nullable=True),
        sa.Column('last_credit_available', sa.Boolean(), nullable=True),
        sa.Column('last_delivery_available', sa.Boolean(), nullable=True),
        sa.Column('last_pickup_available', sa.Boolean(), nullable=True),
        sa.Column('last_color', sa.String(length=100), nullable=True),
        sa.Column('last_memory_variant', sa.String(length=100), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id')
    )
    op.create_index(op.f('ix_comfy_tracker_data_id'), 'comfy_tracker_data', ['id'], unique=False)

    # Create FOXTROT tracker data table
    op.create_table('foxtrot_tracker_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_cashback_amount', sa.Float(), nullable=True),
        sa.Column('last_personal_price_available', sa.Boolean(), nullable=True),
        sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True),
        sa.Column('last_status', sa.String(length=100), nullable=True),
        sa.Column('last_availability', sa.Boolean(), nullable=True),
        sa.Column('last_rating', sa.Float(), nullable=True),
        sa.Column('last_reviews_count', sa.Integer(), nullable=True),
        sa.Column('last_trade_in_available', sa.Boolean(), nullable=True),
        sa.Column('last_credit_available', sa.Boolean(), nullable=True),
        sa.Column('last_delivery_available', sa.Boolean(), nullable=True),
        sa.Column('last_pickup_available', sa.Boolean(), nullable=True),
        sa.Column('last_color', sa.String(length=100), nullable=True),
        sa.Column('last_memory_variant', sa.String(length=100), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tracker_id')
    )
    op.create_index(op.f('ix_foxtrot_tracker_data_id'), 'foxtrot_tracker_data', ['id'], unique=False)

    # Create COMFY offers data table
    op.create_table('comfy_offers_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_cashback_amount', sa.Float(), nullable=True),
        sa.Column('last_personal_price_available', sa.Boolean(), nullable=True),
        sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True),
        sa.Column('last_color', sa.String(length=100), nullable=True),
        sa.Column('last_memory_variant', sa.String(length=100), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comfy_offers_data_id'), 'comfy_offers_data', ['id'], unique=False)

    # Create FOXTROT offers data table
    op.create_table('foxtrot_offers_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('last_old_price', sa.Float(), nullable=True),
        sa.Column('last_discount_percent', sa.Float(), nullable=True),
        sa.Column('last_cashback_amount', sa.Float(), nullable=True),
        sa.Column('last_personal_price_available', sa.Boolean(), nullable=True),
        sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True),
        sa.Column('last_color', sa.String(length=100), nullable=True),
        sa.Column('last_memory_variant', sa.String(length=100), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tracker_id'], ['product_trackers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_foxtrot_offers_data_id'), 'foxtrot_offers_data', ['id'], unique=False)


def downgrade() -> None:
    # Drop all platform-specific tables
    op.drop_index(op.f('ix_foxtrot_offers_data_id'), table_name='foxtrot_offers_data')
    op.drop_table('foxtrot_offers_data')
    
    op.drop_index(op.f('ix_comfy_offers_data_id'), table_name='comfy_offers_data')
    op.drop_table('comfy_offers_data')
    
    op.drop_index(op.f('ix_foxtrot_tracker_data_id'), table_name='foxtrot_tracker_data')
    op.drop_table('foxtrot_tracker_data')
    
    op.drop_index(op.f('ix_comfy_tracker_data_id'), table_name='comfy_tracker_data')
    op.drop_table('comfy_tracker_data')
    
    op.drop_index(op.f('ix_allo_tracker_data_id'), table_name='allo_tracker_data')
    op.drop_table('allo_tracker_data')
    
    op.drop_index(op.f('ix_prom_tracker_data_id'), table_name='prom_tracker_data')
    op.drop_table('prom_tracker_data')
    
    op.drop_index(op.f('ix_olx_tracker_data_id'), table_name='olx_tracker_data')
    op.drop_table('olx_tracker_data')
    
    op.drop_index(op.f('ix_rozetka_tracker_data_id'), table_name='rozetka_tracker_data')
    op.drop_table('rozetka_tracker_data')

    # Restore columns in product_trackers
    op.add_column('product_trackers', sa.Column('title', sa.String(length=500), nullable=True))
    op.add_column('product_trackers', sa.Column('last_price', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_old_price', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_discount_percent', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_rating', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_views', sa.Integer(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_reviews_count', sa.Integer(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_cashback_amount', sa.Float(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_trade_in_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_credit_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_color', sa.String(length=100), nullable=True))
    op.add_column('product_trackers', sa.Column('last_memory_variant', sa.String(length=100), nullable=True))
    op.add_column('product_trackers', sa.Column('last_delivery_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_pickup_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_personal_price_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_gift_offer_available', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_availability', sa.Boolean(), nullable=True))
    op.add_column('product_trackers', sa.Column('last_status', sa.String(length=100), nullable=True))
    op.add_column('product_trackers', sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True))
