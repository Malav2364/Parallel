from app.core.config import settings
from app.core.routes import ROUTES
from app.utils.helpers import filter_headers


def test_context_route_registered():
    assert "context" in ROUTES
    assert ROUTES["context"] == settings.CONTEXT_SERVICE_URL


def test_filter_headers_strips_spoofed_user_headers():
    incoming = {
        "Authorization": "Bearer abc",
        "Content-Type": "application/json",
        "X-User-Id": "spoofed-id",
        "x-user-email": "attacker@example.com",
    }
    filtered = filter_headers(incoming)
    assert "Authorization" in filtered
    assert "Content-Type" in filtered
    assert not any(key.lower().startswith("x-user-") for key in filtered)
