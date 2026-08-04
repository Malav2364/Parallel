from uuid import UUID

from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def update(
        self,
        user: User,
    ) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def has_permission(
        self,
        user_id: str,
        permission_name: str,
    ) -> bool:

        return (
            self.db.query(User)
            .join(Role)
            .join(RolePermission)
            .join(Permission)
            .filter(
                User.id == user_id,
                Permission.name == permission_name,
            )
            .first()
            is not None
        )
