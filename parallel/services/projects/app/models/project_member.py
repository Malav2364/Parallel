from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="Member",
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
