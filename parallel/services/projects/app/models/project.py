from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    owner_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    current_focus: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    latest_activity: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
