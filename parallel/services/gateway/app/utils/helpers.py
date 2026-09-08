from app.utils.constants import HOP_BY_HOP_HEADERS


def filter_headers(headers: dict) -> dict:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
        and not key.lower().startswith("x-user-")
    }
