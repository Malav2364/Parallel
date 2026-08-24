from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class ProjectEmbeddingEntity(Base):
    """A cached embedding vector for one user's project.

    Tier-2's semantic resolver embeds each project's descriptive text once and
    reuses the vector across turns. ``text_hash`` fingerprints the embedded
    text so a rename or focus change transparently invalidates the row and
    forces a re-embed. The vector is stored as a JSON float array -- portable
    and dependency-free (no pgvector).
    """

    __tablename__ = "project_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "project_id",
            name="uq_project_embeddings_user_project",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    project_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    text_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    embedding: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
