import httpx


class ProxyService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def forward_request(
        self,
        method: str,
        url: str,
        headers=None,
        params=None,
        content=None,
    ):
        try:
            return await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                content=content,
            )

        except httpx.ConnectError:
            raise RuntimeError("Unable to connect to downstream service.")

        except httpx.TimeoutException:
            raise RuntimeError("Downstream service timed out.")