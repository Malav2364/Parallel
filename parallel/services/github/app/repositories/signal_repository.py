from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GithubSignal


class SignalRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(
        self,
        user_id: str,
        kind: str,
        external_id: str,
        payload: dict,
    ) -> tuple[GithubSignal, bool]:
        statement = select(GithubSignal).where(
            GithubSignal.user_id == user_id,
            GithubSignal.external_id == external_id,
        )
        existing = self.db.scalar(statement)

        if existing is not None:
            existing.kind = kind
            existing.payload = payload
            self.db.commit()
            self.db.refresh(existing)
            return existing, False

        signal = GithubSignal(
            user_id=user_id,
            kind=kind,
            external_id=external_id,
            payload=payload,
        )
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal, True

    def list_by_user(
        self,
        user_id: str,
        unread_only: bool = False,
    ) -> list[GithubSignal]:
        statement = select(GithubSignal).where(GithubSignal.user_id == user_id)

        if unread_only:
            statement = statement.where(GithubSignal.read_at.is_(None))

        statement = statement.order_by(GithubSignal.synced_at.desc())
        return list(self.db.scalars(statement).all())

    def list_unnotified(
        self,
        user_id: str,
        kind: str,
    ) -> list[GithubSignal]:
        statement = (
            select(GithubSignal)
            .where(
                GithubSignal.user_id == user_id,
                GithubSignal.kind == kind,
                GithubSignal.notified_at.is_(None),
            )
            .order_by(GithubSignal.synced_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def mark_notified(
        self,
        signal_ids: list[str],
        now: datetime,
    ) -> None:
        if not signal_ids:
            return

        statement = select(GithubSignal).where(GithubSignal.id.in_(signal_ids))
        for signal in self.db.scalars(statement).all():
            signal.notified_at = now
        self.db.commit()
