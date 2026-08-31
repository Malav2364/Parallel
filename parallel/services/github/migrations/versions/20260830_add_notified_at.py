"""add notified_at to github_signals

Revision ID: 20260830notified
Revises: 20260829signals
Create Date: 2026-08-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260830notified"
down_revision: str | Sequence[str] | None = "20260829signals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "github_signals",
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_signals", "notified_at")
