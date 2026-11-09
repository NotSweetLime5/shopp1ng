"""添加发货权限和物流单号。

Revision ID: j0e1ship01
Revises: i9d0idem01
"""
from alembic import op
import sqlalchemy as sa

revision = "j0e1ship01"
down_revision = "i9d0idem01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("can_ship_orders", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("orders", sa.Column("carrier", sa.String(60), nullable=True))
    op.add_column("orders", sa.Column("tracking_no", sa.String(64), nullable=True))


def downgrade():
    op.drop_column("orders", "tracking_no")
    op.drop_column("orders", "carrier")
    op.drop_column("users", "can_ship_orders")
