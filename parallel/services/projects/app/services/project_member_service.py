from fastapi import HTTPException

from app.models.project_member import ProjectMember
from app.repositories.project_member_repository import (
    ProjectMemberRepository,
)
from app.schemas.project_member import ProjectMemberCreate


class ProjectMemberService:
    def __init__(
        self,
        repository: ProjectMemberRepository,
    ):
        self.repository = repository

    def add_member(
        self,
        project_id: str,
        request: ProjectMemberCreate,
    ):
        existing = self.repository.get_member(
            project_id,
            request.user_id,
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="User already belongs to project",
            )

        member = ProjectMember(
            project_id=project_id,
            user_id=request.user_id,
            role=request.role,
        )

        return self.repository.create(member)

    def list_members(
        self,
        project_id: str,
    ):
        return self.repository.list_members(
            project_id,
        )

    def remove_member(
        self,
        project_id: str,
        user_id: str,
    ):
        member = self.repository.get_member(
            project_id,
            user_id,
        )

        if member is None:
            raise HTTPException(
                status_code=404,
                detail="Member not found",
            )

        self.repository.delete(member)
