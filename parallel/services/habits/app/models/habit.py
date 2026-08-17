from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Habit(Base):
    __tablename__ = "habits"

    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "normalized_name",
            name="uq_habit_owner_normalized_name",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    owner_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    schedule: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    time_window: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )