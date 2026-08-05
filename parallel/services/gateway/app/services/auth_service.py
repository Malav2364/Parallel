import httpx

from app.core.config import settings


class AuthService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def validate_token(self, token: str):
        try:
            response = await self.client.post(
                f"{settings.IDENTITY_SERVICE_URL}/auth/validate-token",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
            return response
        except httpx.ConnectError:
            raise RuntimeError("Identity Service is unavailable")