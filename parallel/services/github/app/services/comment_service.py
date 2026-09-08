import hashlib

import httpx

from app.clients.github_client import GitHubClient
from app.repositories.idempotency_repository import IdempotencyRepository
from app.services.errors import GithubWriteError, NotConnectedError
from app.services.token_service import TokenService


class CommentService:
    """Post a PR comment, guarded by a durable idempotency ledger.

    A replayed key returns the stored comment instead of re-posting, so a
    retried write never double-posts. Mirrors ``SignalService``'s token guard:
    no stored token ⇒ ``NotConnectedError``; a GitHub write failure ⇒
    ``GithubWriteError`` (never a fabricated success).
    """

    def __init__(
        self,
        idempotency: IdempotencyRepository,
        token_service: TokenService,
        github: GitHubClient,
    ):
        self.idempotency = idempotency
        self.token_service = token_service
        self.github = github

    def post_comment(
        self,
        user_id: str,
        repo: str,
        number: int,
        body: str,
        idempotency_key: str | None = None,
    ) -> dict:
        key = idempotency_key or self._derive_key(user_id, repo, number, body)

        existing = self.idempotency.get(user_id, key)
        if existing is not None:
            return existing.response

        token = self.token_service.get_token(user_id)
        if token is None:
            raise NotConnectedError()

        try:
            response = self.github.create_issue_comment(token, repo, number, body)
        except httpx.HTTPStatusError as exc:
            raise GithubWriteError() from exc

        self.idempotency.create(user_id, key, response)
        return response

    @staticmethod
    def _derive_key(user_id: str, repo: str, number: int, body: str) -> str:
        raw = "\n".join(["post_github_comment", user_id, repo, str(number), body])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
