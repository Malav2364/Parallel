from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SpaceProject(Base):
    __tablename__ = "space_projects"

    __table_args__ = (
        UniqueConstraint(
            "space_id",
            "project_id",
            name="uq_space_project",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    space_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    project_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
