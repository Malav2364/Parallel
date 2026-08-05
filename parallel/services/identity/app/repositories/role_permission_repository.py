from sqlalchemy.orm import Session

from app.models.role_permission import RolePermission


class RolePermissionRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        role_permission: RolePermission,
    ) -> RolePermission:

        self.db.add(role_permission)
        self.db.commit()
        self.db.refresh(role_permission)

        return role_permission

    def get(
        self,
        role_id: str,
        permission_id: str,
    ) -> RolePermission | None:

        return (
            self.db.query(RolePermission)
            .filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
            .first()
        )

    def delete(
        self,
        role_permission: RolePermission,
    ) -> None:

        self.db.delete(role_permission)
        self.db.commit()

    def get_permissions_for_role(
        self,
        role_id: str,
    ) -> list[RolePermission]:

        return (
            self.db.query(RolePermission)
            .filter(
                RolePermission.role_id == role_id,
            )
            .all()
        )

    
