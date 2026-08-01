from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
            )
            .first()
        )

    def revoke(
        self,
        refresh_token: RefreshToken,
    ) -> None:
        refresh_token.is_revoked = True
        self.db.commit()

    def delete_expired(self) -> int:
        deleted = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.expires_at < datetime.now(UTC),
            )
            .delete()
        )

        self.db.commit()

        return deleted