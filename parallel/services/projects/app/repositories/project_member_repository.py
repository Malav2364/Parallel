from sqlalchemy.orm import Session

from app.models.project_member import ProjectMember


class ProjectMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        member: ProjectMember,
    ) -> ProjectMember:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_member(
        self,
        project_id: str,
        user_id: str,
    ) -> ProjectMember | None:
        return (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .first()
        )

    def list_members(
        self,
        project_id: str,
    ):
        return (
            self.db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

    def delete(
        self,
        member: ProjectMember,
    ):
        self.db.delete(member)
        self.db.commit()
