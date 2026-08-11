from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SpaceProject


class SpaceProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(
        self,
        space_id: str,
        project_id: str,
    ) -> SpaceProject | None:
        statement = select(SpaceProject).where(
            SpaceProject.space_id == space_id,
            SpaceProject.project_id == project_id,
        )
        return self.db.scalar(statement)

    def create(
        self,
        association: SpaceProject,
    ) -> SpaceProject:
        self.db.add(association)
        self.db.commit()
        self.db.refresh(association)
        return association

    def list_projects(
        self,
        space_id: str,
    ) -> list[SpaceProject]:
        statement = select(SpaceProject).where(
            SpaceProject.space_id == space_id,
        )
        return list(self.db.scalars(statement).all())
