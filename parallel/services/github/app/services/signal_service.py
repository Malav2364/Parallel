from app.clients.github_client import GitHubClient
from app.models import GithubSignal
from app.repositories import SignalRepository
from app.services.errors import NotConnectedError
from app.services.token_service import TokenService

_PAYLOAD_FIELDS = ("repo", "number", "title", "url", "author", "updated_at")


class SignalService:
    def __init__(
        self,
        repository: SignalRepository,
        token_service: TokenService,
        github: GitHubClient,
    ):
        self.repository = repository
        self.token_service = token_service
        self.github = github

    def sync(self, user_id: str) -> dict:
        token = self.token_service.get_token(user_id)

        if token is None:
            raise NotConnectedError()

        review_requests = self.github.list_review_requests(token)
        my_prs = self.github.list_my_open_prs(token)

        for item in [*review_requests, *my_prs]:
            self.repository.upsert(
                user_id=user_id,
                kind=item["kind"],
                external_id=item["external_id"],
                payload={field: item.get(field) for field in _PAYLOAD_FIELDS},
            )

        return {
            "review_requests": len(review_requests),
            "my_prs": len(my_prs),
        }

    def list_signals(
        self,
        user_id: str,
        unread_only: bool = False,
    ) -> list[GithubSignal]:
        return self.repository.list_by_user(user_id, unread_only=unread_only)
