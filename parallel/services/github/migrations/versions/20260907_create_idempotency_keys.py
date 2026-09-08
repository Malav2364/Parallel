"""create idempotency_keys table

Revision ID: 20260907idempotency
Revises: 20260830notified
Create Date: 2026-09-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907idempotency"
down_revision: str | Sequence[str] | None = "20260830notified"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_idempotency_user_key",
        ),
    )
    op.create_index(
        op.f("ix_idempotency_keys_user_id"),
        "idempotency_keys",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_idempotency_keys_user_id"),
        table_name="idempotency_keys",
    )
    op.drop_table("idempotency_keys")
