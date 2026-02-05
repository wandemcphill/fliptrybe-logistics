"""Genesis base tables

Revision ID: 8b1d0c2a3e4f
Revises: 
Create Date: 2026-02-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b1d0c2a3e4f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def has_table(name):
        return name in existing_tables

    def mark_created(name):
        existing_tables.add(name)

    if not has_table('users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('email', sa.String(length=150), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=False),
            sa.Column('password_hash', sa.String(length=200), nullable=False),
            sa.Column('is_admin', sa.Boolean(), nullable=True),
            sa.Column('is_driver', sa.Boolean(), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('wallet_balance', sa.Float(), nullable=True),
            sa.Column('kyc_selfie_file', sa.String(length=100), nullable=True),
            sa.Column('kyc_id_card_file', sa.String(length=100), nullable=True),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('phone'),
        )
        mark_created('users')

    if not has_table('listings'):
        user_id_col = sa.Column('user_id', sa.Integer(), nullable=False)
        if has_table('users'):
            user_id_col = sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)

        op.create_table(
            'listings',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('title', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('price', sa.Float(), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('state', sa.String(length=50), nullable=False),
            sa.Column('image_filename', sa.String(length=100), nullable=False),
            sa.Column('date_posted', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('section', sa.String(length=50), nullable=False),
            user_id_col,
        )
        mark_created('listings')

    if not has_table('orders'):
        buyer_id_col = sa.Column('buyer_id', sa.Integer(), nullable=False)
        driver_id_col = sa.Column('driver_id', sa.Integer(), nullable=True)
        listing_id_col = sa.Column('listing_id', sa.Integer(), nullable=False)
        if has_table('users'):
            buyer_id_col = sa.Column('buyer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)
            driver_id_col = sa.Column('driver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)
        if has_table('listings'):
            listing_id_col = sa.Column('listing_id', sa.Integer(), sa.ForeignKey('listings.id'), nullable=False)

        op.create_table(
            'orders',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('handshake_id', sa.String(length=12), nullable=False),
            sa.Column('total_price', sa.Float(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('delivery_status', sa.String(length=20), nullable=True),
            buyer_id_col,
            listing_id_col,
            driver_id_col,
            sa.UniqueConstraint('handshake_id'),
        )
        mark_created('orders')

    if not has_table('transactions'):
        user_id_col = sa.Column('user_id', sa.Integer(), nullable=False)
        if has_table('users'):
            user_id_col = sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)

        op.create_table(
            'transactions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('type', sa.String(length=20), nullable=False),
            sa.Column('reference', sa.String(length=50), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            user_id_col,
            sa.UniqueConstraint('reference'),
        )
        mark_created('transactions')

    if not has_table('withdrawals'):
        user_id_col = sa.Column('user_id', sa.Integer(), nullable=False)
        if has_table('users'):
            user_id_col = sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)

        op.create_table(
            'withdrawals',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('bank_name', sa.String(length=50), nullable=False),
            sa.Column('account_number', sa.String(length=20), nullable=False),
            sa.Column('account_name', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('request_date', sa.DateTime(), nullable=True),
            user_id_col,
        )
        mark_created('withdrawals')

    if not has_table('price_histories'):
        listing_id_col = sa.Column('listing_id', sa.Integer(), nullable=False)
        if has_table('listings'):
            listing_id_col = sa.Column('listing_id', sa.Integer(), sa.ForeignKey('listings.id'), nullable=False)

        op.create_table(
            'price_histories',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('price', sa.Float(), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            listing_id_col,
        )
        mark_created('price_histories')

    if not has_table('notifications'):
        user_id_col = sa.Column('user_id', sa.Integer(), nullable=False)
        if has_table('users'):
            user_id_col = sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)

        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('title', sa.String(length=50), nullable=False),
            sa.Column('message', sa.String(length=255), nullable=False),
            sa.Column('category', sa.String(length=20), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            user_id_col,
        )
        mark_created('notifications')

    if not has_table('favorites'):
        user_id_col = sa.Column('user_id', sa.Integer(), nullable=False)
        listing_id_col = sa.Column('listing_id', sa.Integer(), nullable=False)
        if has_table('users'):
            user_id_col = sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)
        if has_table('listings'):
            listing_id_col = sa.Column('listing_id', sa.Integer(), sa.ForeignKey('listings.id'), nullable=False)

        op.create_table(
            'favorites',
            sa.Column('id', sa.Integer(), primary_key=True),
            user_id_col,
            listing_id_col,
        )
        mark_created('favorites')


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('favorites'):
        op.drop_table('favorites')
    if inspector.has_table('notifications'):
        op.drop_table('notifications')
    if inspector.has_table('price_histories'):
        op.drop_table('price_histories')
    if inspector.has_table('withdrawals'):
        op.drop_table('withdrawals')
    if inspector.has_table('transactions'):
        op.drop_table('transactions')
    if inspector.has_table('orders'):
        op.drop_table('orders')
    if inspector.has_table('listings'):
        op.drop_table('listings')
    if inspector.has_table('users'):
        op.drop_table('users')
