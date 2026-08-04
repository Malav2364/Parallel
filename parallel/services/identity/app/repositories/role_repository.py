from sqlalchemy.orm import Session, joinedload

from app.models.role import Role
from app.models.role_permission import RolePermission


class RoleRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        role: Role,
    ) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def get_by_id(
        self,
        role_id: str,
    ) -> Role | None:
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        return self.db.query(Role).filter(Role.name == name).first()

    def get_all(
        self,
    ) -> list[Role]:
        return self.db.query(Role).order_by(Role.name).all()

    def update(
        self,
        role: Role,
    ) -> Role:
        self.db.commit()
        self.db.refresh(role)

        return role

    def delete(
        self,
        role: Role,
    ) -> None:
        self.db.delete(role)
        self.db.commit()

    def get_with_permissions(
        self,
        role_id: str,
    ) -> Role | None:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions).joinedload(RolePermission.permission))
            .filter(Role.id == role_id)
            .first()
        )
