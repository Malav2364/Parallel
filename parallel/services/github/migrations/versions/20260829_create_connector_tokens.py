"""create connector_tokens table

Revision ID: 20260829tokens
Revises:
Create Date: 2026-08-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260829tokens"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connector_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("encrypted_token", sa.Text(), nullable=False),
        sa.Column("token_hint", sa.String(length=10), nullable=False),
        sa.Column("github_login", sa.String(length=255), nullable=True),
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
            "user_id",
            "provider",
            name="uq_connector_token_user_provider",
        ),
    )
    op.create_index(
        op.f("ix_connector_tokens_user_id"),
        "connector_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_connector_tokens_user_id"),
        table_name="connector_tokens",
    )
    op.drop_table("connector_tokens")
