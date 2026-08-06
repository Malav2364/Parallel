from fastapi import Request

from app.services.auth_service import AuthService
from app.services.proxy_service import ProxyService


def get_proxy_service(request: Request):
    return ProxyService(request.app.state.http_client)


def get_auth_service(request: Request):
    return AuthService(request.app.state.http_client)
