import httpx

from app.core.config import settings


class WorkspaceClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.base_url = settings.WORKSPACE_SERVICE_URL.rstrip("/")
        self._client = client

    async def create_space(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
        space_type: str = "custom",
        visibility: str = "private",
        source: str = "ai",
    ) -> dict:
        response = await self._client.post(
            f"{self.base_url}/spaces",
            headers={"X-User-Id": user_id},
            json={
                "name": name,
                "description": description,
                "type": space_type,
                "visibility": visibility,
                "source": source,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def get_by_name(
        self,
        user_id: str,
        name: str,
    ) -> dict | None:
        normalized_name = name.strip().lower()

        response = await self._client.get(
            f"{self.base_url}/spaces",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()

        spaces = response.json()

        return next(
            (
                space
                for space in spaces
                if space.get("name", "").strip().lower() == normalized_name
            ),
            None,
        )

    async def associate_project(
        self,
        space_id: str,
        project_id: str,
    ) -> dict:
        response = await self._client.post(
            f"{self.base_url}/spaces/{space_id}/projects",
            json={"project_id": project_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
