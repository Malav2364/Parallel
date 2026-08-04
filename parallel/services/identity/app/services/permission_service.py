from app.core.logger import logger
from app.exceptions.permission import (
    PermissionAlreadyExistsException,
    PermissionNotFoundException,
)
from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository


class PermissionService:
    def __init__(
        self,
        repository: PermissionRepository,
    ):
        self.repository = repository

    def create_permission(
        self,
        name: str,
        description: str | None = None,
    ) -> Permission:

        existing = self.repository.get_by_name(
            name,
        )

        if existing:
            raise PermissionAlreadyExistsException()

        permission = Permission(
            name=name,
            description=description,
        )

        created = self.repository.create(
            permission,
        )

        logger.info(
            "Permission created: %s",
            created.name,
        )

        return created

    def get_permission(
        self,
        permission_id: str,
    ) -> Permission:

        permission = self.repository.get_by_id(
            permission_id,
        )

        if permission is None:
            raise PermissionNotFoundException()

        return permission

    def get_permissions(
        self,
    ) -> list[Permission]:

        return self.repository.get_all()

    def update_permission(
        self,
        permission_id: str,
        name: str,
        description: str | None = None,
    ) -> Permission:

        permission = self.repository.get_by_id(
            permission_id,
        )

        if permission is None:
            raise PermissionNotFoundException()

        existing = self.repository.get_by_name(
            name,
        )

        if existing and existing.id != permission.id:
            raise PermissionAlreadyExistsException()

        permission.name = name
        permission.description = description

        updated = self.repository.update(
            permission,
        )

        logger.info(
            "Permission updated: %s",
            updated.name,
        )

        return updated

    def delete_permission(
        self,
        permission_id: str,
    ) -> None:

        permission = self.repository.get_by_id(
            permission_id,
        )

        if permission is None:
            raise PermissionNotFoundException()

        self.repository.delete(
            permission,
        )

        logger.info(
            "Permission deleted: %s",
            permission.name,
        )
