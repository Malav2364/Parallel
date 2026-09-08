"""add reminder idempotency key

Revision ID: c6d90aaaaacb
Revises: 815a4ddbeda7
Create Date: 2026-08-23 13:33:35.012780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6d90aaaaacb'
down_revision: Union[str, Sequence[str], None] = '815a4ddbeda7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "reminders",
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_reminder_idempotency_key",
        "reminders",
        ["idempotency_key"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_reminder_idempotency_key",
        "reminders",
        type_="unique",
    )
    op.drop_column("reminders", "idempotency_key")
