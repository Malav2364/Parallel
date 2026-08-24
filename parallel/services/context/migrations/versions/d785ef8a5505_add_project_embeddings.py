"""add project embeddings

Revision ID: d785ef8a5505
Revises: be40c44aea52
Create Date: 2026-08-23 23:58:03.961286

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d785ef8a5505"
down_revision: Union[str, Sequence[str], None] = "be40c44aea52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "project_embeddings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("text_hash", sa.String(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "project_id",
            name="uq_project_embeddings_user_project",
        ),
    )
    op.create_index(
        op.f("ix_project_embeddings_project_id"),
        "project_embeddings",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_embeddings_user_id"),
        "project_embeddings",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_project_embeddings_user_id"),
        table_name="project_embeddings",
    )
    op.drop_index(
        op.f("ix_project_embeddings_project_id"),
        table_name="project_embeddings",
    )
    op.drop_table("project_embeddings")
