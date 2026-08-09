from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WorkspaceEntity


class WorkspaceRepository:
    """Persistence operations for workspaces."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, workspace: WorkspaceEntity) -> WorkspaceEntity:
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def save(self, workspace: WorkspaceEntity) -> WorkspaceEntity:
        """Stage a workspace without committing the surrounding transaction."""
        self.db.add(workspace)
        self.db.flush()
        self.db.refresh(workspace)
        return workspace

    def get_by_id(self, workspace_id: str) -> WorkspaceEntity | None:
        return self.db.get(WorkspaceEntity, workspace_id)

    def get_by_owner_id(self, owner_id: str) -> WorkspaceEntity | None:
        statement = select(WorkspaceEntity).where(
            WorkspaceEntity.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def delete(self, workspace: WorkspaceEntity) -> None:
        self.db.delete(workspace)
        self.db.commit()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
