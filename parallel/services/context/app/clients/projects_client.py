import httpx

from app.core.config import settings


class ProjectsClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.base_url = settings.PROJECTS_SERVICE_URL.rstrip("/")
        self._client = client

    async def create_project(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        headers = {"X-User-Id": user_id}

        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        response = await self._client.post(
            f"{self.base_url}/projects",
            headers=headers,
            json={"name": name, "description": description},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    async def list_projects(
        self,
        user_id: str,
    ) -> list[dict]:
        response = await self._client.get(
            f"{self.base_url}/projects",
            headers={"X-User-Id": user_id},
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

        projects = await self.list_projects(user_id)

        return next(
            (
                project
                for project in projects
                if project.get("name", "").strip().lower() == normalized_name
            ),
            None,
        )

    async def update_activity(
        self,
        project_id: str,
        current_focus: str | None,
        latest_activity: str | None,
    ) -> dict:
        activity_update = {
            key: value
            for key, value in {
                "current_focus": current_focus,
                "latest_activity": latest_activity,
            }.items()
            if value is not None
        }

        response = await self._client.patch(
            f"{self.base_url}/projects/{project_id}/activity",
            json=activity_update,
            timeout=10.0,
        )

        response.raise_for_status()

        return response.json()
