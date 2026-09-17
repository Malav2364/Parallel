from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import (
    get_comment_service,
    get_pull_request_service,
    get_signal_service,
    get_token_service,
)
from app.schemas.github import (
    ApprovalCreateRequest,
    CloseCreateRequest,
    CommentCreateRequest,
    CommentResponse,
    MergeCreateRequest,
    MergeResponse,
    PullStateResponse,
    ReviewResponse,
    SignalResponse,
    SyncResponse,
    TokenConnectRequest,
    TokenStatusResponse,
)
from app.services import (
    CommentService,
    PullRequestService,
    SignalService,
    TokenService,
)
from app.services.errors import (
    GithubWriteError,
    InvalidTokenError,
    NotConnectedError,
)

router = APIRouter()


@router.post("/token", response_model=TokenStatusResponse)
def connect_token(
    request: TokenConnectRequest,
    x_user_id: str = Header(...),
    service: TokenService = Depends(get_token_service),
) -> TokenStatusResponse:
    try:
        return service.store_token(x_user_id, request.pat)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub token",
        ) from exc


@router.get("/status", response_model=TokenStatusResponse)
def token_status(
    x_user_id: str = Header(...),
    service: TokenService = Depends(get_token_service),
) -> TokenStatusResponse:
    return service.status(x_user_id)


@router.delete("/token", status_code=204)
def disconnect_token(
    x_user_id: str = Header(...),
    service: TokenService = Depends(get_token_service),
) -> None:
    service.revoke(x_user_id)


@router.post("/sync", response_model=SyncResponse)
def sync_signals(
    x_user_id: str = Header(...),
    service: SignalService = Depends(get_signal_service),
) -> SyncResponse:
    try:
        return service.sync(x_user_id)
    except NotConnectedError as exc:
        raise HTTPException(
            status_code=409,
            detail="GitHub is not connected",
        ) from exc


@router.get("/signals", response_model=list[SignalResponse])
def list_signals(
    unread: bool = False,
    x_user_id: str = Header(...),
    service: SignalService = Depends(get_signal_service),
) -> list[SignalResponse]:
    return service.list_signals(x_user_id, unread_only=unread)


@router.post("/comments", response_model=CommentResponse)
def create_comment(
    request: CommentCreateRequest,
    x_user_id: str = Header(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    try:
        result = service.post_comment(
            user_id=x_user_id,
            repo=request.repo,
            number=request.number,
            body=request.body,
            idempotency_key=idempotency_key,
        )
    except NotConnectedError as exc:
        raise HTTPException(
            status_code=409,
            detail="GitHub is not connected",
        ) from exc
    except GithubWriteError as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to post comment to GitHub",
        ) from exc

    return CommentResponse(
        id=result["id"],
        url=result["html_url"],
        body=result["body"],
    )


@router.post("/reviews", response_model=ReviewResponse)
def create_review(
    request: ApprovalCreateRequest,
    x_user_id: str = Header(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: PullRequestService = Depends(get_pull_request_service),
) -> ReviewResponse:
    try:
        result = service.approve(
            user_id=x_user_id,
            repo=request.repo,
            number=request.number,
            body=request.body,
            idempotency_key=idempotency_key,
        )
    except NotConnectedError as exc:
        raise HTTPException(
            status_code=409,
            detail="GitHub is not connected",
        ) from exc
    except GithubWriteError as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to approve the PR on GitHub",
        ) from exc

    return ReviewResponse(
        id=result["id"],
        state=result["state"],
    )


@router.post("/merges", response_model=MergeResponse)
def create_merge(
    request: MergeCreateRequest,
    x_user_id: str = Header(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: PullRequestService = Depends(get_pull_request_service),
) -> MergeResponse:
    try:
        result = service.merge(
            user_id=x_user_id,
            repo=request.repo,
            number=request.number,
            merge_method=request.merge_method,
            idempotency_key=idempotency_key,
        )
    except NotConnectedError as exc:
        raise HTTPException(
            status_code=409,
            detail="GitHub is not connected",
        ) from exc
    except GithubWriteError as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to merge the PR on GitHub",
        ) from exc

    return MergeResponse(
        merged=result["merged"],
        sha=result.get("sha"),
        message=result["message"],
    )


@router.post("/closures", response_model=PullStateResponse)
def create_closure(
    request: CloseCreateRequest,
    x_user_id: str = Header(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: PullRequestService = Depends(get_pull_request_service),
) -> PullStateResponse:
    try:
        result = service.close(
            user_id=x_user_id,
            repo=request.repo,
            number=request.number,
            idempotency_key=idempotency_key,
        )
    except NotConnectedError as exc:
        raise HTTPException(
            status_code=409,
            detail="GitHub is not connected",
        ) from exc
    except GithubWriteError as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to close the PR on GitHub",
        ) from exc

    return PullStateResponse(
        number=result["number"],
        state=result["state"],
    )
