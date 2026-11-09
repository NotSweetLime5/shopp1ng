"""将下单幂等键与订单保存在同一个事务中。

Revision ID: i9d0idem01
Revises: h8c9guard01
"""
from alembic import op
import sqlalchemy as sa

revision = "i9d0idem01"
down_revision = "h8c9guard01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("idempotency_key", sa.String(64), nullable=True))
    op.create_index(
        "uq_orders_user_idempotency_key", "orders", ["user_id", "idempotency_key"],
        unique=True, postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade():
    op.drop_index("uq_orders_user_idempotency_key", table_name="orders")
    op.drop_column("orders", "idempotency_key")
