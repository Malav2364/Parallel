from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: str, key: str) -> IdempotencyKey | None:
        statement = select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.idempotency_key == key,
        )
        return self.db.scalar(statement)

    def create(
        self,
        user_id: str,
        key: str,
        response: dict,
    ) -> IdempotencyKey:
        record = IdempotencyKey(
            user_id=user_id,
            idempotency_key=key,
            response=response,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
