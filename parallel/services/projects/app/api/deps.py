from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.project_repository import ProjectRepository
from app.services.project_member_service import (
    ProjectMemberService,
)
from app.services.project_service import ProjectService


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_project_repository(
    db: Session = Depends(get_db),
):
    return ProjectRepository(db)


def get_project_member_repository(
    db: Session = Depends(get_db),
):
    return ProjectMemberRepository(db)


def get_project_member_service(
    repository: ProjectMemberRepository = Depends(
        get_project_member_repository,
    ),
):
    return ProjectMemberService(
        repository,
    )


def get_project_service(
    repository: ProjectRepository = Depends(
        get_project_repository,
    ),
    member_repository: ProjectMemberRepository = Depends(
        get_project_member_repository,
    ),
):
    return ProjectService(
        repository,
        member_repository,
    )
