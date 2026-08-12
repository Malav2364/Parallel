from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SpaceEntity


class SpaceRepository:
    """Persistence operations for spaces."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, space: SpaceEntity) -> SpaceEntity:
        self.db.add(space)
        self.db.commit()
        self.db.refresh(space)
        return space

    def save(self, space: SpaceEntity) -> SpaceEntity:
        """Stage a space without committing the surrounding transaction."""
        self.db.add(space)
        self.db.flush()
        self.db.refresh(space)
        return space

    def get_by_id(self, space_id: str) -> SpaceEntity | None:
        return self.db.get(SpaceEntity, space_id)

    def list_by_workspace(self, workspace_id: str) -> list[SpaceEntity]:
        statement = (
            select(SpaceEntity)
            .where(SpaceEntity.workspace_id == workspace_id)
            .order_by(SpaceEntity.created_at)
        )
        return list(self.db.scalars(statement).all())

    def get_by_slug(
        self,
        workspace_id: str,
        slug: str,
    ) -> SpaceEntity | None:
        statement = select(SpaceEntity).where(
            SpaceEntity.workspace_id == workspace_id,
            SpaceEntity.slug == slug,
        )
        return self.db.scalar(statement)

    def update(self, space: SpaceEntity) -> SpaceEntity:
        self.db.commit()
        self.db.refresh(space)
        return space

    def delete(self, space: SpaceEntity) -> None:
        self.db.delete(space)
        self.db.commit()
