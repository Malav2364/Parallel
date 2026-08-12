from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project: Project,
    ) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(
        self,
        project_id: str,
    ) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_by_owner(
        self,
        owner_id: str,
    ) -> list[Project]:
        return self.db.query(Project).filter(Project.owner_id == owner_id).all()

    def get_by_owner_and_name(
        self,
        owner_id: str,
        name: str,
    ) -> Project | None:
        return (
            self.db.query(Project)
            .filter(
                Project.owner_id == owner_id,
                func.lower(Project.name) == name.strip().lower(),
            )
            .first()
        )

    def get_all(
        self,
    ) -> list[Project]:
        return self.db.query(Project).all()

    def update(
        self,
        project: Project,
    ) -> Project:
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(
        self,
        project: Project,
    ) -> None:
        self.db.delete(project)
        self.db.commit()
