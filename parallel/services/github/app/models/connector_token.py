from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ConnectorToken(Base):
    __tablename__ = "connector_tokens"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            name="uq_connector_token_user_provider",
        ),
    )

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="github",
    )
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_hint: Mapped[str] = mapped_column(String(10), nullable=False)
    github_login: Mapped[str | None] = mapped_column(String(255), nullable=True)
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
