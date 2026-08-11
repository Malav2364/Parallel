import httpx

from app.core.config import settings


class ProjectsClient:
    def __init__(self) -> None:
        self.base_url = settings.PROJECTS_SERVICE_URL.rstrip("/")

    def create_project(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/projects",
            headers={"X-User-Id": user_id},
            json={"name": name, "description": description},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    def list_projects(
        self,
        user_id: str,
    ) -> list[dict]:
        response = httpx.get(
            f"{self.base_url}/projects",
            headers={"X-User-Id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

    def update_activity(
        self,
        project_id: str,
        current_focus: str | None,
        latest_activity: str | None,
    ) -> dict:
        response = httpx.patch(
            f"{self.base_url}/projects/{project_id}/activity",
            json={
                "current_focus": current_focus,
                "latest_activity": latest_activity,
            },
            timeout=10.0,
        )

        response.raise_for_status()

        return response.json()
