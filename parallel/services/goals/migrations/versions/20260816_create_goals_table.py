"""create goals table

Revision ID: 20260816goals
Revises:
Create Date: 2026-08-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260816goals"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("target_date", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id",
            "normalized_name",
            name="uq_goal_owner_normalized_name",
        ),
    )
    op.create_index(op.f("ix_goals_owner_id"), "goals", ["owner_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_goals_owner_id"), table_name="goals")
    op.drop_table("goals")
