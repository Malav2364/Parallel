from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import (
    get_auth_service,
    get_proxy_service,
)
from app.core.logging import logger
from app.core.routes import ROUTES
from app.services.auth_service import AuthService
from app.services.proxy_service import ProxyService
from app.utils.auth import is_public_route
from app.utils.helpers import filter_headers

router = APIRouter()


@router.api_route(
    "/api/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_request(
    service: str,
    path: str,
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    if service not in ROUTES:
        raise HTTPException(
            status_code=404,
            detail="Unknown service",
        )

    target_url = f"{ROUTES[service]}/{path}"

    # ---------------------------
    # Validate Access Token
    # ---------------------------

    # auth_header = request.headers.get("Authorization")

    user = None

    if not is_public_route(
        service,
        path,
        request.method,
    ):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Missing Authorization header",
            )

        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid Authorization header",
            )

        token = auth_header.split(" ", 1)[1]

        validation_response = await auth_service.validate_token(
            token,
        )

        if validation_response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

        user = validation_response.json()

    # ---------------------------
    # Prepare Headers
    # ---------------------------

    headers = filter_headers(
    dict(request.headers),
    )

    if user:

        headers["X-User-Id"] = user["user_id"]
        headers["X-User-Email"] = user["email"]
        headers["X-User-Role"] = user["role"] or ""
        headers["X-User-Permissions"] = ",".join(
            user["permissions"],
        )

    user_email = "anonymous"
    if user:
        user_email = user["email"]

    logger.info(
        "[%s] %s %s -> %s",
        request.state.request_id,
        user_email,
        request.method,
        target_url,
    )

    try:
        response = await proxy_service.forward_request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=dict(request.query_params),
            content=await request.body(),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )