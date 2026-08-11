from uuid import uuid4

from app.models import SpaceProject
from app.repositories.space_project_repository import SpaceProjectRepository


class SpaceProjectService:
    def __init__(self, repository: SpaceProjectRepository):
        self.repository = repository

    def associate(
        self,
        space_id: str,
        project_id: str,
    ) -> SpaceProject:
        existing = self.repository.get(space_id, project_id)
        if existing is not None:
            return existing

        association = SpaceProject(
            id=str(uuid4()),
            space_id=space_id,
            project_id=project_id,
        )
        return self.repository.create(association)

    def list_projects(self, space_id: str) -> list[SpaceProject]:
        return self.repository.list_projects(space_id)
