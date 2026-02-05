"""Create disputes table

Revision ID: f3a1b2c4d5e6
Revises: 
Create Date: 2026-02-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a1b2c4d5e6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('disputes'):
        has_orders = inspector.has_table('orders')
        has_users = inspector.has_table('users')

        order_col = sa.Column('order_id', sa.Integer(), nullable=False)
        if has_orders:
            order_col = sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False)

        claimant_col = sa.Column('claimant_id', sa.Integer(), nullable=False)
        if has_users:
            claimant_col = sa.Column('claimant_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False)

        op.create_table(
            'disputes',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('reason', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            order_col,
            claimant_col,
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('disputes'):
        op.drop_table('disputes')
