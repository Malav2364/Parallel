import httpx

from app.clients.github_client import GitHubClient
from app.repositories import TokenRepository
from app.services.crypto import decrypt, encrypt
from app.services.errors import InvalidTokenError


class TokenService:
    def __init__(self, repository: TokenRepository, github: GitHubClient):
        self.repository = repository
        self.github = github

    def store_token(self, user_id: str, pat: str) -> dict:
        pat = pat.strip()

        try:
            user = self.github.get_authenticated_user(pat)
        except httpx.HTTPStatusError as exc:
            raise InvalidTokenError() from exc

        record = self.repository.upsert(
            user_id=user_id,
            encrypted_token=encrypt(pat),
            token_hint=pat[-4:],
            github_login=user.get("login"),
        )
        return {
            "connected": True,
            "hint": record.token_hint,
            "login": record.github_login,
        }

    def status(self, user_id: str) -> dict:
        record = self.repository.get(user_id)

        if record is None:
            return {"connected": False, "hint": None, "login": None}

        return {
            "connected": True,
            "hint": record.token_hint,
            "login": record.github_login,
        }

    def get_token(self, user_id: str) -> str | None:
        record = self.repository.get(user_id)

        if record is None:
            return None

        return decrypt(record.encrypted_token)

    def revoke(self, user_id: str) -> None:
        self.repository.delete(user_id)
