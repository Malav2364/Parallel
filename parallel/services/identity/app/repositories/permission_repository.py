from sqlalchemy.orm import Session

from app.models.permission import Permission


class PermissionRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        permission: Permission,
    ) -> Permission:
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def get_by_id(
        self,
        permission_id: str,
    ) -> Permission | None:
        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_name(
        self,
        name: str,
    ) -> Permission | None:
        return self.db.query(Permission).filter(Permission.name == name).first()

    def get_all(
        self,
    ) -> list[Permission]:
        return self.db.query(Permission).order_by(Permission.name).all()

    def update(
        self,
        permission: Permission,
    ) -> Permission:
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def delete(
        self,
        permission: Permission,
    ) -> None:
        self.db.delete(permission)
        self.db.commit()

    def exists(
        self,
        permission_id: str,
    ) -> bool:
        return (
            self.db.query(Permission).filter(Permission.id == permission_id).first()
            is not None
        )
