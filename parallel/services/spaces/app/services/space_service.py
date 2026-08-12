import re
from uuid import uuid4

from pios_kernel.Constants import DEFAULT_SPACE_COLOR, DEFAULT_SPACE_ICON

from app.models import SpaceEntity, WorkspaceEntity
from app.repositories import SpaceRepository, WorkspaceRepository
from app.schemas.space import SpaceCreateRequest


class SpaceService:
    """Owner-scoped space queries and creation behavior."""

    def __init__(
        self,
        repository: SpaceRepository,
        workspace_repository: WorkspaceRepository,
    ):
        self.repository = repository
        self.workspace_repository = workspace_repository

    def get_workspace(self, owner_id: str) -> WorkspaceEntity | None:
        return self.workspace_repository.get_by_owner_id(owner_id)

    def list_spaces(self, owner_id: str) -> list[SpaceEntity]:
        workspace = self.get_workspace(owner_id)
        if workspace is None:
            return []
        return self.repository.list_by_workspace(workspace.id)

    def get_space(
        self,
        owner_id: str,
        space_id: str,
    ) -> SpaceEntity | None:
        workspace = self.get_workspace(owner_id)
        if workspace is None:
            return None

        space = self.repository.get_by_id(space_id)
        if space is None or space.workspace_id != workspace.id:
            return None
        return space

    def create_space(
        self,
        owner_id: str,
        request: SpaceCreateRequest,
    ) -> SpaceEntity | None:
        """Create a custom space inside the owner's initialized workspace."""
        workspace = self.get_workspace(owner_id)
        if workspace is None:
            return None

        slug = self._slugify(request.slug or request.name)
        existing = self.repository.get_by_slug(workspace.id, slug)
        if existing is not None:
            return existing

        space = SpaceEntity(
            id=str(uuid4()),
            workspace_id=workspace.id,
            name=request.name,
            slug=slug,
            description=request.description,
            type=request.type.value,
            visibility=request.visibility.value,
            source=request.source.value,
            icon=request.icon or DEFAULT_SPACE_ICON,
            color=request.color or DEFAULT_SPACE_COLOR,
        )

        try:
            self.repository.save(space)
            self.workspace_repository.commit()
            return space
        except Exception:
            self.workspace_repository.rollback()
            raise

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or f"space-{uuid4().hex[:8]}"
