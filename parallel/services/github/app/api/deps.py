from fastapi import Depends
from sqlalchemy.orm import Session

from app.clients.github_client import GitHubClient
from app.core.database import get_db
from app.repositories import (
    IdempotencyRepository,
    SignalRepository,
    TokenRepository,
)
from app.services import CommentService, SignalService, TokenService


def get_github_client() -> GitHubClient:
    return GitHubClient()


def get_token_repository(db: Session = Depends(get_db)) -> TokenRepository:
    return TokenRepository(db)


def get_signal_repository(db: Session = Depends(get_db)) -> SignalRepository:
    return SignalRepository(db)


def get_idempotency_repository(
    db: Session = Depends(get_db),
) -> IdempotencyRepository:
    return IdempotencyRepository(db)


def get_token_service(
    repository: TokenRepository = Depends(get_token_repository),
    github: GitHubClient = Depends(get_github_client),
) -> TokenService:
    return TokenService(repository, github)


def get_signal_service(
    repository: SignalRepository = Depends(get_signal_repository),
    token_service: TokenService = Depends(get_token_service),
    github: GitHubClient = Depends(get_github_client),
) -> SignalService:
    return SignalService(repository, token_service, github)


def get_comment_service(
    idempotency: IdempotencyRepository = Depends(get_idempotency_repository),
    token_service: TokenService = Depends(get_token_service),
    github: GitHubClient = Depends(get_github_client),
) -> CommentService:
    return CommentService(idempotency, token_service, github)
