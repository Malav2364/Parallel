from uuid import uuid4

from pios_kernel.Constants import SYSTEM_SPACES

from app.models import SpaceEntity, WorkspaceEntity
from app.repositories import SpaceRepository, WorkspaceRepository


class WorkspaceService:
    """Workspace initialization behavior."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        space_repository: SpaceRepository,
    ):
        self.workspace_repository = workspace_repository
        self.space_repository = space_repository

    def get_workspace(self, owner_id: str) -> WorkspaceEntity | None:
        return self.workspace_repository.get_by_owner_id(owner_id)

    def initialize_workspace(self, owner_id: str) -> WorkspaceEntity:
        existing = self.get_workspace(owner_id)
        if existing is not None:
            return existing

        try:
            workspace = self.workspace_repository.save(
                WorkspaceEntity(
                    id=str(uuid4()),
                    owner_id=owner_id,
                    name="My Workspace",
                )
            )

            for template in SYSTEM_SPACES:
                self.space_repository.save(
                    SpaceEntity(
                        id=str(uuid4()),
                        workspace_id=workspace.id,
                        name=template["name"],
                        slug=template["name"].lower().replace(" ", "-"),
                        type=template["type"].value,
                        visibility="private",
                        source=template["source"].value,
                        icon=template["icon"],
                        color=template["color"],
                    )
                )

            self.workspace_repository.commit()
            return workspace
        except Exception:
            self.workspace_repository.rollback()
            raise
