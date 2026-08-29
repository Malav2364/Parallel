"""create github_signals table

Revision ID: 20260829signals
Revises: 20260829tokens
Create Date: 2026-08-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260829signals"
down_revision: str | Sequence[str] | None = "20260829tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_signals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=500), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "external_id",
            name="uq_github_signal_user_external",
        ),
    )
    op.create_index(
        op.f("ix_github_signals_user_id"),
        "github_signals",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_github_signals_user_id"),
        table_name="github_signals",
    )
    op.drop_table("github_signals")
