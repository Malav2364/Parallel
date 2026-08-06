from fastapi import HTTPException

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
)


class ProjectService:

    def __init__(
        self,
        repository: ProjectRepository,
        member_repository: ProjectMemberRepository,
    ):
        self.repository = repository
        self.member_repository = member_repository

    def create_project(
        self,
        request: ProjectCreate,
        owner_id: str,
    ):
        project = Project(
            name=request.name,
            description=request.description,
            owner_id=owner_id,
        )

        project = self.repository.create(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=owner_id,
            role="Owner",
        )

        self.member_repository.create(member)

        return project

    def list_projects(self):
        return self.repository.get_all()

    def get_project(
        self,
        project_id: str,
    ):
        project = self.repository.get_by_id(project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found",
            )

        return project

    def update_project(
        self,
        project_id: str,
        request: ProjectUpdate,
    ):
        project = self.get_project(project_id)

        if request.name is not None:
            project.name = request.name

        if request.description is not None:
            project.description = request.description

        return self.repository.update(project)

    def delete_project(
        self,
        project_id: str,
    ):
        project = self.get_project(project_id)

        self.repository.delete(project)
