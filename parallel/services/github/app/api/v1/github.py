from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_signal_service, get_token_service
from app.schemas.github import (
    SignalResponse,
    SyncResponse,
    TokenConnectRequest,
    TokenStatusResponse,
)
from app.services import SignalService, TokenService
from app.services.errors import InvalidTokenError, NotConnectedError

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
