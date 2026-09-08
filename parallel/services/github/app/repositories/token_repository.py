from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConnectorToken


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        user_id: str,
        provider: str = "github",
    ) -> ConnectorToken | None:
        statement = select(ConnectorToken).where(
            ConnectorToken.user_id == user_id,
            ConnectorToken.provider == provider,
        )
        return self.db.scalar(statement)

    def upsert(
        self,
        user_id: str,
        encrypted_token: str,
        token_hint: str,
        github_login: str | None,
        provider: str = "github",
    ) -> ConnectorToken:
        existing = self.get(user_id, provider)

        if existing is not None:
            existing.encrypted_token = encrypted_token
            existing.token_hint = token_hint
            existing.github_login = github_login
            self.db.commit()
            self.db.refresh(existing)
            return existing

        token = ConnectorToken(
            user_id=user_id,
            provider=provider,
            encrypted_token=encrypted_token,
            token_hint=token_hint,
            github_login=github_login,
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def delete(self, user_id: str, provider: str = "github") -> None:
        existing = self.get(user_id, provider)

        if existing is not None:
            self.db.delete(existing)
            self.db.commit()

    def list_user_ids(self, provider: str = "github") -> list[str]:
        statement = select(ConnectorToken.user_id).where(
            ConnectorToken.provider == provider
        )
        return list(self.db.scalars(statement).all())
