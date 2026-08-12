from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ContextChangeEntity, UserContextEntity


class ContextRepository:
    """Persistence operations for current user context."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> UserContextEntity | None:
        statement = select(UserContextEntity).where(
            UserContextEntity.user_id == user_id,
        )
        return self.db.scalar(statement)

    def create(self, context: UserContextEntity) -> UserContextEntity:
        self.db.add(context)
        self.db.commit()
        self.db.refresh(context)
        return context

    def update(self, context: UserContextEntity) -> UserContextEntity:
        self.db.commit()
        self.db.refresh(context)
        return context

    def create_change(self, change: ContextChangeEntity) -> ContextChangeEntity:
        self.db.add(change)
        self.db.commit()
        self.db.refresh(change)
        return change

    def list_changes(self, user_id: str) -> list[ContextChangeEntity]:
        statement = (
            select(ContextChangeEntity)
            .where(ContextChangeEntity.user_id == user_id)
            .order_by(ContextChangeEntity.created_at.desc())
        )
        return list(self.db.scalars(statement).all())
