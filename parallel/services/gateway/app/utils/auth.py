from app.core.public_routes import PUBLIC_ROUTES


def is_public_route(
    service: str,
    path: str,
    method: str,
) -> bool:
    return (
        service in PUBLIC_ROUTES
        and (method.upper(), path) in PUBLIC_ROUTES[service]
    )