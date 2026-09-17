import hashlib

import httpx

from app.clients.github_client import GitHubClient
from app.repositories.idempotency_repository import IdempotencyRepository
from app.services.errors import GithubWriteError, NotConnectedError
from app.services.token_service import TokenService


class PullRequestService:
    """Approve, merge, or close a PR, guarded by the durable idempotency ledger.

    A sibling of ``CommentService``: same token guard (no stored token ⇒
    ``NotConnectedError``) and same write-failure contract (a GitHub write error
    ⇒ ``GithubWriteError``, never a fabricated success). A replayed key returns
    the stored response instead of re-calling GitHub, so a retried write never
    approves/merges/closes twice.
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

    def approve(
        self,
        user_id: str,
        repo: str,
        number: int,
        body: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        key = idempotency_key or self._derive_key(
            "approve_github_pr", user_id, repo, number, body or ""
        )

        existing = self.idempotency.get(user_id, key)
        if existing is not None:
            return existing.response

        token = self.token_service.get_token(user_id)
        if token is None:
            raise NotConnectedError()

        try:
            response = self.github.create_pull_review(
                token, repo, number, event="APPROVE", body=body
            )
        except httpx.HTTPStatusError as exc:
            raise GithubWriteError() from exc

        self.idempotency.create(user_id, key, response)
        return response

    def merge(
        self,
        user_id: str,
        repo: str,
        number: int,
        merge_method: str = "merge",
        idempotency_key: str | None = None,
    ) -> dict:
        key = idempotency_key or self._derive_key(
            "merge_github_pr", user_id, repo, number, merge_method
        )

        existing = self.idempotency.get(user_id, key)
        if existing is not None:
            return existing.response

        token = self.token_service.get_token(user_id)
        if token is None:
            raise NotConnectedError()

        try:
            response = self.github.merge_pull(token, repo, number, merge_method)
        except httpx.HTTPStatusError as exc:
            raise GithubWriteError() from exc

        self.idempotency.create(user_id, key, response)
        return response

    def close(
        self,
        user_id: str,
        repo: str,
        number: int,
        idempotency_key: str | None = None,
    ) -> dict:
        key = idempotency_key or self._derive_key(
            "close_github_pr", user_id, repo, number, ""
        )

        existing = self.idempotency.get(user_id, key)
        if existing is not None:
            return existing.response

        token = self.token_service.get_token(user_id)
        if token is None:
            raise NotConnectedError()

        try:
            response = self.github.close_pull(token, repo, number)
        except httpx.HTTPStatusError as exc:
            raise GithubWriteError() from exc

        self.idempotency.create(user_id, key, response)
        return response

    @staticmethod
    def _derive_key(
        action: str, user_id: str, repo: str, number: int, extra: str
    ) -> str:
        raw = "\n".join([action, user_id, repo, str(number), extra])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
